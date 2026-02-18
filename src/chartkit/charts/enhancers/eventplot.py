from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...settings import get_config
from ...styling.theme import theme
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
    config = get_config()

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    user_color = kwargs.pop("color", None)
    user_zorder = kwargs.pop("zorder", None)
    colors = theme.colors.cycle()
    zorder = user_zorder if user_zorder is not None else config.layout.zorder.data

    positions = [y_data[col].dropna().values for col in y_data.columns]
    c = (
        [user_color] * len(y_data.columns)
        if user_color is not None
        else [colors[i % len(colors)] for i in range(len(y_data.columns))]
    )

    ax.eventplot(positions, colors=c, zorder=zorder, **kwargs)
