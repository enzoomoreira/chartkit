"""Shared pipeline steps for chart creation and finalization."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ..decorations import add_footer, add_title
from ..settings import get_config
from .extraction import should_show_legend
from .plot_validation import coerce_axis_limits
from .tick_formatting import apply_tick_formatting
from .tick_rotation import apply_tick_rotation

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import pandas as pd

    from .plot_validation import AxisLimits

__all__ = ["apply_legend", "create_figure", "finalize_chart"]


def create_figure(
    *,
    figsize: tuple[float, float] | None = None,
    grid: bool | None = None,
) -> tuple[Figure, Axes]:
    """Create a figure/axes pair and optionally override grid.

    The figure is built directly rather than through ``pyplot`` so it is not
    registered in the global figure manager -- otherwise every chart would
    stay alive for the lifetime of the process. Attaching an Agg canvas also
    guarantees a renderer is available whatever backend the caller selected.

    Must be called inside ``theme.context()``: matplotlib reads rcParams when
    the figure and its artists are created.

    Args:
        figsize: Override figure size. ``None`` uses config default.
        grid: Grid override. ``None`` uses config default.
    """
    config = get_config()
    effective_figsize = figsize or config.layout.figsize

    fig = Figure(figsize=effective_figsize)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot()

    if grid is not None:
        ax.grid(grid)

    logger.debug(
        "create_figure: figsize=%s, grid_override=%s",
        effective_figsize,
        grid,
    )

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
        logger.debug(
            "Legend skipped: %s label(s), legend=%s",
            len(labels),
            legend,
        )
        return

    config = get_config()
    ax_left.legend(
        handles,
        labels,
        loc=config.legend.loc,
        frameon=config.legend.frameon,
        framealpha=config.legend.alpha,
    )

    logger.debug(
        "Legend applied: %s handle(s), loc='%s'",
        len(handles),
        config.legend.loc,
    )


def finalize_chart(
    fig: Figure,
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

    # Logs explicit overrides only (config-based defaults are not tracked here)
    applied = []
    if tick_format or tick_freq:
        applied.append("ticks")
    if tick_rotation is not None:
        applied.append("rotation")
    if xlim or ylim:
        applied.append("limits")
    if xlabel or ylabel:
        applied.append("labels")
    if title:
        applied.append("title")
    if source:
        applied.append("footer")
    logger.debug("finalize_chart: overrides=[%s]", ", ".join(applied))
