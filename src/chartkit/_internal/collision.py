"""
Generic collision resolution engine.

Works with unified path-based collision detection. Extracts geometry
from any matplotlib Artist via matplotlib.path.Path, using
Path.intersects_bbox() (Cython) for precise detection.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from math import sqrt
from typing import Protocol, runtime_checkable
from weakref import WeakKeyDictionary

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from loguru import logger
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure
from matplotlib.path import Path as MplPath
from matplotlib.transforms import Affine2D, Bbox

from ..settings import get_config
from ..settings.schema import ChartingConfig, CollisionConfig

# Collision state per Axes, automatically released by GC.
_labels: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_passive: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_artist_obstacles: WeakKeyDictionary[Axes, list[tuple[Artist, bool, bool]]] = (
    WeakKeyDictionary()
)


class _PathObstacle:
    """Unified path-based collision obstacle for any matplotlib Artist."""

    __slots__ = (
        "_ax",
        "_artist",
        "_display_paths",
        "_filled",
        "_colocate",
        "_debug_color",
        "_source_id",
    )

    def __init__(
        self,
        ax: Axes,
        artist: Artist,
        display_paths: list[MplPath],
        *,
        filled: bool,
        colocate: bool = False,
        debug_color: str,
    ) -> None:
        self._ax = ax
        self._artist = artist
        self._display_paths = display_paths
        self._filled = filled
        self._colocate = colocate
        self._debug_color = debug_color
        self._source_id = id(artist)

    def intersects(
        self, bbox: Bbox, renderer: RendererBase, padding: float = 0.0
    ) -> bool:
        test_bbox = _pad_bbox(bbox, padding) if padding > 0 else bbox
        for path in self._display_paths:
            if not path.get_extents().overlaps(test_bbox):
                continue
            if path.intersects_bbox(test_bbox, filled=self._filled):
                return True
        return False

    def local_bbox(
        self, label_bbox: Bbox, margin: float, renderer: RendererBase
    ) -> Bbox:
        """Bbox of the obstacle near the label, for displacement generation."""
        if self._filled:
            extents = [p.get_extents() for p in self._display_paths]
            if not extents:
                return label_bbox
            return Bbox.from_extents(
                min(e.x0 for e in extents),
                min(e.y0 for e in extents),
                max(e.x1 for e in extents),
                max(e.y1 for e in extents),
            )
        # Unfilled: only vertices near the label (for lines)
        x_lo = label_bbox.x0 - margin
        x_hi = label_bbox.x1 + margin
        x_mins: list[float] = []
        y_mins: list[float] = []
        x_maxes: list[float] = []
        y_maxes: list[float] = []
        for path in self._display_paths:
            verts = path.vertices
            mask = (verts[:, 0] >= x_lo) & (verts[:, 0] <= x_hi)
            local = verts[mask]
            if len(local) > 0:
                x_mins.append(float(local[:, 0].min()))
                y_mins.append(float(local[:, 1].min()))
                x_maxes.append(float(local[:, 0].max()))
                y_maxes.append(float(local[:, 1].max()))
        if not x_mins:
            return label_bbox
        return Bbox.from_extents(min(x_mins), min(y_mins), max(x_maxes), max(y_maxes))


# -- Factory functions --


def _bbox_to_path(bbox: Bbox) -> MplPath:
    """Convert a Bbox to a closed rectangular Path in the same coordinates."""
    return MplPath(
        [
            [bbox.x0, bbox.y0],
            [bbox.x1, bbox.y0],
            [bbox.x1, bbox.y1],
            [bbox.x0, bbox.y1],
            [bbox.x0, bbox.y0],
        ]
    )


def _path_from_line(ax: Axes, line: Artist) -> _PathObstacle:
    """Extract display-space path from a Line2D."""
    data_path = line.get_path()
    transform = line.get_transform()
    vertices = transform.transform(data_path.vertices)
    display_path = MplPath(vertices, data_path.codes)
    return _PathObstacle(ax, line, [display_path], filled=False, debug_color="orange")


def _path_from_patch(ax: Axes, patch: Artist) -> _PathObstacle:
    """Extract display-space path from a Patch (Rectangle, Wedge, etc.).

    ``Patch.get_transform()`` already includes ``get_patch_transform()``,
    so using it directly maps unit path -> data -> display in one step.
    """
    path = patch.get_path()
    display_path = path.transformed(patch.get_transform())
    return _PathObstacle(ax, patch, [display_path], filled=True, debug_color="red")


def _path_from_collection(
    ax: Axes, collection: Artist, renderer: RendererBase
) -> _PathObstacle:
    """Extract display-space paths from a Collection (scatter, etc.)."""
    offsets = collection.get_offsets()

    if len(offsets) == 0:
        return _PathObstacle(ax, collection, [], filled=True, debug_color="purple")

    paths = collection.get_paths()
    if not paths:
        return _PathObstacle(ax, collection, [], filled=True, debug_color="purple")

    element_transforms = collection.get_transforms()
    offset_transform = collection.get_offset_transform()
    display_offsets = offset_transform.transform(offsets)

    display_paths: list[MplPath] = []
    for i, doff in enumerate(display_offsets):
        base = paths[i % len(paths)]
        if len(element_transforms) > 0:
            et = element_transforms[i % len(element_transforms)]
            scaled = base.transformed(Affine2D(et))
        else:
            scaled = base
        translated = scaled.transformed(Affine2D().translate(doff[0], doff[1]))
        display_paths.append(translated)

    return _PathObstacle(
        ax,
        collection,
        display_paths,
        filled=True,
        debug_color="purple",
    )


def _path_from_extent(
    ax: Axes, artist: Artist, renderer: RendererBase
) -> _PathObstacle:
    """Fallback: use the artist's bounding box as a filled rectangle."""
    extent = artist.get_window_extent(renderer)
    return _PathObstacle(
        ax,
        artist,
        [_bbox_to_path(extent)],
        filled=True,
        debug_color="red",
    )


# -- Protocol + registration --


@runtime_checkable
class PositionableArtist(Protocol):
    """Artist that supports repositioning via get/set_position."""

    def get_position(self) -> tuple[float, float]: ...
    def set_position(self, xy: tuple[float, float]) -> None: ...
    def get_window_extent(self, renderer: RendererBase | None = None) -> Bbox: ...


def register_moveable(ax: Axes, artist: Artist) -> None:
    """Register Artist that can be repositioned by the engine."""
    _labels.setdefault(ax, []).append(artist)


def register_artist_obstacle(
    ax: Axes, artist: Artist, *, filled: bool = False, colocate: bool = False
) -> None:
    """Register an Artist whose geometry should repel moveable labels.

    The artist's actual path is extracted and used for precise collision
    detection via ``Path.intersects_bbox()``.

    Args:
        filled: ``True`` for shapes (bars, wedges), ``False`` for lines.
        colocate: ``True`` for data lines where labels naturally start ON
            the line. The co-location skip allows the label to remain at
            its origin without being repelled by the line it belongs to.
    """
    _artist_obstacles.setdefault(ax, []).append((artist, filled, colocate))


def register_passive(ax: Axes, artist: Artist) -> None:
    """Register Artist that does not participate in collision resolution.

    Auto-detected patches and collections are treated as obstacles by
    default. Use this to exclude background visuals (bands, shaded areas).
    """
    _passive.setdefault(ax, []).append(artist)


# -- Public entry points --


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

    fixed = _collect_obstacles(ax, moveables, renderer)
    logger.debug(
        "Collision: {} moveable(s), {} obstacle(s)", len(positionable), len(fixed)
    )

    axes_bbox = ax.get_window_extent(renderer)

    _resolve_all(positionable, fixed, renderer, axes_bbox, collision)

    _add_connectors(positionable, original_positions, renderer, config)

    if debug:
        passive_obs = _collect_passive_obstacles(ax, renderer)
        _draw_debug_overlay(
            fig,
            positionable,
            fixed,
            renderer,
            axes_bbox,
            collision,
            passive=passive_obs,
        )


def resolve_composed_collisions(axes: Sequence[Axes], *, debug: bool = False) -> None:
    """Resolve collisions across multiple axes simultaneously.

    Merges all moveable labels from every axes into a single pool
    and resolves them together in pixel space.
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

    seen_ids: set[int] = set()
    fixed: list[_PathObstacle] = []
    for ax in axes:
        for obs in _collect_obstacles(ax, all_moveables, renderer):
            if obs._source_id not in seen_ids:
                fixed.append(obs)
                seen_ids.add(obs._source_id)

    logger.debug(
        "Composed collision: {} moveable(s), {} obstacle(s), {} axes",
        len(positionable),
        len(fixed),
        len(axes),
    )

    axes_bbox = axes[0].get_window_extent(renderer)

    _resolve_all(positionable, fixed, renderer, axes_bbox, collision)

    _add_connectors(positionable, original_positions, renderer, config)

    if debug:
        passive_obs: list[_PathObstacle] = []
        seen_passive: set[int] = set()
        for ax in axes:
            for obs in _collect_passive_obstacles(ax, renderer):
                if obs._source_id not in seen_passive:
                    passive_obs.append(obs)
                    seen_passive.add(obs._source_id)
        _draw_debug_overlay(
            fig,
            positionable,
            fixed,
            renderer,
            axes_bbox,
            collision,
            passive=passive_obs,
        )


# -- Core resolution --


def _resolve_all(
    moveables: Sequence[PositionableArtist],
    obstacles: list[_PathObstacle],
    renderer: RendererBase,
    axes_bbox: Bbox,
    collision: CollisionConfig,
) -> None:
    """Resolve all collisions (obstacles + inter-label) in a unified pass."""
    obstacle_pad = collision.obstacle_padding_px
    label_pad = collision.label_padding_px

    for _ in range(collision.max_iterations):
        any_moved = False

        for i, label in enumerate(moveables):
            raw_bbox = label.get_window_extent(renderer)
            if raw_bbox.width < 1 and raw_bbox.height < 1:
                continue

            label_ax = label.axes  # type: ignore[union-attr]

            # Co-location skip: data lines (colocate=True) on same axis
            # where the label starts ON the line are excluded. Reference
            # lines (colocate=False) always participate in repulsion.
            active_obs: list[_PathObstacle] = []
            for obs in obstacles:
                if (
                    obs._colocate
                    and obs._ax is label_ax
                    and obs.intersects(raw_bbox, renderer)
                ):
                    continue
                active_obs.append(obs)

            # Bboxes from other moveable labels
            label_bboxes: list[Bbox] = []
            for j, other in enumerate(moveables):
                if j != i:
                    label_bboxes.append(
                        _pad_bbox(other.get_window_extent(renderer), label_pad)
                    )

            # Detect collisions
            padded_label = _pad_bbox(raw_bbox, label_pad)
            colliding: list[Bbox] = [
                lb for lb in label_bboxes if padded_label.overlaps(lb)
            ]

            for obs in active_obs:
                pad = obstacle_pad if obs._filled else 0.0
                if obs.intersects(padded_label, renderer, padding=pad):
                    obs_bbox = obs.local_bbox(raw_bbox, label_pad * 2, renderer)
                    if pad > 0:
                        obs_bbox = _pad_bbox(obs_bbox, pad)
                    colliding.append(obs_bbox)

            if not colliding:
                continue

            result = _find_free_position(
                raw_bbox,
                colliding,
                label_bboxes,
                active_obs,
                obstacle_pad,
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
    label_bboxes: list[Bbox],
    obstacles: list[_PathObstacle],
    obstacle_pad: float,
    renderer: RendererBase,
) -> bool:
    """Check if a position is free from all label and path obstacles."""
    if any(bbox.overlaps(lb) for lb in label_bboxes):
        return False
    return not any(
        obs.intersects(bbox, renderer, padding=obstacle_pad if obs._filled else 0.0)
        for obs in obstacles
    )


def _find_free_position(
    label_bbox: Bbox,
    colliding_bboxes: list[Bbox],
    label_bboxes: list[Bbox],
    obstacles: list[_PathObstacle],
    obstacle_pad: float,
    movement: str,
    axes_bbox: Bbox,
    label_pad: float,
    renderer: RendererBase,
) -> tuple[float, float] | None:
    """Find the smallest displacement that frees label_bbox from all obstacles.

    Generates candidate displacements from each colliding obstacle, validates
    them against all obstacles, and returns the best option.
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

    def _sort_key(c: tuple[float, float, float]) -> tuple[int, float]:
        dx, dy, dist = c
        if dx == 0:
            return (0, dist)  # Y-only
        if dy == 0:
            return (1, dist)  # X-only
        return (2, dist)  # diagonal

    candidates.sort(key=_sort_key)

    if movement == "y":
        ordered = [c for c in candidates if c[0] == 0]
        ordered.extend(c for c in candidates if c[0] != 0)
    elif movement == "x":
        ordered = [c for c in candidates if c[1] == 0]
        ordered.extend(c for c in candidates if c[1] != 0)
    else:
        ordered = candidates

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
        if _position_is_free(
            shifted_padded, label_bboxes, obstacles, obstacle_pad, renderer
        ):
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
                    shifted_padded,
                    label_bboxes,
                    obstacles,
                    obstacle_pad,
                    renderer,
                ):
                    return (dx_combo, dy_combo)

    return None


# -- Geometry helpers --


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


# -- Connectors + Debug --


def _add_connectors(
    moveables: Sequence[PositionableArtist],
    original_positions: list[tuple[float, float]],
    renderer: RendererBase,
    config: ChartingConfig,
) -> None:
    """Add guide lines for moveables displaced beyond the threshold."""
    collision = config.collision
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


def _collect_passive_obstacles(ax: Axes, renderer: RendererBase) -> list[_PathObstacle]:
    """Collect passive artists as obstacles for debug visualization."""
    sibling_axes = list(ax.get_shared_x_axes().get_siblings(ax))
    obstacles: list[_PathObstacle] = []
    seen: set[int] = set()

    for sibling in sibling_axes:
        for artist in _passive.get(sibling, []):
            aid = id(artist)
            if aid in seen or not artist.get_visible():
                continue
            seen.add(aid)
            if hasattr(artist, "get_paths") and hasattr(artist, "get_offsets"):
                obs = _path_from_collection(sibling, artist, renderer)
            elif hasattr(artist, "get_patch_transform"):
                obs = _path_from_patch(sibling, artist)
            else:
                obs = _path_from_extent(sibling, artist, renderer)
            obs._debug_color = "gray"
            obstacles.append(obs)

    return obstacles


def _draw_debug_overlay(
    fig: Figure,
    moveables: Sequence[PositionableArtist],
    obstacles: list[_PathObstacle],
    renderer: RendererBase,
    axes_bbox: Bbox,
    collision: CollisionConfig,
    *,
    passive: list[_PathObstacle] | None = None,
) -> None:
    """Draw translucent collision visuals for debugging."""
    label_pad = collision.label_padding_px
    inv = fig.transFigure.inverted()

    def _add_rect(bbox_raw: Bbox, color: str, alpha: float) -> None:
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

    def _draw_obstacles(
        obs_list: list[_PathObstacle],
        *,
        linestyle: str = "solid",
    ) -> None:
        for obs in obs_list:
            is_passive = linestyle == "dashed"
            for path in obs._display_paths:
                if obs._filled:
                    draw_path = path.clip_to_bbox(axes_bbox)
                    if len(draw_path.vertices) < 2:
                        continue
                else:
                    draw_path = path
                fig_verts = inv.transform(draw_path.vertices)
                if is_passive:
                    face_alpha = 0.15
                    edge_alpha = 0.15
                    lw = 1
                elif obs._filled:
                    face_alpha = 0.25
                    edge_alpha = 0.25
                    lw = 1
                else:
                    face_alpha = 0.0
                    edge_alpha = 0.5
                    lw = 4
                fig.patches.append(
                    mpatches.PathPatch(
                        MplPath(fig_verts, draw_path.codes),
                        facecolor=obs._debug_color
                        if (obs._filled or is_passive)
                        else "none",
                        edgecolor=obs._debug_color,
                        linewidth=lw,
                        alpha=max(face_alpha, edge_alpha),
                        linestyle=linestyle,
                        joinstyle="round",
                        capstyle="round",
                        transform=fig.transFigure,
                        clip_on=True,
                        zorder=100,
                    )
                )

    # Active obstacles
    _draw_obstacles(obstacles)

    # Passive obstacles (gray, dashed)
    if passive:
        _draw_obstacles(passive, linestyle="dashed")

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


def _collect_obstacles(
    ax: Axes, moveables: list[Artist], renderer: RendererBase
) -> list[_PathObstacle]:
    """Collect obstacles from patches, collections, and registered artists.

    In composed charts with twinx, labels from one axis must also avoid
    patches, collections, labels and line paths on the sibling axis.
    """
    moveable_ids = {id(m) for m in moveables}
    sibling_axes = list(ax.get_shared_x_axes().get_siblings(ax))
    passive_ids = {id(p) for sibling in sibling_axes for p in _passive.get(sibling, [])}
    seen: set[int] = set()
    obstacles: list[_PathObstacle] = []

    # 1-3. Auto-detect from sibling axes
    for sibling in sibling_axes:
        # 1. Patches (bars, boxes, etc.) -> real patch geometry
        for patch in sibling.patches:
            pid = id(patch)
            if (
                pid not in moveable_ids
                and pid not in passive_ids
                and pid not in seen
                and patch.get_visible()
            ):
                obstacles.append(_path_from_patch(sibling, patch))
                seen.add(pid)

        # 2. Collections (scatter, violin, fill_between, etc.)
        for collection in sibling.collections:
            cid = id(collection)
            if (
                cid not in moveable_ids
                and cid not in passive_ids
                and cid not in seen
                and collection.get_visible()
            ):
                obstacles.append(_path_from_collection(sibling, collection, renderer))
                seen.add(cid)

        # 3. Labels from sibling axes (twinx) -> extent
        if sibling is not ax:
            for label in _labels.get(sibling, []):
                lid = id(label)
                if (
                    lid not in moveable_ids
                    and lid not in passive_ids
                    and lid not in seen
                    and label.get_visible()
                ):
                    obstacles.append(_path_from_extent(sibling, label, renderer))
                    seen.add(lid)

    # 4. Explicitly registered artist obstacles -> dispatch by type
    for sibling in sibling_axes:
        for artist, filled, colocate in _artist_obstacles.get(sibling, []):
            if not artist.get_visible():
                continue
            aid = id(artist)
            if aid in seen or aid in passive_ids:
                continue
            seen.add(aid)
            if not filled and hasattr(artist, "get_path"):
                obs = _path_from_line(sibling, artist)
                obs._colocate = colocate
                obstacles.append(obs)
            elif hasattr(artist, "get_paths") and hasattr(artist, "get_offsets"):
                obstacles.append(_path_from_collection(sibling, artist, renderer))
            elif hasattr(artist, "get_patch_transform"):
                obstacles.append(_path_from_patch(sibling, artist))
            else:
                obstacles.append(_path_from_extent(sibling, artist, renderer))

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
    final_x = num_x if dx_px == 0 else new_data[0]
    final_y = num_y if dy_px == 0 else new_data[1]
    label.set_position((final_x, final_y))
