"""Auto-rotation of X-axis tick labels to prevent overlap."""

from __future__ import annotations

from typing import Literal

from matplotlib.artist import setp
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ..exceptions import ValidationError
from ..settings import get_config
from .rendering import get_renderer

__all__ = ["apply_tick_rotation"]


def _is_crowded(fig: Figure, ax: Axes, min_gap_px: float) -> bool:
    """Whether adjacent X tick labels come closer than *min_gap_px*.

    Strict intersection is not the bar to clear. Twenty quarterly labels came
    out with 0.96px between them -- none of them touching, all of them reading
    as one long word.
    """
    renderer = get_renderer(fig)
    labels = [t for t in ax.get_xticklabels() if t.get_text()]

    if len(labels) < 2:
        return False

    for i in range(len(labels) - 1):
        bbox_curr = labels[i].get_window_extent(renderer)
        bbox_next = labels[i + 1].get_window_extent(renderer)
        if bbox_curr.x1 + min_gap_px > bbox_next.x0:
            return True

    return False


def _adjust_bottom_margin(fig: Figure, ax: Axes) -> None:
    """Push axes up if rotated tick labels overlap the footer area."""
    fig.canvas.draw()
    renderer = get_renderer(fig)

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


def _apply_angle(ax: Axes, angle: int) -> None:
    """Set rotation, horizontal alignment and rotation mode on X tick labels."""
    if abs(angle) == 90:
        ha, rotation_mode = "center", "default"
    elif angle > 0:
        ha, rotation_mode = "right", "anchor"
    else:
        ha, rotation_mode = "left", "anchor"

    setp(
        ax.get_xticklabels(),
        rotation=angle,
        ha=ha,
        rotation_mode=rotation_mode,
    )


def apply_tick_rotation(
    fig: Figure,
    ax: Axes,
    *,
    tick_rotation: int | Literal["auto"] | None = None,
) -> None:
    """Apply rotation to X-axis tick labels.

    Resolution order: ``tick_rotation`` parameter > ``config.ticks.rotation``.
    When ``"auto"``, rotation is applied once adjacent labels come within
    ``config.ticks.min_gap_px`` of each other. If the configured angle is
    insufficient, escalates to 90 degrees. After rotation, the bottom margin
    is adjusted so labels do not overlap the footer.
    """
    config = get_config()
    effective = tick_rotation if tick_rotation is not None else config.ticks.rotation

    if effective == "auto":
        min_gap = config.ticks.min_gap_px
        fig.canvas.draw()
        if not _is_crowded(fig, ax, min_gap):
            return
        angle = config.ticks.auto_rotation_angle

        _apply_angle(ax, angle)

        if angle != 90:
            fig.canvas.draw()
            # Strict intersection here, not min_gap: the bounding box of a
            # rotated label is its diagonal envelope, so two 45-degree labels
            # measure ~1px apart horizontally while reading perfectly clear of
            # each other. Demanding a gap of that number escalates everything
            # to 90 degrees.
            if _is_crowded(fig, ax, 0.0):
                angle = 90
                _apply_angle(ax, angle)
    else:
        # bool is a subclass of int, so ``tick_rotation=True`` would silently mean
        # a 1 degree rotation -- almost certainly not what the caller meant.
        if isinstance(effective, bool) or not isinstance(effective, int):
            raise ValidationError(
                f"tick_rotation must be an int or 'auto', got {type(effective).__name__}: {effective!r}"
            )
        angle = effective

    if angle == 0:
        return

    if effective != "auto":
        _apply_angle(ax, angle)

    _adjust_bottom_margin(fig, ax)
