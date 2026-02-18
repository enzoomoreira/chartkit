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

__all__ = ["plot_stairs"]


@ChartRenderer.register_enhancer("stairs")
def plot_stairs(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs: Any,
) -> None:
    """Plot step-function chart using ``ax.stairs()``.

    ``ax.stairs(values, edges)`` expects values (heights) as the first
    positional arg. Without explicit edges matplotlib auto-generates
    ``range(len(values) + 1)``.
    """
    config = get_config()

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    user_color = kwargs.pop("color", None)
    user_zorder = kwargs.pop("zorder", None)
    colors = theme.colors.cycle()
    zorder = user_zorder if user_zorder is not None else config.layout.zorder.data

    for i, col in enumerate(y_data.columns):
        c = user_color if user_color is not None else colors[i % len(colors)]
        ax.stairs(
            y_data[col],
            color=c,
            label=str(col),
            zorder=zorder,
            **kwargs,
        )

    if highlight and y_data.shape[1] == 1:
        col = y_data.columns[0]
        c = user_color if user_color is not None else colors[0]
        add_highlight(ax, y_data[col], style="line", color=c, modes=highlight)
