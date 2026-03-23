from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from .._helpers import prepare_render_context, resolve_color
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
    ctx = prepare_render_context(y_data, kwargs)

    for i, col in enumerate(ctx.y_data.columns):
        c = resolve_color(ctx, i)
        ax.ecdf(
            ctx.y_data[col].dropna(),
            color=c,
            label=str(col),
            zorder=ctx.zorder,
            **kwargs,
        )
