"""Pure time series transforms.

All functions follow the contract:
- Accept DataFrame, Series, dict, list or ndarray (automatic coercion).
- Validate that data is numeric (warning + filtering for non-numeric).
- Guard against inf (replace with NaN in the result).
- Functions that depend on frequency (variation, accum, annualize)
  resolve periods via auto-detect or require explicit freq=/periods=.
"""

from __future__ import annotations

from typing import overload

import numpy as np
import pandas as pd
from loguru import logger

from ..exceptions import TransformError
from ..settings import get_config
from ._validation import (
    _DiffParams,
    _FreqResolvedParams,
    _NormalizeParams,
    _RollingParams,
    _ZScoreParams,
    _infer_freq,
    _normalize_freq_code,
    coerce_input,
    resolve_periods,
    sanitize_result,
    validate_numeric,
    validate_params,
)

__all__ = [
    "variation",
    "accum",
    "diff",
    "normalize",
    "annualize",
    "drawdown",
    "zscore",
    "to_month_end",
]


# ---------------------------------------------------------------------------
# variation -- percentage change by horizon
# ---------------------------------------------------------------------------

_VALID_HORIZONS = {"month", "year"}


@overload
def variation(
    df: pd.DataFrame,
    horizon: str = "month",
    periods: int | None = None,
    freq: str | None = None,
) -> pd.DataFrame: ...
@overload
def variation(
    df: pd.Series,
    horizon: str = "month",
    periods: int | None = None,
    freq: str | None = None,
) -> pd.Series: ...
def variation(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    horizon: str = "month",
    periods: int | None = None,
    freq: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Percentage change between periods.

    Calculates percentage change by comparing each point with a prior point,
    determined by ``horizon``. The number of comparison periods is resolved
    automatically based on the data frequency.

    Args:
        df: Input data.
        horizon: Comparison horizon (``'month'`` or ``'year'``).
            For monthly data, ``'month'`` compares with the previous month (periods=1)
            and ``'year'`` compares with the same month of the prior year (periods=12).
            For quarterly/annual data, ``'month'`` compares with the prior period
            (period-over-period).
        periods: Explicit override of the number of periods.
            Mutually exclusive with ``freq``.
        freq: Data frequency (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``, ``'Y'``).
            Mutually exclusive with ``periods``.
    """
    if horizon not in _VALID_HORIZONS:
        raise TransformError(
            f"Invalid horizon '{horizon}'. Use: {', '.join(sorted(_VALID_HORIZONS))}"
        )
    params = validate_params(_FreqResolvedParams, periods=periods, freq=freq)
    data = validate_numeric(coerce_input(df))
    resolved = resolve_periods(data, horizon, params.periods, params.freq)
    logger.debug("variation: horizon='{}', resolved_periods={}", horizon, resolved)

    # Warn when horizon='month' does not mean "calendar month"
    if horizon == "month" and resolved == 1 and params.periods is None:
        detected = (
            _infer_freq(data)
            if params.freq is None
            else _normalize_freq_code(params.freq)
        )
        if detected in ("QE", "QS", "YE", "YS"):
            logger.warning(
                "horizon='month' with {} data resolves to periods=1 "
                "(period-over-period, not calendar month-over-month)",
                detected,
            )

    result = data.pct_change(periods=resolved) * 100
    return sanitize_result(result)


# ---------------------------------------------------------------------------
# accum -- cumulative change in rolling window
# ---------------------------------------------------------------------------


@overload
def accum(
    df: pd.DataFrame, window: int | None = None, freq: str | None = None
) -> pd.DataFrame: ...
@overload
def accum(
    df: pd.Series, window: int | None = None, freq: str | None = None
) -> pd.Series: ...
def accum(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    window: int | None = None,
    freq: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Cumulative change via compound product in rolling window.

    Formula: ``(prod(1 + x/100) - 1) * 100`` over the window.

    The window is resolved by the following precedence:

    1. Explicit ``window=``
    2. Explicit ``freq=`` (resolved via mapping)
    3. Auto-detect via ``pd.infer_freq``
    4. Fallback to ``config.transforms.accum_window``

    Args:
        df: Input data (rates in percentage).
        window: Window size in number of periods.
            Mutually exclusive with ``freq``.
        freq: Data frequency (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``, ``'Y'``).
            Mutually exclusive with ``window``.
    """
    params = validate_params(_RollingParams, window=window, freq=freq)
    data = validate_numeric(coerce_input(df))

    try:
        resolved = resolve_periods(data, "accum", params.window, params.freq)
        logger.debug("accum: resolved_window={}", resolved)
    except TransformError:
        if params.window is not None or params.freq is not None:
            raise
        resolved = get_config().transforms.accum_window
        logger.info(
            "Could not auto-detect frequency for accum. Using config accum_window={}",
            resolved,
        )

    factor = 1 + data / 100

    def _prod(x: np.ndarray) -> float:
        return float(np.prod(x))

    result = factor.rolling(resolved, min_periods=resolved).apply(  # type: ignore[union-attr]
        _prod, raw=True
    )
    result = (result - 1) * 100
    return sanitize_result(result)


# ---------------------------------------------------------------------------
# diff -- absolute difference
# ---------------------------------------------------------------------------


@overload
def diff(df: pd.DataFrame, periods: int = 1) -> pd.DataFrame: ...
@overload
def diff(df: pd.Series, periods: int = 1) -> pd.Series: ...
def diff(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    periods: int = 1,
) -> pd.DataFrame | pd.Series:
    """Absolute difference between periods.

    Args:
        df: Input data.
        periods: Number of periods for the diff. Negative for forward diff.
    """
    params = validate_params(_DiffParams, periods=periods)
    data = validate_numeric(coerce_input(df))
    return sanitize_result(data.diff(periods=params.periods))


# ---------------------------------------------------------------------------
# normalize -- rebase to base value
# ---------------------------------------------------------------------------


@overload
def normalize(
    df: pd.DataFrame,
    base: int | None = None,
    base_date: str | None = None,
) -> pd.DataFrame: ...
@overload
def normalize(
    df: pd.Series,
    base: int | None = None,
    base_date: str | None = None,
) -> pd.Series: ...
def normalize(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    base: int | None = None,
    base_date: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Normalize series to a base value.

    Uses the first non-NaN value as reference. If ``base_date`` is
    provided, uses the value at that date.

    Args:
        df: Input data.
        base: Base value for normalization (default: config ``normalize_base``).
            Must be positive.
        base_date: Reference date (string parseable by ``pd.Timestamp``).
            If the exact date does not exist in the index, uses the nearest one.
    """
    params = validate_params(_NormalizeParams, base=base, base_date=base_date)
    data = validate_numeric(coerce_input(df))

    effective_base = (
        params.base
        if params.base is not None
        else get_config().transforms.normalize_base
    )

    if params.base_date is not None:
        try:
            ts = pd.Timestamp(params.base_date)
        except (ValueError, TypeError) as exc:
            raise TransformError(
                f"Invalid base_date '{params.base_date}': {exc}"
            ) from exc
        if ts in data.index:
            base_value = data.loc[ts]
        else:
            idx = data.index.get_indexer([ts], method="nearest")
            if idx[0] == -1:
                raise TransformError(
                    f"base_date '{params.base_date}' could not be matched "
                    f"to any date in the index"
                )
            matched_date = data.index[idx[0]]
            logger.debug(
                "normalize: base_date '{}' matched to nearest '{}'", ts, matched_date
            )
            base_value = data.iloc[idx[0]]
    else:
        # First non-NaN value
        if isinstance(data, pd.DataFrame):
            base_value = data.apply(
                lambda s: s.dropna().iloc[0] if not s.dropna().empty else np.nan
            )
        else:
            clean = data.dropna()
            if clean.empty:
                raise TransformError("Cannot normalize: all values are NaN")
            base_value = clean.iloc[0]

    # Validate base_value
    if isinstance(base_value, (int, float, np.integer, np.floating)):
        if np.isnan(base_value) or base_value == 0:
            raise TransformError(
                f"Base value for normalization is {'NaN' if np.isnan(base_value) else 'zero'}. "
                f"Cannot divide by {'NaN' if np.isnan(base_value) else 'zero'}."
            )
    elif isinstance(base_value, pd.Series):
        # DataFrame: base_value is a Series (one entry per column)
        zero_cols = base_value[base_value == 0].index.tolist()
        nan_cols = base_value[base_value.isna()].index.tolist()
        problem_cols = zero_cols + nan_cols
        if problem_cols:
            raise TransformError(
                f"Base value is zero or NaN for columns: {problem_cols}. "
                f"Cannot normalize these columns."
            )
    else:
        raise TransformError(f"Unexpected base value type: {type(base_value).__name__}")

    result = (data / base_value) * effective_base
    return sanitize_result(result)


# ---------------------------------------------------------------------------
# annualize -- annualize periodic rate
# ---------------------------------------------------------------------------


@overload
def annualize(
    df: pd.DataFrame, periods: int | None = None, freq: str | None = None
) -> pd.DataFrame: ...
@overload
def annualize(
    df: pd.Series, periods: int | None = None, freq: str | None = None
) -> pd.Series: ...
def annualize(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    periods: int | None = None,
    freq: str | None = None,
) -> pd.DataFrame | pd.Series:
    """Annualize periodic rate via compound interest.

    Formula: ``((1 + r/100) ^ periods_per_year - 1) * 100``

    The number of periods per year is resolved automatically from the
    data frequency (e.g. 252 for daily, 12 for monthly).
    Use ``periods=`` or ``freq=`` to override.

    Args:
        df: Input data (rates in percentage).
        periods: Number of periods per year for compounding.
            Mutually exclusive with ``freq``.
        freq: Data frequency (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``, ``'Y'``).
            Mutually exclusive with ``periods``.
    """
    params = validate_params(_FreqResolvedParams, periods=periods, freq=freq)
    data = validate_numeric(coerce_input(df))
    resolved = resolve_periods(data, "annualize", params.periods, params.freq)
    logger.debug("annualize: resolved_periods_per_year={}", resolved)
    rate_decimal = data / 100
    annualized = (1 + rate_decimal) ** resolved - 1
    return sanitize_result(annualized * 100)


# ---------------------------------------------------------------------------
# drawdown -- percentage distance from historical peak
# ---------------------------------------------------------------------------


@overload
def drawdown(df: pd.DataFrame) -> pd.DataFrame: ...
@overload
def drawdown(df: pd.Series) -> pd.Series: ...
def drawdown(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
) -> pd.DataFrame | pd.Series:
    """Percentage distance from historical peak (drawdown).

    Formula: ``(data / cummax - 1) * 100``. Returns values <= 0,
    where 0 means the value is at its peak and negative values indicate
    the magnitude of the decline relative to the cumulative maximum.

    Args:
        df: Input data.
    """
    data = validate_numeric(coerce_input(df))
    cummax = data.cummax()

    # Drawdown requires strictly positive values (prices, indices).
    # cummax <= 0 causes division by zero or inverted results.
    has_non_positive = (
        (cummax <= 0).any().any()
        if isinstance(cummax, pd.DataFrame)
        else (cummax <= 0).any()
    )
    if has_non_positive:
        raise TransformError(
            "drawdown requires strictly positive values. "
            "Data contains zero or negative cumulative maximum."
        )

    result = (data / cummax - 1) * 100
    return sanitize_result(result)


# ---------------------------------------------------------------------------
# zscore -- statistical standardization
# ---------------------------------------------------------------------------


@overload
def zscore(df: pd.DataFrame, window: int | None = None) -> pd.DataFrame: ...
@overload
def zscore(df: pd.Series, window: int | None = None) -> pd.Series: ...
def zscore(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    window: int | None = None,
) -> pd.DataFrame | pd.Series:
    """Statistical standardization (z-score).

    Transforms the series into standard deviation units relative to the mean,
    removing scale and level. Allows comparing series with completely
    different units on the same chart.

    Global formula: ``(data - mean) / std``
    Rolling formula: ``(data - rolling_mean) / rolling_std``

    Args:
        df: Input data.
        window: Optional rolling window. If provided, computes rolling
            z-score (moving mean and std). If ``None``, computes
            z-score over the entire series (global).
    """
    params = validate_params(_ZScoreParams, window=window)
    data = validate_numeric(coerce_input(df))

    if params.window is not None:
        rolling = data.rolling(window=params.window, min_periods=params.window)
        mean = rolling.mean()
        std = rolling.std()
    else:
        mean = data.mean()
        std = data.std()

    result = (data - mean) / std

    # Warn when std=0 (constant data) produces all-NaN
    if isinstance(data, pd.DataFrame):
        all_nan_cols = result.columns[result.isna().all()].tolist()
        if all_nan_cols:
            logger.warning(
                "zscore produced all-NaN for columns {} (constant data, std=0)",
                all_nan_cols,
            )
    elif result.isna().all():
        logger.warning("zscore produced all-NaN (constant data, std=0)")

    return sanitize_result(result)


# ---------------------------------------------------------------------------
# to_month_end -- normalize index to month end
# ---------------------------------------------------------------------------


@overload
def to_month_end(df: pd.DataFrame) -> pd.DataFrame: ...
@overload
def to_month_end(df: pd.Series) -> pd.Series: ...
def to_month_end(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
) -> pd.DataFrame | pd.Series:
    """Normalize temporal index to month end, consolidating monthly observations.

    Each timestamp is mapped to the last day of its respective month.
    If multiple rows fall in the same month (e.g. daily data), keeps
    only the last chronological observation of that month.

    Args:
        df: Input data. Index must be DatetimeIndex.

    Raises:
        TransformError: If data is empty or index is not DatetimeIndex.
    """
    data = coerce_input(df)

    if data.empty:
        raise TransformError("Input data is empty")

    if not isinstance(data.index, pd.DatetimeIndex):
        raise TransformError(
            f"to_month_end requires DatetimeIndex, got {type(data.index).__name__}"
        )

    result = data.copy()
    result.index = result.index.to_period("M").to_timestamp("M")  # type: ignore[attr-defined]
    result = result.sort_index()
    return result.groupby(level=0).last()
