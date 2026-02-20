from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
from matplotlib.axes import Axes

from ...exceptions import ValidationError
from .._helpers import prepare_render_context, resolve_color
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
    as slice labels. Colors come from the theme palette (or user override).

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

    ctx = prepare_render_context(y_data, kwargs)
    c = [resolve_color(ctx, i) for i in range(len(vals))]
    labels = [str(label) for label in x]

    ax.pie(vals, labels=labels, colors=c, **kwargs)
    ax.set_aspect("equal")
