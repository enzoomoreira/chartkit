"""Collision resolution engine: entry points, core resolution, and connectors."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
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


def _axis_priority(c: tuple[float, float, float], movement: str) -> tuple[int, float]:
    """Unified sort key that combines axis preference and distance."""
    dx, dy, dist = c
    is_y_only = dx == 0
    is_x_only = dy == 0

    if movement == "y":
        return (0 if is_y_only else 1, dist)
    if movement == "x":
        return (0 if is_x_only else 1, dist)
    # "both" -- prefer Y-only, then X-only, then diagonal
    if is_y_only:
        return (0, dist)
    if is_x_only:
        return (1, dist)
    return (2, dist)


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

    candidates.sort(key=lambda c: _axis_priority(c, movement))

    for dx, dy, _ in candidates:
        shifted_padded = _pad_bbox(_shift_bbox(label_bbox, dx, dy), label_pad)
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
                    _shift_bbox(label_bbox, dx_combo, dy_combo), label_pad
                )
                if _position_is_free(
                    shifted_padded, label_bboxes, obstacles, obstacle_pad, renderer
                ):
                    return (dx_combo, dy_combo)

    return None


# -- Geometry helpers --


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
