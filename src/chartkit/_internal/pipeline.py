"""Shared pipeline steps for chart creation and finalization."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from .extraction import should_show_legend
from .plot_validation import coerce_axis_limits
from .tick_formatting import apply_tick_formatting
from .tick_rotation import apply_tick_rotation
from ..decorations import add_footer, add_title
from ..settings import get_config
from ..styling.theme import theme

if TYPE_CHECKING:
    import pandas as pd

    from .plot_validation import AxisLimits

__all__ = ["apply_legend", "create_figure", "finalize_chart"]


def create_figure(
    *,
    figsize: tuple[float, float] | None = None,
    grid: bool | None = None,
) -> tuple[plt.Figure, Axes]:
    """Apply theme, create figure/axes and optionally override grid.

    Args:
        figsize: Override figure size. ``None`` uses config default.
        grid: Grid override. ``None`` uses config default.
    """
    theme.apply()
    config = get_config()
    effective_figsize = figsize or config.layout.figsize
    fig, ax = plt.subplots(figsize=effective_figsize)

    if grid is not None:
        ax.grid(grid)

    return fig, ax


def apply_legend(
    ax_left: Axes,
    ax_right: Axes | None = None,
    *,
    legend: bool | None = None,
) -> None:
    """Apply legend with optional dual-axis handle consolidation.

    When ``ax_right`` is provided, handles and labels from both axes are
    merged into a single legend on ``ax_left``, and any existing legend
    on ``ax_right`` is removed to avoid duplicates.
    """
    handles, labels = ax_left.get_legend_handles_labels()

    if ax_right is not None:
        h_right, l_right = ax_right.get_legend_handles_labels()
        handles += h_right
        labels += l_right
        existing = ax_right.get_legend()
        if existing is not None:
            existing.remove()

    if not should_show_legend(labels, legend) or not labels:
        return

    config = get_config()
    ax_left.legend(
        handles,
        labels,
        loc=config.legend.loc,
        frameon=config.legend.frameon,
        framealpha=config.legend.alpha,
    )


def finalize_chart(
    fig: plt.Figure,
    ax: Axes,
    *,
    tick_format: str | None = None,
    tick_freq: str | None = None,
    tick_rotation: int | Literal["auto"] | None = None,
    x_data: pd.Index | pd.Series | None = None,
    xlim: AxisLimits | None = None,
    ylim: AxisLimits | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    title: str | None = None,
    source: str | None = None,
) -> None:
    """Run post-render pipeline steps shared by engine and compose.

    Applies tick formatting, tick rotation, axis limits, axis labels,
    and decorations (title + footer) in the canonical order.
    """
    apply_tick_formatting(
        ax, tick_format=tick_format, tick_freq=tick_freq, x_data=x_data
    )
    apply_tick_rotation(fig, ax, tick_rotation=tick_rotation)

    if xlim is not None:
        ax.set_xlim(coerce_axis_limits(xlim))
    if ylim is not None:
        ax.set_ylim(coerce_axis_limits(ylim))

    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)

    add_title(ax, title)
    add_footer(fig, source)
