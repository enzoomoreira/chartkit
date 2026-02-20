from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from .._helpers import prepare_render_context, resolve_color
from ..renderer import ChartRenderer

if TYPE_CHECKING:
    from ...overlays import HighlightMode

__all__ = ["plot_boxplot", "plot_violinplot"]


@ChartRenderer.register_enhancer("boxplot")
def plot_boxplot(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs: Any,
) -> None:
    """Plot box-and-whisker chart using ``ax.boxplot()``.

    Each column becomes a box. ``patch_artist=True`` is forced to enable
    face coloring.
    """
    ctx = prepare_render_context(y_data, kwargs)

    cols = ctx.y_data.columns.tolist()
    arrays = [ctx.y_data[col].dropna().values for col in cols]
    labels = [str(col) for col in cols]

    kwargs.setdefault("patch_artist", True)
    bp = ax.boxplot(arrays, tick_labels=labels, zorder=ctx.zorder, **kwargs)

    if kwargs.get("patch_artist", True):
        for i, box in enumerate(bp["boxes"]):
            c = resolve_color(ctx, i)
            box.set_facecolor(c)


@ChartRenderer.register_enhancer("violinplot")
def plot_violinplot(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs: Any,
) -> None:
    """Plot violin chart using ``ax.violinplot()``.

    Each column becomes a violin body. Colors are applied post-creation
    via ``set_facecolor()`` / ``set_edgecolor()``.
    """
    ctx = prepare_render_context(y_data, kwargs)

    cols = ctx.y_data.columns.tolist()
    arrays = [ctx.y_data[col].dropna().values for col in cols]
    labels = [str(col) for col in cols]

    vp = ax.violinplot(arrays, **kwargs)

    for i, body in enumerate(vp.get("bodies", [])):
        c = resolve_color(ctx, i)
        body.set_facecolor(c)
        body.set_edgecolor(c)
        body.set_alpha(0.7)
        body.set_zorder(ctx.zorder)

    positions = list(range(1, len(cols) + 1))
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
