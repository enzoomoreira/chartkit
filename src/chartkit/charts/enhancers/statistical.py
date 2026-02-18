from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...settings import get_config
from ...styling.theme import theme
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
    config = get_config()

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    user_color = kwargs.pop("color", None)
    kwargs.pop("zorder", None)
    colors = theme.colors.cycle()

    cols = y_data.columns.tolist()
    arrays = [y_data[col].dropna().values for col in cols]
    labels = [str(col) for col in cols]

    kwargs.setdefault("patch_artist", True)
    bp = ax.boxplot(
        arrays, tick_labels=labels, zorder=config.layout.zorder.data, **kwargs
    )

    if kwargs.get("patch_artist", True):
        for i, box in enumerate(bp["boxes"]):
            c = user_color if user_color is not None else colors[i % len(colors)]
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
    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    user_color = kwargs.pop("color", None)
    kwargs.pop("zorder", None)
    colors = theme.colors.cycle()

    cols = y_data.columns.tolist()
    arrays = [y_data[col].dropna().values for col in cols]
    labels = [str(col) for col in cols]

    vp = ax.violinplot(arrays, **kwargs)

    for i, body in enumerate(vp.get("bodies", [])):
        c = user_color if user_color is not None else colors[i % len(colors)]
        body.set_facecolor(c)
        body.set_edgecolor(c)
        body.set_alpha(0.7)

    positions = list(range(1, len(cols) + 1))
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
