from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from ..overlays.markers import add_highlight
from ..settings import get_config
from ..styling.theme import theme
from ._helpers import (
    apply_y_origin,
    detect_bar_width,
    is_categorical_index,
    prepare_categorical_axis,
    validate_y_origin,
)
from .registry import ChartRegistry

if TYPE_CHECKING:
    from ..overlays.markers import HighlightMode

__all__ = ["plot_stacked_bar"]


@ChartRegistry.register("stacked_bar")
def plot_stacked_bar(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    y_origin: Literal["zero", "auto"] = "zero",
    **kwargs,
) -> None:
    """Plot stacked bar chart for composition.

    Each DataFrame column becomes a layer in the stack, with colors from the palette.
    A single Series behaves identically to a normal bar chart.

    Args:
        y_origin: ``'zero'`` includes zero in the Y axis (default),
            ``'auto'`` adjusts limits to focus on data with margin.
    """
    y_origin = validate_y_origin(y_origin)

    config = get_config()
    bars = config.bars

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    if len(y_data) > bars.warning_threshold:
        logger.warning(
            "Stacked bar with {} points may be hard to read. Consider kind='line'.",
            len(y_data),
        )

    user_color = kwargs.pop("color", None)
    colors = theme.colors.cycle()

    categorical = is_categorical_index(x)
    if categorical:
        x_plot = np.arange(len(x))
        width = bars.width_default
    else:
        x_plot = x
        width = detect_bar_width(x, bars)

    bottom = np.zeros(len(y_data))
    for i, col in enumerate(y_data.columns):
        c = user_color if user_color is not None else colors[i % len(colors)]
        vals = y_data[col].fillna(0)

        ax.bar(
            x_plot,
            vals,
            width=width,
            bottom=bottom,
            color=c,
            label=str(col),
            zorder=config.layout.zorder.data,
            **kwargs,
        )
        bottom = bottom + vals.values

    if categorical:
        prepare_categorical_axis(ax, x)

    total = y_data.sum(axis=1)
    apply_y_origin(ax, y_origin, total, bars.auto_margin)

    if highlight:
        color = user_color if user_color is not None else theme.colors.primary
        add_highlight(ax, total, style="bar", color=color, x=x_plot, modes=highlight)
