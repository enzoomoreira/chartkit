"""Auto-rotation of X-axis tick labels to prevent overlap."""

from __future__ import annotations

from typing import Literal

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from ..settings import get_config

__all__ = ["apply_tick_rotation"]


def _has_overlap(fig: plt.Figure, ax: Axes) -> bool:
    """Check if adjacent X tick labels overlap."""
    renderer = fig.canvas.get_renderer()
    labels = [t for t in ax.get_xticklabels() if t.get_text()]

    if len(labels) < 2:
        return False

    for i in range(len(labels) - 1):
        bbox_curr = labels[i].get_window_extent(renderer)
        bbox_next = labels[i + 1].get_window_extent(renderer)
        if bbox_curr.x1 > bbox_next.x0:
            return True

    return False


def _adjust_bottom_margin(fig: plt.Figure, ax: Axes) -> None:
    """Push axes up if rotated tick labels overlap the footer area."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    labels = [t for t in ax.get_xticklabels() if t.get_text()]
    if not labels:
        return

    # Lowest tick label extent in figure-fraction coordinates
    min_y = min(
        label.get_window_extent(renderer).transformed(fig.transFigure.inverted()).y0
        for label in labels
    )

    config = get_config()
    footer_y = config.layout.footer.y

    # Estimate footer text height (points -> inches -> figure fraction)
    footer_height = (config.fonts.sizes.footer / 72) / fig.get_size_inches()[1]
    clearance = footer_y + footer_height + 0.01

    if min_y >= clearance:
        return

    current_bottom = ax.get_position().y0
    fig.subplots_adjust(bottom=current_bottom + (clearance - min_y))


def apply_tick_rotation(
    fig: plt.Figure,
    ax: Axes,
    *,
    tick_rotation: int | Literal["auto"] | None = None,
) -> None:
    """Apply rotation to X-axis tick labels.

    Resolution order: ``tick_rotation`` parameter > ``config.ticks.rotation``.
    When ``"auto"``, rotation is applied only if adjacent labels overlap.
    After rotation, the bottom margin is adjusted so labels do not overlap
    the footer.
    """
    config = get_config()
    effective = tick_rotation if tick_rotation is not None else config.ticks.rotation

    if effective == "auto":
        fig.canvas.draw()
        if not _has_overlap(fig, ax):
            return
        angle = config.ticks.auto_rotation_angle
    else:
        angle = effective

    if angle == 0:
        return

    ha = "right" if angle > 0 else "center"
    plt.setp(ax.get_xticklabels(), rotation=angle, ha=ha)

    _adjust_bottom_margin(fig, ax)
