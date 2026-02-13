"""Internal helpers shared between chart types."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Literal, cast

import numpy as np
import pandas as pd

from ..exceptions import ValidationError
from ..settings.schema import BarsConfig

if TYPE_CHECKING:
    from matplotlib.axes import Axes

__all__ = [
    "apply_y_origin",
    "detect_bar_width",
    "is_categorical_index",
    "prepare_categorical_axis",
    "validate_y_origin",
]


def is_categorical_index(x: pd.Index | pd.Series) -> bool:
    """Return True for string/categorical indices (non-temporal, non-numeric)."""
    idx = pd.Index(x)
    if pd.api.types.is_datetime64_any_dtype(idx) or pd.api.types.is_numeric_dtype(idx):
        return False
    if isinstance(idx.dtype, pd.CategoricalDtype) or isinstance(
        idx.dtype, pd.StringDtype
    ):
        return True
    if idx.dtype == "object":
        non_null = [v for v in idx if v is not None and not pd.isna(v)]
        return all(isinstance(v, str) for v in non_null)
    return False


def prepare_categorical_axis(
    ax: Axes,
    x: pd.Index | pd.Series,
) -> np.ndarray:
    """Convert categorical index to numeric positions and set tick labels.

    Returns the numeric x positions (np.arange). Caller should use these
    instead of the original x for plotting.
    """
    x_numeric = np.arange(len(x))
    ax.set_xticks(x_numeric)
    ax.set_xticklabels(list(x))
    return x_numeric


def validate_y_origin(y_origin: str) -> Literal["zero", "auto"]:
    if y_origin not in ("zero", "auto"):
        raise ValidationError(f"y_origin must be 'zero' or 'auto', got: {y_origin!r}")
    return y_origin  # type: ignore[return-value]


def apply_y_origin(
    ax: Axes,
    y_origin: Literal["zero", "auto"],
    values: pd.Series,
    auto_margin: float,
) -> None:
    """Apply y_origin logic to the axes.

    Args:
        values: Flat series of all relevant data values (e.g. stacked totals
            or raw bar values).
        auto_margin: Fractional margin for ``'auto'`` mode (from BarsConfig).
    """
    if y_origin == "auto":
        clean = values.dropna()
        if not clean.empty:
            ymin, ymax = clean.min(), clean.max()
            margin = (ymax - ymin) * auto_margin
            ax.set_ylim(ymin - margin, ymax + margin)
    else:
        ymin, ymax = ax.get_ylim()
        if ymin > 0:
            ax.set_ylim(0, ymax)
        elif ymax < 0:
            ax.set_ylim(ymin, 0)


def _coerce_datetime_index(x: pd.Index | pd.Series) -> pd.DatetimeIndex | None:
    """Best-effort conversion to DatetimeIndex for frequency detection."""
    idx = pd.Index(x)
    if pd.api.types.is_datetime64_any_dtype(idx):
        return pd.DatetimeIndex(idx)

    if is_categorical_index(idx):
        return None

    if idx.dtype == "object":
        has_datetime_like = any(
            isinstance(v, (pd.Timestamp, datetime, date, np.datetime64))
            for v in idx
            if v is not None and not pd.isna(v)
        )
        if not has_datetime_like:
            return None

    parsed = pd.to_datetime(idx, errors="coerce")
    valid = parsed[~parsed.isna()]
    if len(valid) < 2:
        return None
    return pd.DatetimeIndex(valid)


def detect_bar_width(x: pd.Index | pd.Series, bars: BarsConfig) -> float:
    """Automatic bar width based on data frequency."""
    width: float = bars.width_default
    dt_index = _coerce_datetime_index(x)
    if dt_index is not None and len(dt_index) > 1:
        span = cast(pd.Timestamp, dt_index.max()) - cast(pd.Timestamp, dt_index.min())
        avg_diff = span / (len(dt_index) - 1)
        if avg_diff.days > bars.frequency_detection.annual_threshold:
            width = float(bars.width_annual)
        elif avg_diff.days > bars.frequency_detection.monthly_threshold:
            width = float(bars.width_monthly)
    return width
