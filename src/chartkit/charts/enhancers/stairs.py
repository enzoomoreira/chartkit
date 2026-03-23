from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...overlays import add_highlight
from .._helpers import prepare_render_context, resolve_color
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
    ctx = prepare_render_context(y_data, kwargs)

    for i, col in enumerate(ctx.y_data.columns):
        c = resolve_color(ctx, i)
        ax.stairs(
            ctx.y_data[col],
            color=c,
            label=str(col),
            zorder=ctx.zorder,
            **kwargs,
        )

    if highlight and ctx.y_data.shape[1] == 1:
        col = ctx.y_data.columns[0]
        c = resolve_color(ctx, 0)
        add_highlight(ax, ctx.y_data[col], style="line", color=c, modes=highlight)
