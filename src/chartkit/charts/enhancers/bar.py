from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from ...exceptions import ValidationError
from ...overlays import add_highlight
from .._helpers import (
    apply_y_origin,
    compute_bar_offsets,
    detect_bar_width,
    is_categorical_index,
    prepare_categorical_axis,
    prepare_render_context,
    resolve_color,
    validate_y_origin,
)
from ..renderer import ChartRenderer

if TYPE_CHECKING:
    from ...overlays import HighlightMode

__all__ = ["plot_bar", "plot_barh"]

_VALID_SORT = {None, "ascending", "descending"}


@ChartRenderer.register_enhancer("bar")
def plot_bar(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    y_origin: Literal["zero", "auto"] = "zero",
    **kwargs,
) -> None:
    """Plot bar chart with automatic width based on frequency.

    Args:
        y_origin: ``'zero'`` includes zero in the Y axis (default),
            ``'auto'`` adjusts limits to focus on data with margin.

    Keyword Args:
        sort: ``None``, ``'ascending'`` or ``'descending'``. Single-column only.
        color: Explicit color or ``'cycle'`` to cycle theme colors per bar.
            ``'cycle'`` is single-column only.
    """
    y_origin = validate_y_origin(y_origin)
    sort = kwargs.pop("sort", None)
    multi_col = isinstance(y_data, pd.DataFrame) and y_data.shape[1] > 1
    ctx = prepare_render_context(y_data, kwargs)
    bars = ctx.config.bars

    if sort not in _VALID_SORT:
        raise ValidationError(
            f"sort must be None, 'ascending' or 'descending', got: {sort!r}"
        )
    if sort is not None and multi_col:
        raise ValidationError("sort is not supported for multi-column bar charts")
    if ctx.user_color == "cycle" and multi_col:
        raise ValidationError(
            "color='cycle' is not supported for multi-column bar charts"
        )

    if multi_col:
        if len(ctx.y_data) > bars.warning_threshold:
            logger.warning(
                "Bar chart with {} points may be hard to read. Consider kind='line'.",
                len(ctx.y_data),
            )

        categorical = is_categorical_index(x)

        if categorical:
            x_numeric = prepare_categorical_axis(ax, x)
            group_width = bars.width_default
        else:
            x_numeric = x
            group_width = detect_bar_width(x, bars)

        n_cols = len(ctx.y_data.columns)
        bar_width, offsets = compute_bar_offsets(n_cols, group_width)
        is_datetime = not categorical and pd.api.types.is_datetime64_any_dtype(x)

        for i, col in enumerate(ctx.y_data.columns):
            c = resolve_color(ctx, i)
            offset = offsets[i]
            if is_datetime:
                x_pos = x + pd.Timedelta(days=offset)
            else:
                x_pos = x_numeric + offset
            ax.bar(
                x_pos,
                ctx.y_data[col],
                width=bar_width,
                color=c,
                label=str(col),
                zorder=ctx.zorder,
                **kwargs,
            )

        all_vals = ctx.y_data.stack().dropna()
    else:
        vals = y_data if isinstance(y_data, pd.Series) else y_data.iloc[:, 0]

        if len(vals) > bars.warning_threshold:
            logger.warning(
                "Bar chart with {} points may be hard to read. Consider kind='line'.",
                len(vals),
            )

        if sort is not None:
            ascending = sort == "ascending"
            vals = vals.sort_values(ascending=ascending)
            x = vals.index

        if ctx.user_color == "cycle":
            c = [ctx.colors[i % len(ctx.colors)] for i in range(len(vals))]
        else:
            c = resolve_color(ctx, 0)

        width = detect_bar_width(x, bars)
        label = str(vals.name) if vals.name is not None else None
        ax.bar(
            x,
            vals,
            width=width,
            color=c,
            label=label,
            zorder=ctx.zorder,
            **kwargs,
        )

        all_vals = vals

    apply_y_origin(ax, y_origin, all_vals, bars.auto_margin)

    if highlight and not multi_col:
        highlight_color = ctx.config.colors.text if ctx.user_color == "cycle" else c
        add_highlight(
            ax, vals, style="bar", color=highlight_color, x=x, modes=highlight
        )


@ChartRenderer.register_enhancer("barh")
def plot_barh(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    y_origin: Literal["zero", "auto"] = "zero",
    **kwargs,
) -> None:
    """Plot horizontal bar chart with automatic height based on frequency.

    Semantics are inverted vs ``bar``: the Y axis holds categories/positions,
    the X axis holds values. ``y_origin`` controls the X-axis origin.

    Keyword Args:
        sort: ``None``, ``'ascending'`` or ``'descending'``. Single-column only.
        color: Explicit color or ``'cycle'`` to cycle theme colors per bar.
    """
    y_origin = validate_y_origin(y_origin)
    sort = kwargs.pop("sort", None)
    multi_col = isinstance(y_data, pd.DataFrame) and y_data.shape[1] > 1
    ctx = prepare_render_context(y_data, kwargs)
    bars = ctx.config.bars

    if sort not in _VALID_SORT:
        raise ValidationError(
            f"sort must be None, 'ascending' or 'descending', got: {sort!r}"
        )
    if sort is not None and multi_col:
        raise ValidationError("sort is not supported for multi-column barh charts")
    if ctx.user_color == "cycle" and multi_col:
        raise ValidationError(
            "color='cycle' is not supported for multi-column barh charts"
        )

    if multi_col:
        categorical = is_categorical_index(x)

        if categorical:
            y_numeric = prepare_categorical_axis(ax, x, axis="y")
            group_height = bars.width_default
        else:
            y_numeric = np.arange(len(x))
            ax.set_yticks(y_numeric)
            ax.set_yticklabels(list(x))
            group_height = bars.width_default

        n_cols = len(ctx.y_data.columns)
        bar_height, offsets = compute_bar_offsets(n_cols, group_height)

        for i, col in enumerate(ctx.y_data.columns):
            c = resolve_color(ctx, i)
            ax.barh(
                y_numeric + offsets[i],
                ctx.y_data[col],
                height=bar_height,
                color=c,
                label=str(col),
                zorder=ctx.zorder,
                **kwargs,
            )
        all_vals = ctx.y_data.stack().dropna()
    else:
        vals = y_data if isinstance(y_data, pd.Series) else y_data.iloc[:, 0]

        if sort is not None:
            ascending = sort == "ascending"
            vals = vals.sort_values(ascending=ascending)
            x = vals.index

        if ctx.user_color == "cycle":
            c = [ctx.colors[i % len(ctx.colors)] for i in range(len(vals))]
        else:
            c = resolve_color(ctx, 0)

        label = str(vals.name) if vals.name is not None else None
        ax.barh(
            range(len(vals)),
            vals,
            height=bars.width_default,
            color=c,
            label=label,
            zorder=ctx.zorder,
            **kwargs,
        )
        ax.set_yticks(range(len(vals)))
        ax.set_yticklabels(list(x))

        all_vals = vals

    apply_y_origin(ax, y_origin, all_vals, bars.auto_margin, axis="x")

    if highlight:
        logger.debug("barh: highlight not supported for horizontal bars, skipping")
