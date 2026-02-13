"""Shared data extraction and legend logic for engine and compose."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pandas as pd

if TYPE_CHECKING:
    from matplotlib.axes import Axes

__all__ = [
    "add_right_margin",
    "extract_plot_data",
    "resolve_series",
    "should_show_legend",
]


def resolve_series(
    y_data: pd.Series | pd.DataFrame,
    series: str | None,
) -> pd.Series:
    """Resolve a single Series from y_data.

    If y_data is a DataFrame, selects the column named ``series``
    (or the first column if ``series`` is None).
    """
    if isinstance(y_data, pd.DataFrame):
        col = series if series is not None else y_data.columns[0]
        return y_data[col]
    return y_data


def extract_plot_data(
    df: pd.DataFrame,
    x: str | None,
    y: str | list[str] | None,
) -> tuple[pd.Index | pd.Series, pd.Series | pd.DataFrame]:
    x_data: pd.Index | pd.Series = df.index if x is None else cast(pd.Series, df[x])
    if y is None:
        y_data = df.select_dtypes(include=["number"])
    else:
        y_data = df[y]
    return x_data, y_data


def should_show_legend(labels: list[str], legend: bool | None) -> bool:
    if legend is None:
        return len(labels) > 1
    return legend


def add_right_margin(
    ax_left: Axes, ax_right: Axes | None, fraction: float = 0.06
) -> None:
    """Expand X limits to give room for highlight labels at the right edge."""
    x0, x1 = ax_left.get_xlim()
    pad = (x1 - x0) * fraction
    ax_left.set_xlim(x0, x1 + pad)
    if ax_right is not None:
        ax_right.set_xlim(x0, x1 + pad)
