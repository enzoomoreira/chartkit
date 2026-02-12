from typing import Any

import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from .._internal.collision import register_fixed
from ..settings import get_config
from ..styling.theme import theme


def _add_stat_line(
    ax: Axes,
    y_data: pd.Series | pd.DataFrame,
    stat: str,
    default_color: str,
    default_label: str,
    color: str | None = None,
    linestyle: str | None = None,
    label: str | None = None,
    linewidth: float | None = None,
    series: str | None = None,
) -> None:
    """Add horizontal line at a statistic (max, min, mean) of the data."""
    config = get_config()

    if isinstance(y_data, pd.DataFrame):
        col = series if series is not None else y_data.columns[0]
        y_data = y_data[col]

    value = getattr(y_data, stat)()
    if pd.isna(value):
        logger.warning(
            "Stat '{}' returned NaN for series, skipping reference line", stat
        )
        return

    line = ax.axhline(
        y=value,
        color=color if color is not None else default_color,
        linestyle=linestyle if linestyle is not None else config.lines.reference_style,
        linewidth=linewidth if linewidth is not None else config.lines.overlay_width,
        label=label if label is not None else default_label,
        zorder=config.layout.zorder.reference_lines,
    )
    register_fixed(ax, line)


def add_ath_line(
    ax: Axes,
    y_data: pd.Series | pd.DataFrame,
    **kwargs: Any,
) -> None:
    """Add horizontal line at the All-Time High (maximum value)."""
    config = get_config()
    _add_stat_line(
        ax,
        y_data,
        stat="max",
        default_color=theme.colors.positive,
        default_label=config.labels.ath,
        **kwargs,
    )


def add_atl_line(
    ax: Axes,
    y_data: pd.Series | pd.DataFrame,
    **kwargs: Any,
) -> None:
    """Add horizontal line at the All-Time Low (minimum value)."""
    config = get_config()
    _add_stat_line(
        ax,
        y_data,
        stat="min",
        default_color=theme.colors.negative,
        default_label=config.labels.atl,
        **kwargs,
    )


def add_avg_line(
    ax: Axes,
    y_data: pd.Series | pd.DataFrame,
    **kwargs: Any,
) -> None:
    """Add horizontal line at the mean of the data."""
    config = get_config()
    _add_stat_line(
        ax,
        y_data,
        stat="mean",
        default_color=theme.colors.grid,
        default_label=config.labels.avg,
        **kwargs,
    )


def add_hline(
    ax: Axes,
    value: float,
    color: str | None = None,
    linestyle: str | None = None,
    label: str | None = None,
    linewidth: float | None = None,
) -> None:
    """Add horizontal line at an arbitrary value."""
    config = get_config()

    line = ax.axhline(
        y=value,
        color=color if color is not None else theme.colors.grid,
        linestyle=linestyle if linestyle is not None else config.lines.reference_style,
        linewidth=linewidth if linewidth is not None else config.lines.overlay_width,
        label=label,
        zorder=config.layout.zorder.reference_lines,
    )
    register_fixed(ax, line)


def add_target_line(
    ax: Axes,
    value: float,
    color: str | None = None,
    linestyle: str | None = None,
    label: str | None = None,
    linewidth: float | None = None,
) -> None:
    """Add horizontal target line with distinct styling.

    Semantically distinct from ``add_hline``: uses its own color (secondary),
    alternating dash pattern, and label with "Target:" prefix by default.
    """
    config = get_config()

    y_fmt = ax.yaxis.get_major_formatter()
    formatted_value = y_fmt(value, None)
    if not formatted_value:
        formatted_value = f"{value:g}"

    default_label = config.labels.target_format.format(value=formatted_value)

    line = ax.axhline(
        y=value,
        color=color if color is not None else theme.colors.secondary,
        linestyle=linestyle if linestyle is not None else config.lines.target_style,
        linewidth=linewidth if linewidth is not None else config.lines.overlay_width,
        label=label if label is not None else default_label,
        zorder=config.layout.zorder.reference_lines,
    )
    register_fixed(ax, line)
