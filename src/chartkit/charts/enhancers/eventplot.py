from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from .._helpers import prepare_render_context, resolve_color
from ..renderer import ChartRenderer

if TYPE_CHECKING:
    from ...overlays import HighlightMode

__all__ = ["plot_eventplot"]


@ChartRenderer.register_enhancer("eventplot")
def plot_eventplot(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs: Any,
) -> None:
    """Plot event positions using ``ax.eventplot()``.

    ``ax.eventplot(positions)`` receives arrays of event positions.
    Each column becomes a separate row of events.
    """
    ctx = prepare_render_context(y_data, kwargs)

    positions = [ctx.y_data[col].dropna().values for col in ctx.y_data.columns]
    c = [resolve_color(ctx, i) for i in range(len(ctx.y_data.columns))]

    ax.eventplot(positions, colors=c, zorder=ctx.zorder, **kwargs)
