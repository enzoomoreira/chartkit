"""Shared data extraction and legend logic for engine and compose."""

from __future__ import annotations

from typing import cast

import pandas as pd

__all__ = ["extract_plot_data", "should_show_legend"]


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
