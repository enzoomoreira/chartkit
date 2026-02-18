from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...settings import get_config
from ...styling.theme import theme
from ..renderer import ChartRenderer

if TYPE_CHECKING:
    from ...overlays import HighlightMode

__all__ = ["plot_hist"]


@ChartRenderer.register_enhancer("hist")
def plot_hist(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs: Any,
) -> None:
    """Plot histogram with automatic color cycling.

    ``ax.hist(x)`` receives raw data for binning, not ``(x, y)`` pairs.
    Multi-column data is passed as a list of arrays to align bins.
    """
    config = get_config()

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    user_color = kwargs.pop("color", None)
    user_zorder = kwargs.pop("zorder", None)
    stacked = kwargs.pop("stacked", False)
    colors = theme.colors.cycle()
    zorder = user_zorder if user_zorder is not None else config.layout.zorder.data

    cols = y_data.columns.tolist()
    multi_col = len(cols) > 1

    if multi_col or stacked:
        arrays = [y_data[col].dropna().values for col in cols]
        c = (
            [user_color] * len(cols)
            if user_color is not None
            else [colors[i % len(colors)] for i in range(len(cols))]
        )
        labels = [str(col) for col in cols]
        ax.hist(
            arrays,
            color=c,
            label=labels,
            zorder=zorder,
            stacked=stacked,
            **kwargs,
        )
    else:
        col = cols[0]
        c = user_color if user_color is not None else colors[0]
        ax.hist(
            y_data[col].dropna(),
            color=c,
            label=str(col),
            zorder=zorder,
            **kwargs,
        )
