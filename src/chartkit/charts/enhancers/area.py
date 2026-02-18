from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...overlays import add_highlight
from ...settings import get_config
from ...styling.theme import theme
from ..renderer import ChartRenderer

if TYPE_CHECKING:
    from ...overlays import HighlightMode

__all__ = ["plot_area"]


@ChartRenderer.register_enhancer("fill_between")
def plot_area(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs: Any,
) -> None:
    """Plot area chart via ``ax.fill_between()``.

    Each column fills from zero with a contour line on top for visual
    definition. For stacked areas use ``kind='stackplot'`` instead.
    """
    config = get_config()

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    user_color = kwargs.pop("color", None)
    user_zorder = kwargs.pop("zorder", None)
    alpha = kwargs.pop("alpha", 0.3)
    colors = theme.colors.cycle()
    zorder = user_zorder if user_zorder is not None else config.layout.zorder.data

    for i, col in enumerate(y_data.columns):
        c = user_color if user_color is not None else colors[i % len(colors)]
        ax.fill_between(
            x,
            0,
            y_data[col],
            alpha=alpha,
            color=c,
            label=str(col),
            zorder=zorder,
            **kwargs,
        )
        ax.plot(x, y_data[col], color=c, linewidth=1, zorder=zorder + 1)

    if highlight and y_data.shape[1] == 1:
        col = y_data.columns[0]
        c = user_color if user_color is not None else colors[0]
        add_highlight(ax, y_data[col], style="line", color=c, modes=highlight)
