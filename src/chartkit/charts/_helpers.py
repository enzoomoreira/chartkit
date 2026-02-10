"""Helpers internos compartilhados entre chart types."""

from typing import cast

import pandas as pd

from ..settings.schema import BarsConfig

__all__ = ["detect_bar_width"]


def detect_bar_width(x: pd.Index | pd.Series, bars: BarsConfig) -> float:
    """Largura automatica de barras baseada na frequencia dos dados."""
    width: float = bars.width_default
    if pd.api.types.is_datetime64_any_dtype(x):
        if len(x) > 1:
            span = cast(pd.Timestamp, x.max()) - cast(pd.Timestamp, x.min())
            avg_diff = span / (len(x) - 1)
            if avg_diff.days > bars.frequency_detection.annual_threshold:
                width = float(bars.width_annual)
            elif avg_diff.days > bars.frequency_detection.monthly_threshold:
                width = float(bars.width_monthly)
    return width
