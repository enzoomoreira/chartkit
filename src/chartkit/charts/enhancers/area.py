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
    config = get_config()

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    user_color = kwargs.pop("color", None)
    user_zorder = kwargs.pop("zorder", None)
    alpha = kwargs.pop("alpha", 0.3)
    colors = theme.colors.cycle()
    zorder = user_zorder if user_zorder is not None else config.layout.zorder.data

    if y_data.shape[1] == 2:
        _fill_between_pair(ax, x, y_data, alpha, user_color, colors, zorder, **kwargs)
    else:
        _fill_from_zero(ax, x, y_data, alpha, user_color, colors, zorder, **kwargs)

    if highlight and y_data.shape[1] == 1:
        col = y_data.columns[0]
        c = user_color if user_color is not None else colors[0]
        add_highlight(ax, y_data[col], style="line", color=c, modes=highlight)


def _fill_between_pair(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.DataFrame,
    alpha: float,
    user_color: str | None,
    colors: list[str],
    zorder: int,
    **kwargs: Any,
) -> None:
    """Fill the area between two columns with contour lines on each."""
    col1, col2 = y_data.columns
    c = user_color if user_color is not None else colors[0]

    ax.fill_between(
        x,
        y_data[col1],
        y_data[col2],
        alpha=alpha,
        color=c,
        zorder=zorder,
        **kwargs,
    )
    ax.plot(x, y_data[col1], color=c, linewidth=1, label=str(col1), zorder=zorder + 1)

    c2 = user_color if user_color is not None else colors[1 % len(colors)]
    ax.plot(x, y_data[col2], color=c2, linewidth=1, label=str(col2), zorder=zorder + 1)


def _fill_from_zero(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.DataFrame,
    alpha: float,
    user_color: str | None,
    colors: list[str],
    zorder: int,
    **kwargs: Any,
) -> None:
    """Fill from zero to y for each column independently."""
    for i, col in enumerate(y_data.columns):
        c = user_color if user_color is not None else colors[i % len(colors)]
        ax.fill_between(
            x,
            0,
            y_data[col],
            alpha=alpha,
            color=c,
            label=str(col),
            zorder=zorder,
            **kwargs,
        )
        ax.plot(x, y_data[col], color=c, linewidth=1, zorder=zorder + 1)
