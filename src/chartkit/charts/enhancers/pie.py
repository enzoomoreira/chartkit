from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...exceptions import ValidationError
from ...styling.theme import theme
from ..renderer import ChartRenderer

if TYPE_CHECKING:
    from ...overlays import HighlightMode

__all__ = ["plot_pie"]


@ChartRenderer.register_enhancer("pie")
def plot_pie(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs: Any,
) -> None:
    """Plot pie chart using ``ax.pie()``.

    Only single-column data is supported. The DataFrame index is used
    as slice labels. Colors come from the theme palette.

    Raises:
        ValidationError: If y_data has more than one column.
    """
    if isinstance(y_data, pd.DataFrame):
        if y_data.shape[1] > 1:
            raise ValidationError(
                "Pie chart supports only single-column data, "
                f"got {y_data.shape[1]} columns."
            )
        vals = y_data.iloc[:, 0]
    else:
        vals = y_data

    kwargs.pop("color", None)
    kwargs.pop("zorder", None)

    colors = theme.colors.cycle()
    n = len(vals)
    c = [colors[i % len(colors)] for i in range(n)]

    labels = [str(label) for label in x]

    ax.pie(vals, labels=labels, colors=c, **kwargs)
    ax.set_aspect("equal")
