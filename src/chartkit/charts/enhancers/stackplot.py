from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...settings import get_config
from ...styling.theme import theme
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
    config = get_config()

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    user_color = kwargs.pop("color", None)
    user_zorder = kwargs.pop("zorder", None)
    colors = theme.colors.cycle()
    zorder = user_zorder if user_zorder is not None else config.layout.zorder.data

    cols = y_data.columns.tolist()
    arrays = [y_data[col].fillna(0).values for col in cols]
    c = (
        [user_color] * len(cols)
        if user_color is not None
        else [colors[i % len(colors)] for i in range(len(cols))]
    )
    labels = [str(col) for col in cols]

    ax.stackplot(x, *arrays, colors=c, labels=labels, zorder=zorder, **kwargs)
