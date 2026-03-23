from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...overlays import add_highlight
from .._helpers import prepare_render_context, resolve_color
from ..renderer import ChartRenderer

if TYPE_CHECKING:
    from ...overlays import HighlightMode

__all__ = ["plot_stem"]


@ChartRenderer.register_enhancer("stem")
def plot_stem(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs: Any,
) -> None:
    """Plot stem chart with automatic color cycling.

    ``ax.stem()`` does not accept ``color=`` or ``zorder=`` directly;
    colors are applied post-creation on the returned StemContainer.
    """
    ctx = prepare_render_context(y_data, kwargs)

    for i, col in enumerate(ctx.y_data.columns):
        c = resolve_color(ctx, i)

        container = ax.stem(x, ctx.y_data[col], label=str(col), **kwargs)

        container.stemlines.set_color(c)
        container.stemlines.set_zorder(ctx.zorder)
        container.markerline.set_color(c)
        container.markerline.set_zorder(ctx.zorder)
        container.baseline.set_color(ctx.config.colors.grid)
        container.baseline.set_zorder(ctx.zorder - 1)

    if highlight and ctx.y_data.shape[1] == 1:
        col = ctx.y_data.columns[0]
        c = resolve_color(ctx, 0)
        add_highlight(ax, ctx.y_data[col], style="line", color=c, modes=highlight)
