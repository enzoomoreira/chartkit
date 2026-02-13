"""
Generic collision resolution engine.

Works with bounding boxes (display pixels) and continuous path
intersection for line obstacles. Element-type agnostic.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from math import sqrt
from typing import Protocol, runtime_checkable
from weakref import WeakKeyDictionary

import matplotlib.dates as mdates
import matplotlib.patches as mpatches  # used by _draw_debug_overlay
from loguru import logger
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure
from matplotlib.path import Path as MplPath
from matplotlib.transforms import Bbox

from ..settings import get_config
from ..settings.schema import ChartingConfig, CollisionConfig

# Collision state per Axes, automatically released by GC.
_labels: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_obstacles: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_passive: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_line_obstacles: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()


class _LinePathObstacle:
    """Continuous path obstacle from a Line2D.

    Uses matplotlib's Cython-based ``Path.intersects_bbox()`` for exact
    collision detection along the entire line curve, replacing the
    previous approach of N point-sized obstacles per data point.
    """

    __slots__ = ("_ax", "_line", "_display_path")

    def __init__(self, ax: Axes, line: Artist) -> None:
        self._ax = ax
        self._line = line
        self._display_path: MplPath | None = None

    def _get_display_path(self, renderer: RendererBase) -> MplPath:
        if self._display_path is None:
            data_path = self._line.get_path()
            transform = self._line.get_transform()
            vertices = transform.transform(data_path.vertices)
            self._display_path = MplPath(vertices, data_path.codes)
        return self._display_path

    def intersects(self, bbox: Bbox, renderer: RendererBase) -> bool:
        path = self._get_display_path(renderer)
        if not path.get_extents().overlaps(bbox):
            return False
        return path.intersects_bbox(bbox, filled=False)

    def local_bbox(
        self, label_bbox: Bbox, margin: float, renderer: RendererBase
    ) -> Bbox:
        """Bbox of path vertices near the label, for displacement generation."""
        path = self._get_display_path(renderer)
        verts = path.vertices
        x_lo = label_bbox.x0 - margin
        x_hi = label_bbox.x1 + margin
        mask = (verts[:, 0] >= x_lo) & (verts[:, 0] <= x_hi)
        local = verts[mask]
        if len(local) == 0:
            return label_bbox
        return Bbox.from_extents(
            local[:, 0].min(),
            local[:, 1].min(),
            local[:, 0].max(),
            local[:, 1].max(),
        )


Obstacle = Artist | _LinePathObstacle


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
    Instead, ``_collect_obstacles`` wraps each line in a ``_LinePathObstacle``
    that uses continuous path intersection for collision detection.
    """
    _line_obstacles.setdefault(ax, []).append(line)


def register_passive(ax: Axes, artist: Artist) -> None:
    """Register Artist that does not participate in collision resolution.

    Auto-detected patches (ax.patches) are treated as obstacles by default.
    Use this function to exclude background visual elements (bands, shaded
    areas, etc.) from automatic detection.
    """
    _passive.setdefault(ax, []).append(artist)


def resolve_collisions(ax: Axes, *, debug: bool = False) -> None:
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

    _add_connectors(positionable, original_positions, renderer, config)

    if debug:
        _draw_debug_overlay(fig, positionable, fixed, renderer, axes_bbox, collision)


def resolve_composed_collisions(axes: Sequence[Axes], *, debug: bool = False) -> None:
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
    fixed: list[Obstacle] = []
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

    _add_connectors(positionable, original_positions, renderer, config)

    if debug:
        _draw_debug_overlay(fig, positionable, fixed, renderer, axes_bbox, collision)


def _resolve_all(
    moveables: Sequence[PositionableArtist],
    fixed: list[Obstacle],
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

            # Separate bbox obstacles from path obstacles.
            # Path obstacles (lines) use continuous intersection checks
            # instead of discrete bounding boxes.
            label_ax = label.axes  # type: ignore[union-attr]
            bbox_obs: list[Bbox] = []
            path_obs: list[_LinePathObstacle] = []

            for obs in fixed:
                if isinstance(obs, _LinePathObstacle):
                    # Same-axis co-location: label starts ON this line
                    if obs._ax is label_ax and obs.intersects(raw_bbox, renderer):
                        continue
                    path_obs.append(obs)
                else:
                    bbox_obs.append(
                        _pad_bbox(obs.get_window_extent(renderer), obstacle_pad)
                    )

            for j, other in enumerate(moveables):
                if j == i:
                    continue
                bbox_obs.append(_pad_bbox(other.get_window_extent(renderer), label_pad))

            # Detect collisions: bbox overlap + path intersection
            padded_label = _pad_bbox(raw_bbox, label_pad)
            colliding: list[Bbox] = [ob for ob in bbox_obs if padded_label.overlaps(ob)]
            for po in path_obs:
                if po.intersects(padded_label, renderer):
                    colliding.append(po.local_bbox(raw_bbox, label_pad * 2, renderer))

            if not colliding:
                continue

            result = _find_free_position(
                raw_bbox,
                colliding,
                bbox_obs,
                path_obs,
                collision.movement,
                axes_bbox,
                label_pad,
                renderer,
            )
            if result is not None:
                dx, dy = result
                _shift_label(label, dx, dy)
                any_moved = True

        if not any_moved:
            break


def _position_is_free(
    bbox: Bbox,
    bbox_obs: list[Bbox],
    paths: list[_LinePathObstacle],
    renderer: RendererBase,
) -> bool:
    """Check if a position is free from all bbox and path obstacles."""
    if any(bbox.overlaps(ob) for ob in bbox_obs):
        return False
    return not any(p.intersects(bbox, renderer) for p in paths)


def _find_free_position(
    label_bbox: Bbox,
    colliding_bboxes: list[Bbox],
    all_obs_bboxes: list[Bbox],
    path_obs: list[_LinePathObstacle],
    movement: str,
    axes_bbox: Bbox,
    label_pad: float,
    renderer: RendererBase,
) -> tuple[float, float] | None:
    """Find the smallest displacement that frees label_bbox from all obstacles.

    Generates candidate displacements from each colliding obstacle, validates
    them against all obstacles (bbox + path), and returns the best option.
    Falls back to diagonal displacement if no single-axis solution exists.
    """
    candidates: list[tuple[float, float, float]] = []
    clearance = label_pad + 1.0
    for obs in colliding_bboxes:
        candidates.extend(
            _compute_displacement_options(label_bbox, obs, clearance, axes_bbox)
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

    # Validate each candidate against ALL obstacles (bbox + path)
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
        if _position_is_free(shifted_padded, all_obs_bboxes, path_obs, renderer):
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
                if _position_is_free(
                    shifted_padded, all_obs_bboxes, path_obs, renderer
                ):
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
    padding_px: float,
    axes_bbox: Bbox,
) -> list[tuple[float, float, float]]:
    """Compute valid displacement options in both axes."""
    options: list[tuple[float, float, float]] = []  # (dx, dy, abs_distance)

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
    config: ChartingConfig,
) -> None:
    """Add guide lines for moveables displaced beyond the threshold."""
    collision = config.collision
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


def _draw_debug_overlay(
    fig: Figure,
    moveables: Sequence[PositionableArtist],
    fixed: list[Obstacle],
    renderer: RendererBase,
    axes_bbox: Bbox,
    collision: CollisionConfig,
) -> None:
    """Draw translucent collision bboxes for visual debugging."""
    obstacle_pad = collision.obstacle_padding_px
    label_pad = collision.label_padding_px
    inv = fig.transFigure.inverted()

    def _add_rect(bbox_raw: Bbox, color: str, alpha: float) -> None:
        # Clip to axes bounds so debug rects don't stretch the figure
        bbox = Bbox.from_extents(
            max(bbox_raw.x0, axes_bbox.x0),
            max(bbox_raw.y0, axes_bbox.y0),
            min(bbox_raw.x1, axes_bbox.x1),
            min(bbox_raw.y1, axes_bbox.y1),
        )
        if bbox.width <= 0 or bbox.height <= 0:
            return
        p0 = inv.transform((bbox.x0, bbox.y0))
        p1 = inv.transform((bbox.x1, bbox.y1))
        fig.patches.append(
            mpatches.FancyBboxPatch(
                (p0[0], p0[1]),
                p1[0] - p0[0],
                p1[1] - p0[1],
                boxstyle="square,pad=0",
                transform=fig.transFigure,
                facecolor=color,
                edgecolor=color,
                alpha=alpha,
                clip_on=False,
                zorder=100,
            )
        )

    # Fixed obstacles (red) and line paths (orange)
    for obs in fixed:
        if isinstance(obs, _LinePathObstacle):
            path = obs._get_display_path(renderer)
            fig_verts = inv.transform(path.vertices)
            fig.patches.append(
                mpatches.PathPatch(
                    MplPath(fig_verts, path.codes),
                    facecolor="none",
                    edgecolor="orange",
                    linewidth=4,
                    alpha=0.5,
                    joinstyle="round",
                    capstyle="round",
                    transform=fig.transFigure,
                    clip_on=True,
                    zorder=100,
                )
            )
        else:
            ext = obs.get_window_extent(renderer)
            _add_rect(_pad_bbox(ext, obstacle_pad), "red", 0.25)

    # Moveable labels (blue)
    for label in moveables:
        ext = label.get_window_extent(renderer)
        _add_rect(_pad_bbox(ext, label_pad), "dodgerblue", 0.3)

    # Axes bounds (green border)
    p0 = inv.transform((axes_bbox.x0, axes_bbox.y0))
    p1 = inv.transform((axes_bbox.x1, axes_bbox.y1))
    fig.patches.append(
        mpatches.FancyBboxPatch(
            (p0[0], p0[1]),
            p1[0] - p0[0],
            p1[1] - p0[1],
            boxstyle="square,pad=0",
            transform=fig.transFigure,
            facecolor="none",
            edgecolor="green",
            linewidth=2,
            alpha=0.8,
            clip_on=False,
            zorder=101,
        )
    )


# -- Internal helpers --


def _collect_obstacles(ax: Axes, moveables: list[Artist]) -> list[Obstacle]:
    """Collect obstacles: explicit + auto-detected patches + line paths on shared axes.

    In composed charts with twinx, labels from one axis must also avoid
    patches, labels and line paths rendered on the sibling axis.
    """
    moveable_ids = {id(m) for m in moveables}
    sibling_axes = list(ax.get_shared_x_axes().get_siblings(ax))
    passive_ids = {id(p) for sibling in sibling_axes for p in _passive.get(sibling, [])}
    seen: set[int] = set()
    obstacles: list[Obstacle] = []

    # 1. Explicitly registered obstacles (reference lines, etc.)
    for obs in _obstacles.get(ax, []):
        oid = id(obs)
        if oid not in seen:
            obstacles.append(obs)
            seen.add(oid)

    # 2. Auto-detect patches on all axes sharing X (bars, boxes, etc.)
    #    Full Line2D bboxes are NOT included (they span the entire data area).
    #    Registered lines are wrapped in _LinePathObstacle (step 3).
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

    # 3. Line path obstacles: one _LinePathObstacle per registered line,
    #    using continuous path intersection instead of per-point sampling.
    for sibling in sibling_axes:
        for line in _line_obstacles.get(sibling, []):
            if not line.get_visible():
                continue
            lid = id(line)
            if lid in seen:
                continue
            seen.add(lid)
            obstacles.append(_LinePathObstacle(sibling, line))

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
