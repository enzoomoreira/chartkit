from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ..._internal.collision import register_passive
from .._helpers import prepare_render_context, resolve_color
from ..renderer import ChartRenderer

if TYPE_CHECKING:
    from ...overlays import HighlightMode

__all__ = ["plot_stackplot"]


@ChartRenderer.register_enhancer("stackplot")
def plot_stackplot(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs: Any,
) -> None:
    """Plot stacked area chart using ``ax.stackplot()``.

    ``ax.stackplot(x, *ys, labels=, colors=)`` requires all series at
    once for correct stacking. Each DataFrame column becomes a layer.
    """
    ctx = prepare_render_context(y_data, kwargs)

    cols = ctx.y_data.columns.tolist()
    arrays = [ctx.y_data[col].fillna(0).values for col in cols]
    c = [resolve_color(ctx, i) for i in range(len(cols))]
    labels = [str(col) for col in cols]

    polys = ax.stackplot(
        x, *arrays, colors=c, labels=labels, zorder=ctx.zorder, **kwargs
    )
    for poly in polys:
        register_passive(ax, poly)
