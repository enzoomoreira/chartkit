from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...overlays import add_highlight
from .._helpers import RenderContext, prepare_render_context, resolve_color
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

    Behavior depends on the number of columns:
    - **1 column**: fills from zero to y (classic area chart).
    - **2 columns**: fills between the two series (spread / interval).
    - **3+ columns**: each column fills from zero independently.

    For stacked areas use ``kind='stackplot'`` instead.
    """
    ctx = prepare_render_context(y_data, kwargs)
    alpha = kwargs.pop("alpha", 0.3)

    if ctx.y_data.shape[1] == 2:
        _fill_between_pair(ax, x, ctx, alpha, **kwargs)
    else:
        _fill_from_zero(ax, x, ctx, alpha, **kwargs)

    if highlight and ctx.y_data.shape[1] == 1:
        col = ctx.y_data.columns[0]
        c = resolve_color(ctx, 0)
        add_highlight(ax, ctx.y_data[col], style="line", color=c, modes=highlight)


def _fill_between_pair(
    ax: Axes,
    x: pd.Index | pd.Series,
    ctx: RenderContext,
    alpha: float,
    **kwargs: Any,
) -> None:
    """Fill the area between two columns with contour lines on each."""
    col1, col2 = ctx.y_data.columns
    c = resolve_color(ctx, 0)

    ax.fill_between(
        x,
        ctx.y_data[col1],
        ctx.y_data[col2],
        alpha=alpha,
        color=c,
        zorder=ctx.zorder,
        **kwargs,
    )
    lw = ctx.config.lines.main_width
    ax.plot(
        x,
        ctx.y_data[col1],
        color=c,
        linewidth=lw,
        label=str(col1),
        zorder=ctx.zorder + 1,
    )

    c2 = resolve_color(ctx, 1)
    ax.plot(
        x,
        ctx.y_data[col2],
        color=c2,
        linewidth=lw,
        label=str(col2),
        zorder=ctx.zorder + 1,
    )


def _fill_from_zero(
    ax: Axes,
    x: pd.Index | pd.Series,
    ctx: RenderContext,
    alpha: float,
    **kwargs: Any,
) -> None:
    """Fill from zero to y for each column independently."""
    for i, col in enumerate(ctx.y_data.columns):
        c = resolve_color(ctx, i)
        ax.fill_between(
            x,
            0,
            ctx.y_data[col],
            alpha=alpha,
            color=c,
            label=str(col),
            zorder=ctx.zorder,
            **kwargs,
        )
        ax.plot(
            x,
            ctx.y_data[col],
            color=c,
            linewidth=ctx.config.lines.main_width,
            zorder=ctx.zorder + 1,
        )
