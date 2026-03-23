"""Collision resolution engine: entry points, core resolution, and connectors."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from itertools import chain
from math import sqrt

import matplotlib.dates as mdates
from loguru import logger
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.transforms import Bbox

from ...settings import get_config
from ...settings.schema import ChartingConfig, CollisionConfig
from ._debug import _draw_debug_overlay
from ._obstacles import (
    _PathObstacle,
    _collect_obstacles,
    _collect_passive_obstacles,
    _pad_bbox,
    _shift_bbox,
)
from ._registry import PositionableArtist, _labels


# -- Shared setup --


def _prepare_resolution(
    moveables: list[Artist],
    fig_source: Axes,
) -> tuple[list[PositionableArtist], list[tuple[float, float]], ChartingConfig] | None:
    """Shared setup for resolve_collisions and resolve_composed_collisions.

    Returns (positionable, original_positions, config) or None if nothing to do.
    """
    config = get_config()

    fig = fig_source.figure
    fig.draw_without_rendering()

    positionable = [m for m in moveables if isinstance(m, PositionableArtist)]
    if not positionable:
        return None

    original_positions = [_pos_to_numeric(*m.get_position()) for m in positionable]
    return positionable, original_positions, config


# -- Public entry points --


def resolve_collisions(ax: Axes) -> None:
    """Resolve all registered collisions in a single axes."""
    moveables = _labels.get(ax, [])
    if not moveables:
        return

    result = _prepare_resolution(moveables, ax)
    if result is None:
        return
    positionable, original_positions, config = result
    collision = config.collision
    renderer = ax.figure.canvas.get_renderer()  # type: ignore[attr-defined]

    fixed = _collect_obstacles(ax, moveables, renderer)
    logger.debug(
        "Collision: {} moveable(s), {} obstacle(s)", len(positionable), len(fixed)
    )

    axes_bbox = ax.get_window_extent(renderer)
    _resolve_all(positionable, fixed, renderer, axes_bbox, collision)
    _add_connectors(positionable, original_positions, renderer, config)


def resolve_composed_collisions(axes: Sequence[Axes]) -> None:
    """Resolve collisions across multiple axes simultaneously.

    Merges all moveable labels from every axes into a single pool
    and resolves them together in pixel space.
    """
    all_moveables: list[Artist] = []
    for ax in axes:
        all_moveables.extend(_labels.get(ax, []))
    if not all_moveables:
        return

    result = _prepare_resolution(all_moveables, axes[0])
    if result is None:
        return
    positionable, original_positions, config = result
    collision = config.collision
    renderer = axes[0].figure.canvas.get_renderer()  # type: ignore[attr-defined]

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


def draw_debug_overlay(ax: Axes) -> None:
    """Draw collision debug overlay with fresh geometry.

    Call after ``finalize_chart()`` so the overlay reflects the final
    axes position (after tick rotation / subplots_adjust).
    """
    moveables = _labels.get(ax, [])
    if not moveables:
        return

    config = get_config()
    fig = ax.figure
    fig.draw_without_rendering()
    renderer = fig.canvas.get_renderer()  # type: ignore[attr-defined]

    positionable = [m for m in moveables if isinstance(m, PositionableArtist)]
    if not positionable:
        return

    fixed = _collect_obstacles(ax, moveables, renderer)
    passive = _collect_passive_obstacles(ax, renderer)
    axes_bbox = ax.get_window_extent(renderer)

    _draw_debug_overlay(
        fig, positionable, fixed, renderer, axes_bbox, config.collision, passive=passive
    )


def draw_composed_debug_overlay(axes: Sequence[Axes]) -> None:
    """Draw collision debug overlay for composed charts with fresh geometry.

    Call after ``finalize_chart()`` so the overlay reflects the final
    axes position (after tick rotation / subplots_adjust).
    """
    all_moveables: list[Artist] = []
    for ax in axes:
        all_moveables.extend(_labels.get(ax, []))
    if not all_moveables:
        return

    config = get_config()
    fig = axes[0].figure
    fig.draw_without_rendering()
    renderer = fig.canvas.get_renderer()  # type: ignore[attr-defined]

    positionable = [m for m in all_moveables if isinstance(m, PositionableArtist)]
    if not positionable:
        return

    seen_ids: set[int] = set()
    fixed: list[_PathObstacle] = []
    for ax in axes:
        for obs in _collect_obstacles(ax, all_moveables, renderer):
            if obs._source_id not in seen_ids:
                fixed.append(obs)
                seen_ids.add(obs._source_id)

    passive: list[_PathObstacle] = []
    seen_passive: set[int] = set()
    for ax in axes:
        for obs in _collect_passive_obstacles(ax, renderer):
            if obs._source_id not in seen_passive:
                passive.append(obs)
                seen_passive.add(obs._source_id)

    axes_bbox = axes[0].get_window_extent(renderer)

    _draw_debug_overlay(
        fig, positionable, fixed, renderer, axes_bbox, config.collision, passive=passive
    )


# -- Cost function weights (not user-configurable) --

_WEIGHT_DISTANCE = 1.0
_WEIGHT_AXIS = 3.0
_WEIGHT_EDGE = 5.0

# 8 cardinal directions: N, NE, E, SE, S, SW, W, NW
_DIRECTIONS: list[tuple[float, float]] = [
    (0, 1),
    (1, 1),
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, -1),
    (-1, 0),
    (-1, 1),
]

_SQRT2 = sqrt(2)


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

    # Snapshot anchor bboxes before any movement
    anchor_bboxes: dict[int, Bbox] = {}
    for label in moveables:
        raw = label.get_window_extent(renderer)
        anchor_bboxes[id(label)] = Bbox.from_extents(raw.x0, raw.y0, raw.x1, raw.y1)

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
                anchor_bboxes[id(label)],
                colliding,
                label_bboxes,
                active_obs,
                obstacle_pad,
                collision.movement,
                axes_bbox,
                label_pad,
                renderer,
                collision.candidate_distances,
                collision.edge_margin_factor,
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
    anchor_bbox: Bbox,
    colliding_bboxes: list[Bbox],
    label_bboxes: list[Bbox],
    obstacles: list[_PathObstacle],
    obstacle_pad: float,
    movement: str,
    axes_bbox: Bbox,
    label_pad: float,
    renderer: RendererBase,
    candidate_distances: tuple[float, ...],
    edge_margin_factor: float,
) -> tuple[float, float] | None:
    """Find the lowest-cost displacement that frees label_bbox from collisions.

    Generates proactive candidates in 8 cardinal directions at multiple
    distances, plus reactive snap-to-edge candidates per colliding obstacle.
    Scores each valid candidate with a continuous cost function and returns
    the one with the lowest cost.
    """
    edge_margin = edge_margin_factor * label_bbox.height

    proactive = _generate_proactive_candidates(
        anchor_bbox, label_bbox, axes_bbox, candidate_distances
    )
    clearance = label_pad + 1.0
    reactive: list[tuple[float, float, float]] = []
    for obs in colliding_bboxes:
        reactive.extend(
            _generate_reactive_candidates(label_bbox, obs, clearance, axes_bbox)
        )

    logger.debug("Candidates: {} proactive, {} reactive", len(proactive), len(reactive))

    best_cost = float("inf")
    best_displacement: tuple[float, float] | None = None
    valid_count = 0

    total = len(proactive) + len(reactive)
    for dx, dy, _ in chain(proactive, reactive):
        shifted_padded = _pad_bbox(_shift_bbox(label_bbox, dx, dy), label_pad)
        if not _position_is_free(
            shifted_padded, label_bboxes, obstacles, obstacle_pad, renderer
        ):
            continue

        valid_count += 1
        cost = _compute_placement_cost(
            dx, dy, anchor_bbox, label_bbox, axes_bbox, movement, edge_margin
        )
        if cost < best_cost:
            best_cost = cost
            best_displacement = (dx, dy)

    if best_displacement is not None:
        dx, dy = best_displacement
        logger.debug(
            "Best candidate: cost={:.2f} (dist={:.2f}, valid={}/{})",
            best_cost,
            sqrt(dx**2 + dy**2) / max(label_bbox.height, 1.0),
            valid_count,
            total,
        )

    return best_displacement


# -- Candidate generation --


def _generate_proactive_candidates(
    anchor_bbox: Bbox,
    label_bbox: Bbox,
    axes_bbox: Bbox,
    distances: tuple[float, ...],
) -> list[tuple[float, float, float]]:
    """Generate candidates in 8 cardinal directions at multiple distances.

    Each distance is a multiplier of the label height. Candidates are
    positioned relative to the anchor point (original label position).
    """
    label_h = label_bbox.height
    anchor_cx = (anchor_bbox.x0 + anchor_bbox.x1) / 2
    anchor_cy = (anchor_bbox.y0 + anchor_bbox.y1) / 2
    label_cx = (label_bbox.x0 + label_bbox.x1) / 2
    label_cy = (label_bbox.y0 + label_bbox.y1) / 2

    candidates: list[tuple[float, float, float]] = []
    for dist_mult in distances:
        step = dist_mult * label_h
        for dir_x, dir_y in _DIRECTIONS:
            # Normalize diagonal directions
            norm = _SQRT2 if dir_x != 0 and dir_y != 0 else 1.0
            target_cx = anchor_cx + (dir_x / norm) * step
            target_cy = anchor_cy + (dir_y / norm) * step

            dx = target_cx - label_cx
            dy = target_cy - label_cy

            # Bounds check
            new_x0 = label_bbox.x0 + dx
            new_x1 = label_bbox.x1 + dx
            new_y0 = label_bbox.y0 + dy
            new_y1 = label_bbox.y1 + dy
            if (
                new_x0 >= axes_bbox.x0
                and new_x1 <= axes_bbox.x1
                and new_y0 >= axes_bbox.y0
                and new_y1 <= axes_bbox.y1
            ):
                distance = sqrt(dx**2 + dy**2)
                candidates.append((dx, dy, distance))

    return candidates


def _generate_reactive_candidates(
    mov_bbox: Bbox,
    fix_bbox: Bbox,
    padding_px: float,
    axes_bbox: Bbox,
) -> list[tuple[float, float, float]]:
    """Compute snap-to-edge displacement options per colliding obstacle.

    Generates up to 4 candidates (above, below, right, left) that place
    the label just outside the obstacle bounding box.
    """
    options: list[tuple[float, float, float]] = []

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


# -- Cost function --


def _edge_proximity_cost(bbox: Bbox, axes_bbox: Bbox, margin: float) -> float:
    """Linear penalty when label is within ``margin`` pixels of any axes edge.

    Returns 0.0 when safely away, scales to 1.0 when touching the edge.
    """
    if margin <= 0:
        return 0.0

    gaps = [
        bbox.x0 - axes_bbox.x0,  # left
        axes_bbox.x1 - bbox.x1,  # right
        bbox.y0 - axes_bbox.y0,  # bottom
        axes_bbox.y1 - bbox.y1,  # top
    ]
    min_gap = min(gaps)
    if min_gap >= margin:
        return 0.0
    return max(0.0, min(1.0, 1.0 - min_gap / margin))


def _compute_placement_cost(
    dx: float,
    dy: float,
    anchor_bbox: Bbox,
    label_bbox: Bbox,
    axes_bbox: Bbox,
    movement: str,
    edge_margin: float,
) -> float:
    """Continuous cost function for candidate placement.

    Three weighted components:
    - Distance from anchor (w=1.0): normalized by label height
    - Axis preference (w=3.0): penalizes off-axis movement
    - Edge proximity (w=5.0): penalizes placements near axes borders
    """
    label_h = max(label_bbox.height, 1.0)

    # 1. Distance from anchor (scale-independent)
    dist_cost = sqrt(dx**2 + dy**2) / label_h

    # 2. Axis preference
    is_y_only = abs(dx) < 0.5
    is_x_only = abs(dy) < 0.5
    is_diagonal = not is_y_only and not is_x_only

    if movement == "y":
        axis_cost = 0.0 if is_y_only else (1.5 if is_diagonal else 1.0)
    elif movement == "x":
        axis_cost = 0.0 if is_x_only else (1.5 if is_diagonal else 1.0)
    else:  # "xy"
        if is_y_only or is_x_only:
            axis_cost = 0.0 if is_y_only else 0.5
        else:
            axis_cost = 1.0

    # 3. Edge proximity
    shifted = _shift_bbox(label_bbox, dx, dy)
    edge_cost = _edge_proximity_cost(shifted, axes_bbox, edge_margin)

    return (
        _WEIGHT_DISTANCE * dist_cost
        + _WEIGHT_AXIS * axis_cost
        + _WEIGHT_EDGE * edge_cost
    )


# -- Connectors --


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


# -- Internal helpers --


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
