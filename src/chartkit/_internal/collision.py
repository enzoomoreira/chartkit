"""
Generic collision resolution engine.

Works exclusively with bounding boxes (display pixels).
Element-type agnostic - any Artist with get_window_extent() works.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from math import isfinite, sqrt
from typing import Protocol, runtime_checkable
from weakref import WeakKeyDictionary

import matplotlib.dates as mdates
from loguru import logger
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.transforms import Bbox

from ..settings import get_config
from ..settings.schema import ChartingConfig, CollisionConfig

# Collision state per Axes, automatically released by GC.
_labels: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_obstacles: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_passive: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_line_obstacles: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()


class _LineSampleObstacle:
    """Virtual point-sized obstacle sampled from a Line2D path.

    Line2D bounding boxes span the entire data area, making them useless
    as collision targets.  Instead, we create small obstacles at each data
    point so moveable labels can be pushed away from the visible line path.
    """

    __slots__ = ("_ax", "_x", "_y", "_radius_px")

    def __init__(self, ax: Axes, x: object, y: object, radius_px: float = 3.0) -> None:
        self._ax = ax
        self._x = x
        self._y = y
        self._radius_px = radius_px

    def get_window_extent(self, renderer: RendererBase | None = None) -> Bbox:
        num_x, num_y = _pos_to_numeric(self._x, self._y)
        px = self._ax.transData.transform((num_x, num_y))
        r = self._radius_px
        return Bbox.from_extents(px[0] - r, px[1] - r, px[0] + r, px[1] + r)

    def get_visible(self) -> bool:
        return True


@runtime_checkable
class PositionableArtist(Protocol):
    """Artist that supports repositioning via get/set_position."""

    def get_position(self) -> tuple[float, float]: ...
    def set_position(self, xy: tuple[float, float]) -> None: ...
    def get_window_extent(self, renderer: RendererBase | None = None) -> Bbox: ...


def register_moveable(ax: Axes, artist: Artist) -> None:
    """Register Artist that can be repositioned by the engine."""
    _labels.setdefault(ax, []).append(artist)


def register_fixed(ax: Axes, artist: Artist) -> None:
    """Register Artist that should be avoided by moveables."""
    _obstacles.setdefault(ax, []).append(artist)


def register_line_obstacle(ax: Axes, line: Artist) -> None:
    """Register a Line2D whose data path should repel moveable labels.

    The line's full bounding box is not used (it spans the entire plot).
    Instead, ``_collect_obstacles`` samples each data point and creates
    point-sized virtual obstacles along the path.
    """
    _line_obstacles.setdefault(ax, []).append(line)


def register_passive(ax: Axes, artist: Artist) -> None:
    """Register Artist that does not participate in collision resolution.

    Auto-detected patches (ax.patches) are treated as obstacles by default.
    Use this function to exclude background visual elements (bands, shaded
    areas, etc.) from automatic detection.
    """
    _passive.setdefault(ax, []).append(artist)


def resolve_collisions(ax: Axes) -> None:
    """Resolve all registered collisions in a single axes."""
    moveables = _labels.get(ax, [])
    if not moveables:
        return

    config = get_config()
    collision = config.collision

    fig = ax.figure
    fig.draw_without_rendering()
    renderer = fig.canvas.get_renderer()  # type: ignore[attr-defined]

    positionable = [m for m in moveables if isinstance(m, PositionableArtist)]
    if not positionable:
        return

    original_positions = [_pos_to_numeric(*m.get_position()) for m in positionable]

    fixed = _collect_obstacles(ax, moveables)
    logger.debug(
        "Collision: {} moveable(s), {} obstacle(s)", len(positionable), len(fixed)
    )

    axes_bbox = ax.get_window_extent(renderer)

    _resolve_all(positionable, fixed, renderer, axes_bbox, collision)

    _add_connectors(positionable, original_positions, renderer, collision, config)


def resolve_composed_collisions(axes: Sequence[Axes]) -> None:
    """Resolve collisions across multiple axes simultaneously.

    Merges all moveable labels from every axes into a single pool
    and resolves them together in pixel space. Each label is shifted
    using its own axes' transform (``label.axes.transData``).
    """
    all_moveables: list[Artist] = []
    for ax in axes:
        all_moveables.extend(_labels.get(ax, []))
    if not all_moveables:
        return

    config = get_config()
    collision = config.collision

    fig = axes[0].figure
    fig.draw_without_rendering()
    renderer = fig.canvas.get_renderer()  # type: ignore[attr-defined]

    positionable = [m for m in all_moveables if isinstance(m, PositionableArtist)]
    if not positionable:
        return

    original_positions = [_pos_to_numeric(*m.get_position()) for m in positionable]

    # Collect obstacles from all axes (deduplicated via _collect_obstacles internals)
    seen_ids: set[int] = set()
    fixed: list[Artist] = []
    for ax in axes:
        for obs in _collect_obstacles(ax, all_moveables):
            oid = id(obs)
            if oid not in seen_ids:
                fixed.append(obs)
                seen_ids.add(oid)

    logger.debug(
        "Composed collision: {} moveable(s), {} obstacle(s), {} axes",
        len(positionable),
        len(fixed),
        len(axes),
    )

    # twinx axes share the same physical area
    axes_bbox = axes[0].get_window_extent(renderer)

    _resolve_all(positionable, fixed, renderer, axes_bbox, collision)

    _add_connectors(positionable, original_positions, renderer, collision, config)


def _resolve_all(
    moveables: Sequence[PositionableArtist],
    fixed: list[Artist],
    renderer: RendererBase,
    axes_bbox: Bbox,
    collision: CollisionConfig,
) -> None:
    """Resolve all collisions (fixed + inter-label) in a unified pass."""
    obstacle_pad = collision.obstacle_padding_px
    label_pad = collision.label_padding_px

    for _ in range(collision.max_iterations):
        any_moved = False

        for i, label in enumerate(moveables):
            raw_bbox = label.get_window_extent(renderer)
            if raw_bbox.width < 1 and raw_bbox.height < 1:
                continue

            # Build obstacle list with appropriate padding per type
            all_obs: list[Bbox] = []
            for obs in fixed:
                all_obs.append(_pad_bbox(obs.get_window_extent(renderer), obstacle_pad))
            for j, other in enumerate(moveables):
                if j == i:
                    continue
                all_obs.append(_pad_bbox(other.get_window_extent(renderer), label_pad))

            # Find which obstacles collide with padded label bbox
            padded_label = _pad_bbox(raw_bbox, label_pad)
            colliding: list[Bbox] = []
            for ob in all_obs:
                if padded_label.overlaps(ob):
                    colliding.append(ob)

            if not colliding:
                continue

            result = _find_free_position(
                raw_bbox, colliding, all_obs, collision.movement, axes_bbox, label_pad
            )
            if result is not None:
                dx, dy = result
                _shift_label(label, dx, dy)
                any_moved = True

        if not any_moved:
            break


def _find_free_position(
    label_bbox: Bbox,
    colliding_bboxes: list[Bbox],
    all_obs_bboxes: list[Bbox],
    movement: str,
    axes_bbox: Bbox,
    label_pad: float,
) -> tuple[float, float] | None:
    """Find the smallest displacement that frees label_bbox from all obstacles.

    Generates candidate displacements from each colliding obstacle, validates
    them against all obstacles, and returns the best collision-free option.
    Falls back to diagonal displacement if no single-axis solution exists.
    """
    candidates: list[tuple[float, float, float]] = []
    clearance = label_pad + 1.0
    for obs in colliding_bboxes:
        candidates.extend(
            _compute_displacement_options(label_bbox, obs, "xy", clearance, axes_bbox)
        )

    if not candidates:
        return None

    # Sort: Y-only first, X-only second, diagonal last (by distance within each)
    def _sort_key(c: tuple[float, float, float]) -> tuple[int, float]:
        dx, dy, dist = c
        if dx == 0:
            return (0, dist)  # Y-only
        if dy == 0:
            return (1, dist)  # X-only
        return (2, dist)  # diagonal

    candidates.sort(key=_sort_key)

    # Filter by movement preference
    if movement == "y":
        ordered = [c for c in candidates if c[0] == 0]
        ordered.extend(c for c in candidates if c[0] != 0)
    elif movement == "x":
        ordered = [c for c in candidates if c[1] == 0]
        ordered.extend(c for c in candidates if c[1] != 0)
    else:
        ordered = candidates

    # Validate each candidate against ALL obstacles using padded label bbox
    for dx, dy, _ in ordered:
        shifted_padded = _pad_bbox(
            Bbox.from_extents(
                label_bbox.x0 + dx,
                label_bbox.y0 + dy,
                label_bbox.x1 + dx,
                label_bbox.y1 + dy,
            ),
            label_pad,
        )
        if not any(shifted_padded.overlaps(ob) for ob in all_obs_bboxes):
            return (dx, dy)

    # Fallback: diagonal combination of best Y + best X
    y_opts = [(dx, dy, d) for dx, dy, d in candidates if dx == 0]
    x_opts = [(dx, dy, d) for dx, dy, d in candidates if dy == 0]
    if y_opts and x_opts:
        for yc in y_opts:
            for xc in x_opts:
                dx_combo = xc[0]
                dy_combo = yc[1]
                shifted_padded = _pad_bbox(
                    Bbox.from_extents(
                        label_bbox.x0 + dx_combo,
                        label_bbox.y0 + dy_combo,
                        label_bbox.x1 + dx_combo,
                        label_bbox.y1 + dy_combo,
                    ),
                    label_pad,
                )
                if not any(shifted_padded.overlaps(ob) for ob in all_obs_bboxes):
                    return (dx_combo, dy_combo)

    return None


def _pad_bbox(bbox: Bbox, padding_px: float) -> Bbox:
    """Expand a raw Bbox by a fixed padding on all sides."""
    return Bbox.from_extents(
        bbox.x0 - padding_px,
        bbox.y0 - padding_px,
        bbox.x1 + padding_px,
        bbox.y1 + padding_px,
    )


def _compute_displacement_options(
    mov_bbox: Bbox,
    fix_bbox: Bbox,
    movement: str,
    padding_px: float,
    axes_bbox: Bbox,
) -> list[tuple[float, float, float]]:
    """Compute valid displacement options for a given movement axis."""
    options: list[tuple[float, float, float]] = []  # (dx, dy, abs_distance)

    if movement in ("y", "xy"):
        dy_up = fix_bbox.y1 + padding_px - mov_bbox.y0
        dy_down = fix_bbox.y0 - padding_px - mov_bbox.y1

        new_y0_up = mov_bbox.y0 + dy_up
        new_y1_up = mov_bbox.y1 + dy_up
        if new_y0_up >= axes_bbox.y0 and new_y1_up <= axes_bbox.y1:
            options.append((0, dy_up, abs(dy_up)))

        new_y0_down = mov_bbox.y0 + dy_down
        new_y1_down = mov_bbox.y1 + dy_down
        if new_y0_down >= axes_bbox.y0 and new_y1_down <= axes_bbox.y1:
            options.append((0, dy_down, abs(dy_down)))

    if movement in ("x", "xy"):
        dx_right = fix_bbox.x1 + padding_px - mov_bbox.x0
        new_x0_right = mov_bbox.x0 + dx_right
        new_x1_right = mov_bbox.x1 + dx_right
        if new_x0_right >= axes_bbox.x0 and new_x1_right <= axes_bbox.x1:
            options.append((dx_right, 0, abs(dx_right)))

        dx_left = fix_bbox.x0 - padding_px - mov_bbox.x1
        new_x0_left = mov_bbox.x0 + dx_left
        new_x1_left = mov_bbox.x1 + dx_left
        if new_x0_left >= axes_bbox.x0 and new_x1_left <= axes_bbox.x1:
            options.append((dx_left, 0, abs(dx_left)))

    return options


def _add_connectors(
    moveables: Sequence[PositionableArtist],
    original_positions: list[tuple[float, float]],
    renderer: RendererBase,
    collision: CollisionConfig,
    config: ChartingConfig,
) -> None:
    """Add guide lines for moveables displaced beyond the threshold."""
    # Group labels by their parent axes for correct transform and limit preservation
    by_axes: defaultdict[Axes, list[tuple[PositionableArtist, tuple[float, float]]]] = (
        defaultdict(list)
    )
    for label, orig in zip(moveables, original_positions):
        by_axes[label.axes].append((label, orig))  # type: ignore[union-attr]

    for ax, items in by_axes.items():
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        for label, (orig_x, orig_y) in items:
            curr_x, curr_y = _pos_to_numeric(*label.get_position())
            orig_px = ax.transData.transform((orig_x, orig_y))
            curr_px = ax.transData.transform((curr_x, curr_y))
            dist_px = sqrt(
                (orig_px[0] - curr_px[0]) ** 2 + (orig_px[1] - curr_px[1]) ** 2
            )

            if dist_px > collision.connector_threshold_px:
                ax.plot(
                    [orig_x, curr_x],
                    [orig_y, curr_y],
                    color=config.colors.grid,
                    alpha=collision.connector_alpha,
                    lw=collision.connector_width,
                    linestyle=collision.connector_style,
                    zorder=config.layout.zorder.reference_lines,
                )

        ax.set_xlim(xlim)
        ax.set_ylim(ylim)


# -- Internal helpers --


def _collect_obstacles(ax: Axes, moveables: list[Artist]) -> list[Artist]:
    """Collect obstacles: explicit + auto-detected patches + line samples on shared axes.

    In composed charts with twinx, labels from one axis must also avoid
    patches, labels and line paths rendered on the sibling axis.
    """
    moveable_ids = {id(m) for m in moveables}
    sibling_axes = list(ax.get_shared_x_axes().get_siblings(ax))
    passive_ids = {id(p) for sibling in sibling_axes for p in _passive.get(sibling, [])}
    seen: set[int] = set()
    obstacles: list[Artist] = []

    # 1. Explicitly registered obstacles (reference lines, etc.)
    for obs in _obstacles.get(ax, []):
        oid = id(obs)
        if oid not in seen:
            obstacles.append(obs)
            seen.add(oid)

    # 2. Auto-detect patches on all axes sharing X (bars, boxes, etc.)
    #    Full Line2D bboxes are NOT included (they span the entire data area).
    #    Instead, registered lines are sampled at data points (step 3).
    for sibling in sibling_axes:
        for patch in sibling.patches:
            pid = id(patch)
            if (
                pid not in moveable_ids
                and pid not in passive_ids
                and pid not in seen
                and patch.get_visible()
            ):
                obstacles.append(patch)
                seen.add(pid)

        # Labels from sibling axes (twinx) are obstacles for cross-axis avoidance
        if sibling is not ax:
            for label in _labels.get(sibling, []):
                lid = id(label)
                if (
                    lid not in moveable_ids
                    and lid not in passive_ids
                    and lid not in seen
                    and label.get_visible()
                ):
                    obstacles.append(label)
                    seen.add(lid)

    # 3. Line path samples: point-sized obstacles at each data point of
    #    registered lines, so moveable labels avoid the visible line path.
    for sibling in sibling_axes:
        for line in _line_obstacles.get(sibling, []):
            if not line.get_visible():
                continue
            lid = id(line)
            if lid in seen:
                continue
            seen.add(lid)
            xdata = line.get_xdata()
            ydata = line.get_ydata()
            radius = max(float(line.get_linewidth()), 2.0)
            for lx, ly in zip(xdata, ydata):
                try:
                    if not isfinite(float(ly)):
                        continue
                except (TypeError, ValueError):
                    continue
                obstacles.append(_LineSampleObstacle(sibling, lx, ly, radius_px=radius))

    return obstacles


def _pos_to_numeric(x: object, y: object) -> tuple[float, float]:
    """Convert data-space position to numeric (dates -> mdates float)."""
    if not isinstance(x, (int, float)):
        try:
            x = mdates.date2num(x)
        except (TypeError, ValueError, AttributeError):
            x = float(x)  # type: ignore[arg-type]
    return float(x), float(y)  # type: ignore[arg-type]


def _shift_label(label: PositionableArtist, dx_px: float, dy_px: float) -> None:
    """Move label by pixel delta, converting via the label's own axes transform."""
    ax = label.axes  # type: ignore[union-attr]
    num_x, num_y = _pos_to_numeric(*label.get_position())
    curr_px = ax.transData.transform((num_x, num_y))
    new_px = (curr_px[0] + dx_px, curr_px[1] + dy_px)
    new_data = ax.transData.inverted().transform(new_px)
    # Pin coordinate that should not change to avoid roundtrip drift
    final_x = num_x if dx_px == 0 else new_data[0]
    final_y = num_y if dy_px == 0 else new_data[1]
    label.set_position((final_x, final_y))
