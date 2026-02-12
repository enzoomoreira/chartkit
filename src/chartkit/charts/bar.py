from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from ..exceptions import ValidationError
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

__all__ = ["plot_bar"]

_VALID_SORT = {None, "ascending", "descending"}


@ChartRegistry.register("bar")
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

    config = get_config()
    bars = config.bars

    user_color = kwargs.pop("color", None)
    sort = kwargs.pop("sort", None)
    colors = theme.colors.cycle()

    multi_col = isinstance(y_data, pd.DataFrame) and y_data.shape[1] > 1

    if sort not in _VALID_SORT:
        raise ValidationError(
            f"sort must be None, 'ascending' or 'descending', got: {sort!r}"
        )
    if sort is not None and multi_col:
        raise ValidationError("sort is not supported for multi-column bar charts")
    if user_color == "cycle" and multi_col:
        raise ValidationError(
            "color='cycle' is not supported for multi-column bar charts"
        )

    if multi_col:
        if len(y_data) > bars.warning_threshold:
            logger.warning(
                "Bar chart with {} points may be hard to read. Consider kind='line'.",
                len(y_data),
            )

        categorical = is_categorical_index(x)

        if categorical:
            x_numeric = prepare_categorical_axis(ax, x)
            group_width = bars.width_default
        else:
            x_numeric = x
            group_width = detect_bar_width(x, bars)

        n_cols = len(y_data.columns)
        bar_width = group_width / n_cols
        is_datetime = not categorical and pd.api.types.is_datetime64_any_dtype(x)

        for i, col in enumerate(y_data.columns):
            c = user_color if user_color is not None else colors[i % len(colors)]
            offset = (i - n_cols / 2 + 0.5) * bar_width
            if is_datetime:
                x_pos = x + pd.Timedelta(days=offset)
            else:
                x_pos = x_numeric + offset
            ax.bar(
                x_pos,
                y_data[col],
                width=bar_width,
                color=c,
                label=str(col),
                zorder=config.layout.zorder.data,
                **kwargs,
            )

        all_vals = y_data.stack().dropna()
    else:
        vals = y_data.iloc[:, 0] if isinstance(y_data, pd.DataFrame) else y_data

        if len(vals) > bars.warning_threshold:
            logger.warning(
                "Bar chart with {} points may be hard to read. Consider kind='line'.",
                len(vals),
            )

        if sort is not None:
            ascending = sort == "ascending"
            vals = vals.sort_values(ascending=ascending)
            x = vals.index

        if user_color == "cycle":
            c = [colors[i % len(colors)] for i in range(len(vals))]
        else:
            c = user_color if user_color is not None else colors[0]

        width = detect_bar_width(x, bars)
        label = str(vals.name) if vals.name is not None else None
        ax.bar(
            x,
            vals,
            width=width,
            color=c,
            label=label,
            zorder=config.layout.zorder.data,
            **kwargs,
        )

        all_vals = vals

    apply_y_origin(ax, y_origin, all_vals, bars.auto_margin)

    if highlight and not multi_col:
        highlight_color = config.colors.text if user_color == "cycle" else c
        add_highlight(
            ax, vals, style="bar", color=highlight_color, x=x, modes=highlight
        )
