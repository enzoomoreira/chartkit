from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from .._internal.collision import register_line_obstacle
from ..overlays.markers import add_highlight
from ..settings import get_config
from ..styling.theme import theme
from .registry import ChartRegistry

if TYPE_CHECKING:
    from ..overlays.markers import HighlightMode

__all__ = ["plot_line"]


@ChartRegistry.register("line")
def plot_line(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs,
) -> None:
    """Plot time series as a line chart.

    If y_data is a DataFrame, each column becomes a series with a color from the palette.
    """
    config = get_config()
    lines = config.lines

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    logger.debug("plot_line: {} series, {} points", len(y_data.columns), len(y_data))

    user_color = kwargs.pop("color", None)
    user_linewidth = kwargs.pop("linewidth", None)
    user_zorder = kwargs.pop("zorder", None)

    colors = theme.colors.cycle()

    for i, col in enumerate(y_data.columns):
        c = user_color if user_color is not None else colors[i % len(colors)]

        ax.plot(
            x,
            y_data[col],
            linewidth=user_linewidth
            if user_linewidth is not None
            else lines.main_width,
            color=c,
            label=str(col),
            zorder=user_zorder
            if user_zorder is not None
            else config.layout.zorder.data,
            **kwargs,
        )

        register_line_obstacle(ax, ax.lines[-1])

        if highlight:
            add_highlight(
                ax, cast(pd.Series, y_data[col]), style="line", color=c, modes=highlight
            )
