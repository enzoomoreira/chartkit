from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from .._helpers import prepare_render_context, resolve_color
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
    stacked = kwargs.pop("stacked", False)
    ctx = prepare_render_context(y_data, kwargs)

    cols = ctx.y_data.columns.tolist()
    multi_col = len(cols) > 1

    if multi_col or stacked:
        arrays = [ctx.y_data[col].dropna().values for col in cols]
        c = [resolve_color(ctx, i) for i in range(len(cols))]
        labels = [str(col) for col in cols]
        ax.hist(
            arrays,
            color=c,
            label=labels,
            zorder=ctx.zorder,
            stacked=stacked,
            **kwargs,
        )
    else:
        col = cols[0]
        c = resolve_color(ctx, 0)
        ax.hist(
            ctx.y_data[col].dropna(),
            color=c,
            label=str(col),
            zorder=ctx.zorder,
            **kwargs,
        )
