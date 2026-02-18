from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...overlays import add_highlight
from ...settings import get_config
from ...styling.theme import theme
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
    config = get_config()

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    user_color = kwargs.pop("color", None)
    user_zorder = kwargs.pop("zorder", None)
    colors = theme.colors.cycle()
    zorder = user_zorder if user_zorder is not None else config.layout.zorder.data

    for i, col in enumerate(y_data.columns):
        c = user_color if user_color is not None else colors[i % len(colors)]

        container = ax.stem(x, y_data[col], label=str(col), **kwargs)

        container.stemlines.set_color(c)
        container.stemlines.set_zorder(zorder)
        container.markerline.set_color(c)
        container.markerline.set_zorder(zorder)
        container.baseline.set_color(config.colors.grid)
        container.baseline.set_zorder(zorder - 1)

    if highlight and y_data.shape[1] == 1:
        col = y_data.columns[0]
        c = user_color if user_color is not None else colors[0]
        add_highlight(ax, y_data[col], style="line", color=c, modes=highlight)
