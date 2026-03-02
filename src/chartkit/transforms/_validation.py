"""Validation, coercion and frequency resolution for transforms.

Internal module -- not part of the public API.
"""

from __future__ import annotations

from typing import Literal

__all__ = [
    "coerce_input",
    "resolve_periods",
    "sanitize_result",
    "validate_numeric",
    "validate_params",
    "_DespikeParams",
]


import numpy as np
import pandas as pd
from loguru import logger
from pydantic import BaseModel, PositiveInt, ValidationError, model_validator

from .._internal.frequency import FREQ_ALIASES, infer_freq, normalize_freq_code
from ..exceptions import TransformError

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

FreqLiteral = Literal[
    "D",
    "B",
    "W",
    "M",
    "Q",
    "Y",
    "BME",
    "BMS",
    "daily",
    "business",
    "weekly",
    "monthly",
    "quarterly",
    "yearly",
    "annual",
]

TransformName = Literal["month", "year", "accum", "annualize"]

# ---------------------------------------------------------------------------
# Frequency -> periods mapping constants
# ---------------------------------------------------------------------------

# Mapping of normalized freq code -> periods per transform type.
# Codes here are those returned by pd.infer_freq() or normalized via FREQ_ALIASES.
FREQ_PERIODS_MAP: dict[str, dict[TransformName, int]] = {
    "D": {"month": 30, "year": 365, "accum": 365, "annualize": 365},
    "B": {"month": 21, "year": 252, "accum": 252, "annualize": 252},
    "W": {"month": 4, "year": 52, "accum": 52, "annualize": 52},
    "ME": {"month": 1, "year": 12, "accum": 12, "annualize": 12},
    "MS": {"month": 1, "year": 12, "accum": 12, "annualize": 12},
    "BME": {"month": 1, "year": 12, "accum": 12, "annualize": 12},
    "BMS": {"month": 1, "year": 12, "accum": 12, "annualize": 12},
    "QE": {"month": 1, "year": 4, "accum": 4, "annualize": 4},
    "QS": {"month": 1, "year": 4, "accum": 4, "annualize": 4},
    "BQE": {"month": 1, "year": 4, "accum": 4, "annualize": 4},
    "BQS": {"month": 1, "year": 4, "accum": 4, "annualize": 4},
    "YE": {"month": 1, "year": 1, "accum": 1, "annualize": 1},
    "YS": {"month": 1, "year": 1, "accum": 1, "annualize": 1},
    "BYE": {"month": 1, "year": 1, "accum": 1, "annualize": 1},
    "BYS": {"month": 1, "year": 1, "accum": 1, "annualize": 1},
}


# ---------------------------------------------------------------------------
# Pydantic models for parameter validation
# ---------------------------------------------------------------------------


class _FreqResolvedParams(BaseModel):
    """Validation for transforms that resolve periods via frequency (variation, annualize)."""

    periods: PositiveInt | None = None
    freq: FreqLiteral | None = None

    @model_validator(mode="after")
    def _periods_xor_freq(self) -> _FreqResolvedParams:
        if self.periods is not None and self.freq is not None:
            raise ValueError("Cannot specify both 'periods' and 'freq'")
        return self


class _RollingParams(BaseModel):
    """Validation for accum."""

    window: PositiveInt | None = None
    freq: FreqLiteral | None = None

    @model_validator(mode="after")
    def _window_xor_freq(self) -> _RollingParams:
        if self.window is not None and self.freq is not None:
            raise ValueError("Cannot specify both 'window' and 'freq'")
        return self


class _NormalizeParams(BaseModel):
    """Validation for normalize."""

    base: PositiveInt | None = None
    base_date: str | None = None


class _DiffParams(BaseModel):
    """Validation for diff."""

    periods: int

    @model_validator(mode="after")
    def _nonzero(self) -> _DiffParams:
        if self.periods == 0:
            raise ValueError("'periods' must be non-zero (periods=0 returns all zeros)")
        return self


class _ZScoreParams(BaseModel):
    """Validation for zscore."""

    window: PositiveInt | None = None

    @model_validator(mode="after")
    def _min_window(self) -> _ZScoreParams:
        if self.window is not None and self.window < 2:
            raise ValueError("'window' must be >= 2 (std of 1 value is undefined)")
        return self


class _DespikeParams(BaseModel):
    """Validation for despike."""

    window: PositiveInt = 21
    threshold: float = 5.0
    method: Literal["median", "interpolate"] = "median"

    @model_validator(mode="after")
    def _validate(self) -> _DespikeParams:
        if self.window < 3:
            raise ValueError("'window' must be >= 3 (need neighbors on both sides)")
        if self.window % 2 == 0:
            raise ValueError("'window' must be odd (centered rolling requires symmetric sides)")
        if self.threshold <= 0:
            raise ValueError("'threshold' must be positive")
        return self


# ---------------------------------------------------------------------------
# Parameter validation (pydantic wrapper -> TransformError)
# ---------------------------------------------------------------------------


def validate_params[T: BaseModel](model_class: type[T], **kwargs) -> T:
    """Validate scalar parameters via pydantic model.

    Catches ``ValidationError`` and re-raises as ``TransformError``
    with a clean message.
    """

    try:
        return model_class(**kwargs)
    except ValidationError as exc:
        errors = exc.errors()
        messages = [
            f"  {e['loc'][0]}: {e['msg']}" if e.get("loc") else f"  {e['msg']}"
            for e in errors
        ]
        raise TransformError(
            f"Invalid parameters for {model_class.__name__}:\n" + "\n".join(messages)
        ) from exc


# ---------------------------------------------------------------------------
# Input coercion
# ---------------------------------------------------------------------------


def coerce_input(data: object) -> pd.DataFrame | pd.Series:
    """Convert common inputs to DataFrame or Series.

    Accepts: DataFrame, Series, dict, list, np.ndarray.
    Raises ``TransformError`` for unsupported types.
    """
    if isinstance(data, (pd.DataFrame, pd.Series)):
        return data

    if isinstance(data, dict):
        try:
            return pd.DataFrame(data)
        except ValueError:
            return pd.Series(data)

    if isinstance(data, (list, np.ndarray)):
        arr = np.asarray(data)
        if arr.ndim == 1:
            return pd.Series(arr)
        if arr.ndim == 2:
            return pd.DataFrame(arr)
        raise TransformError(f"Arrays with {arr.ndim} dimensions are not supported")

    raise TransformError(
        f"Expected DataFrame, Series, dict, list, or ndarray. Got {type(data).__name__}"
    )


# ---------------------------------------------------------------------------
# Numeric validation
# ---------------------------------------------------------------------------


def validate_numeric(df: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Validate and filter data to contain only numeric columns.

    - DataFrame: filters non-numeric columns with warning, raises if none remain.
    - Series: raises if non-numeric.
    - Emits warning if index is not DatetimeIndex.
    """
    if df.empty:
        raise TransformError("Input data is empty")

    if isinstance(df, pd.Series):
        if not pd.api.types.is_numeric_dtype(df):
            raise TransformError(f"Series must be numeric, got dtype '{df.dtype}'")
        if not isinstance(df.index, pd.DatetimeIndex):
            logger.warning(
                "Series index is {} instead of DatetimeIndex. "
                "Frequency auto-detection will not work.",
                type(df.index).__name__,
            )
        return df

    # DataFrame
    non_numeric = df.select_dtypes(exclude="number").columns.tolist()
    if non_numeric:
        logger.warning(
            "Dropping non-numeric columns: {}",
            non_numeric,
        )
        df = df.select_dtypes(include="number")
        if df.empty:
            raise TransformError("No numeric columns remaining after filtering")

    if not isinstance(df.index, pd.DatetimeIndex):
        logger.warning(
            "DataFrame index is {} instead of DatetimeIndex. "
            "Frequency auto-detection will not work.",
            type(df.index).__name__,
        )

    return df


# ---------------------------------------------------------------------------
# Result sanitization
# ---------------------------------------------------------------------------


def sanitize_result(
    result: pd.DataFrame | pd.Series,
) -> pd.DataFrame | pd.Series:
    """Replace inf/-inf with NaN in the result."""
    return result.replace([np.inf, -np.inf], np.nan)


# ---------------------------------------------------------------------------
# Frequency -> periods resolution
# ---------------------------------------------------------------------------


def resolve_periods(
    df: pd.DataFrame | pd.Series,
    transform: TransformName,
    periods: int | None,
    freq: str | None,
) -> int:
    """Resolve the number of periods for a transform.

    Precedence: ``periods`` (explicit) > ``freq`` (explicit) >
    auto-detect via ``pd.infer_freq`` > ``ValueError``.

    Args:
        df: Input data (used for auto-detect).
        transform: Transform name ('month', 'year', 'accum', 'annualize').
        periods: Explicit periods passed by the user.
        freq: Explicit frequency passed by the user.

    Returns:
        Resolved number of periods.

    Raises:
        TransformError: If frequency cannot be resolved.
    """
    # 1. Explicit periods -> use directly
    if periods is not None:
        return periods

    # 2. Explicit freq -> lookup
    if freq is not None:
        normalized = normalize_freq_code(freq)
        mapping = FREQ_PERIODS_MAP.get(normalized)
        if mapping is None:
            raise TransformError(
                f"Unknown frequency '{freq}'. "
                f"Supported: {', '.join(sorted(FREQ_ALIASES.keys()))}"
            )
        return mapping[transform]

    # 3. Auto-detect
    detected = infer_freq(df)
    if detected is not None:
        mapping = FREQ_PERIODS_MAP.get(detected)
        if mapping is not None:
            logger.debug(
                "Auto-detected frequency '{}' for transform '{}'", detected, transform
            )
            return mapping[transform]
        # Detected frequency but it is not supported
        raise TransformError(
            f"Detected frequency '{detected}' is not supported. "
            f"Supported: {', '.join(sorted(FREQ_PERIODS_MAP.keys()))}. "
            f"Pass periods= explicitly."
        )

    # 4. Could not detect frequency
    raise TransformError(
        f"Cannot determine frequency for '{transform}'. "
        f"Pass freq= (e.g. 'M', 'D', 'B') or periods= explicitly."
    )
