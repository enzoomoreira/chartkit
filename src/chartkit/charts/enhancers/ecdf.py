from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...settings import get_config
from ...styling.theme import theme
from ..renderer import ChartRenderer

if TYPE_CHECKING:
    from ...overlays import HighlightMode

__all__ = ["plot_ecdf"]


@ChartRenderer.register_enhancer("ecdf")
def plot_ecdf(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs: Any,
) -> None:
    """Plot empirical cumulative distribution function.

    ``ax.ecdf(x)`` takes a 1D array of data values; the X axis becomes
    data values and Y becomes cumulative probability. The DataFrame
    index is ignored.
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
        ax.ecdf(
            y_data[col].dropna(),
            color=c,
            label=str(col),
            zorder=zorder,
            **kwargs,
        )
