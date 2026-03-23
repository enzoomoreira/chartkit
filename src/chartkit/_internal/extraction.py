"""Shared data extraction and legend logic for engine and compose."""

from __future__ import annotations

from typing import cast

import pandas as pd
from loguru import logger

from ..exceptions import ValidationError

__all__ = [
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

    Raises:
        ValidationError: If the DataFrame has no columns or the requested
            column does not exist.
    """
    if isinstance(y_data, pd.DataFrame):
        if y_data.columns.empty:
            raise ValidationError(
                "Cannot resolve series from empty DataFrame (no columns)"
            )
        col = series if series is not None else y_data.columns[0]
        if col not in y_data.columns:
            raise ValidationError(
                f"Series '{col}' not found. Available: {list(y_data.columns)}"
            )
        return y_data[col]
    return y_data


def extract_plot_data(
    df: pd.DataFrame,
    x: str | None,
    y: str | list[str] | None,
) -> tuple[pd.Index | pd.Series, pd.Series | pd.DataFrame]:
    """Extract x and y data from a DataFrame for plotting.

    Raises:
        ValidationError: If requested columns are missing or no numeric
            columns exist when ``y`` is None.
    """
    if x is not None and x not in df.columns:
        raise ValidationError(
            f"Column '{x}' not found in DataFrame. Available: {list(df.columns)}"
        )
    x_data: pd.Index | pd.Series = df.index if x is None else cast(pd.Series, df[x])

    if y is None:
        y_data = df.select_dtypes(include=["number"])
        if y_data.empty:
            raise ValidationError(
                "No numeric columns found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )
    else:
        cols = y if isinstance(y, list) else [y]
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValidationError(
                f"Column(s) not found: {missing}. Available: {list(df.columns)}"
            )
        y_data = df[y]

    logger.debug(
        "extract_plot_data: x={}, y_columns={}, rows={}",
        "index" if x is None else x,
        list(y_data.columns) if isinstance(y_data, pd.DataFrame) else [y_data.name],
        len(df),
    )

    return x_data, y_data


def should_show_legend(labels: list[str], legend: bool | None) -> bool:
    if legend is None:
        return len(labels) > 1
    return legend
