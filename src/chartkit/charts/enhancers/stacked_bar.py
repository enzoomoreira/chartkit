"""Stacked bar chart, for showing the composition of a total over time."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import pandas as pd
from matplotlib.axes import Axes

from ...overlays import add_highlight
from ...styling.theme import theme
from ...warnings import RenderingWarning, warn
from .._helpers import (
    apply_y_origin,
    detect_bar_width,
    is_categorical_index,
    prepare_categorical_axis,
    prepare_render_context,
    resolve_color,
    validate_y_origin,
)
from ..renderer import ChartRenderer

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ...overlays import HighlightMode

__all__ = ["plot_stacked_bar"]


@ChartRenderer.register_enhancer("stacked_bar")
def plot_stacked_bar(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    y_origin: Literal["zero", "auto"] = "zero",
    **kwargs: Any,
) -> None:
    """Plot stacked bar chart for composition.

    Each DataFrame column becomes a layer in the stack, with colors from the palette.
    A single Series behaves identically to a normal bar chart.

    Args:
        y_origin: ``'zero'`` includes zero in the Y axis (default),
            ``'auto'`` adjusts limits to focus on data with margin.

    Keyword Args:
        width: Overrides the measured width -- in days on a date axis, in
            index units on a categorical one.
    """
    y_origin = validate_y_origin(y_origin)
    user_width = kwargs.pop("width", None)
    ctx = prepare_render_context(y_data, kwargs)
    bars = ctx.config.bars

    if len(ctx.y_data) > bars.warning_threshold:
        warn(
            f"Stacked bar with {len(ctx.y_data)} points may be hard to read. "
            f"Consider kind='line'.",
            RenderingWarning,
        )

    categorical = is_categorical_index(x)
    x_plot = prepare_categorical_axis(ax, x) if categorical else x
    width = user_width if user_width is not None else detect_bar_width(x, bars)

    bottom = np.zeros(len(ctx.y_data))
    for i, col in enumerate(ctx.y_data.columns):
        c = resolve_color(ctx, i)
        vals = ctx.y_data[col].fillna(0)

        ax.bar(
            x_plot,
            vals,
            width=width,
            bottom=bottom,
            color=c,
            label=str(col),
            zorder=ctx.zorder,
            **kwargs,
        )
        bottom = bottom + vals.values

    total = ctx.y_data.sum(axis=1)
    apply_y_origin(ax, y_origin, total, bars.auto_margin)

    if highlight:
        color = (
            resolve_color(ctx, 0)
            if ctx.user_color is not None
            else theme.colors.primary
        )
        add_highlight(ax, total, style="bar", color=color, x=x_plot, modes=highlight)
