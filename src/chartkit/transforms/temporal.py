"""Pure time series transforms.

All functions follow the contract:
- Accept DataFrame, Series, dict, list or ndarray (automatic coercion).
- Validate that data is numeric (warning + filtering for non-numeric).
- Guard against inf (replace with NaN in the result).
- Functions that depend on frequency (variation, accum, annualize)
  resolve periods via auto-detect or require explicit freq=/periods=.
"""

from __future__ import annotations

import logging
from typing import get_args, overload

import numpy as np
import pandas as pd

from .._internal.frequency import estimate_freq, infer_freq, normalize_freq_code
from ..exceptions import TransformError
from ..settings import get_config
from ..warnings import InferenceWarning, warn
from ._validation import (
    FREQ_PERIODS_MAP,
    _DespikeParams,
    _DiffParams,
    _FreqResolvedParams,
    _NormalizeParams,
    _ResampleParams,
    _RollingParams,
    _ZScoreParams,
    coerce_input,
    resolve_periods,
    sanitize_result,
    validate_numeric,
    validate_params,
)
from .types import DespikeMethod, Freq, Horizon, ResampleFreq, ResampleMethod

logger = logging.getLogger(__name__)

__all__ = [
    "variation",
    "accum",
    "diff",
    "normalize",
    "annualize",
    "drawdown",
    "zscore",
    "despike",
    "resample",
]


# ---------------------------------------------------------------------------
# variation -- percentage change by horizon
# ---------------------------------------------------------------------------

_VALID_HORIZONS = frozenset(get_args(Horizon))


@overload
def variation(
    df: pd.DataFrame,
    horizon: Horizon = "month",
    periods: int | None = None,
    freq: Freq | None = None,
) -> pd.DataFrame: ...
@overload
def variation(
    df: pd.Series,
    horizon: Horizon = "month",
    periods: int | None = None,
    freq: Freq | None = None,
) -> pd.Series: ...
def variation(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    horizon: Horizon = "month",
    periods: int | None = None,
    freq: Freq | None = None,
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
        periods: Explicit override of the number of periods. Must be
            positive: a negative lookback would compare each point with
            a future one. ``diff()`` does accept negatives, because
            there the sign chooses the direction of the difference.
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
    logger.debug("variation: horizon='%s', resolved_periods=%s", horizon, resolved)

    # Warn when horizon='month' does not mean "calendar month"
    if horizon == "month" and resolved == 1 and params.periods is None:
        detected = (
            infer_freq(data)
            if params.freq is None
            else normalize_freq_code(params.freq)
        )
        if detected in ("QE", "QS", "YE", "YS"):
            warn(
                f"horizon='month' with {detected} data resolves to periods=1 "
                f"(period-over-period, not calendar month-over-month)",
                InferenceWarning,
            )

    result = data.pct_change(periods=resolved) * 100
    return sanitize_result(result)


# ---------------------------------------------------------------------------
# accum -- cumulative change in rolling window
# ---------------------------------------------------------------------------


@overload
def accum(
    df: pd.DataFrame, window: int | None = None, freq: Freq | None = None
) -> pd.DataFrame: ...
@overload
def accum(
    df: pd.Series, window: int | None = None, freq: Freq | None = None
) -> pd.Series: ...
def accum(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    window: int | None = None,
    freq: Freq | None = None,
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
        logger.debug("accum: resolved_window=%s", resolved)
    except TransformError:
        if params.window is not None or params.freq is not None:
            raise
        # pd.infer_freq needs a perfectly regular index, which no market series
        # has -- one public holiday is enough for it to give up on data that is
        # plainly business-daily. Falling straight to the configured window then
        # accumulated over 12 *days*. The median spacing still tells daily from
        # monthly, so prefer it and keep the config value as the last resort.
        estimated = estimate_freq(data)
        mapping = FREQ_PERIODS_MAP.get(estimated) if estimated else None
        if mapping is not None:
            resolved = mapping["accum"]
            warn(
                f"Could not infer an exact frequency for accum; estimated "
                f"'{estimated}' from the median spacing between observations "
                f"(window={resolved}). Pass window= or freq= to be explicit.",
                InferenceWarning,
            )
        else:
            resolved = get_config().transforms.accum_window
            warn(
                f"Could not auto-detect frequency for accum; falling back to "
                f"config accum_window={resolved}. Pass window= or freq= to be "
                f"explicit.",
                InferenceWarning,
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
    base: float | None = None,
    base_date: str | None = None,
) -> pd.DataFrame: ...
@overload
def normalize(
    df: pd.Series,
    base: float | None = None,
    base_date: str | None = None,
) -> pd.Series: ...
def normalize(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    base: float | None = None,
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
            # get_indexer compares the timestamp against the index, so a
            # non-temporal index raises TypeError and a duplicated one raises
            # InvalidIndexError -- neither of which is a ChartKitError.
            try:
                idx = data.index.get_indexer([ts], method="nearest")
            except (TypeError, pd.errors.InvalidIndexError) as exc:
                raise TransformError(
                    f"base_date '{params.base_date}' cannot be matched against "
                    f"a {type(data.index).__name__}"
                    f"{' with duplicate entries' if not data.index.is_unique else ''}"
                    f": {exc}"
                ) from exc
            if idx[0] == -1:
                raise TransformError(
                    f"base_date '{params.base_date}' could not be matched "
                    f"to any date in the index"
                )
            matched_date = data.index[idx[0]]
            logger.debug(
                "normalize: base_date '%s' matched to nearest '%s'", ts, matched_date
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
    df: pd.DataFrame, periods: int | None = None, freq: Freq | None = None
) -> pd.DataFrame: ...
@overload
def annualize(
    df: pd.Series, periods: int | None = None, freq: Freq | None = None
) -> pd.Series: ...
def annualize(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    periods: int | None = None,
    freq: Freq | None = None,
) -> pd.DataFrame | pd.Series:
    """Annualize periodic rate via compound interest.

    Formula: ``((1 + r/100) ^ periods_per_year - 1) * 100``

    The number of periods per year is resolved automatically from the
    data frequency (e.g. 252 for daily, 12 for monthly).
    Use ``periods=`` or ``freq=`` to override.

    Args:
        df: Input data (rates in percentage).
        periods: Number of periods per year for compounding. Must be
            positive, unlike the ``periods`` of ``diff()``.
            Mutually exclusive with ``freq``.
        freq: Data frequency (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``, ``'Y'``).
            Mutually exclusive with ``periods``.
    """
    params = validate_params(_FreqResolvedParams, periods=periods, freq=freq)
    data = validate_numeric(coerce_input(df))
    resolved = resolve_periods(data, "annualize", params.periods, params.freq)
    logger.debug("annualize: resolved_periods_per_year=%s", resolved)
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

    # An all-NaN result has two very different causes, and reporting the wrong
    # one sends the reader looking at their data instead of their call.
    window_too_long = params.window is not None and params.window > len(data)
    cause = (
        f"window={params.window} exceeds the {len(data)} available observations"
        if window_too_long
        else "constant data, std=0"
    )

    if isinstance(data, pd.DataFrame):
        all_nan_cols = result.columns[result.isna().all()].tolist()
        if all_nan_cols:
            logger.warning(
                "zscore produced all-NaN for columns %s (%s)", all_nan_cols, cause
            )
    elif result.isna().all():
        logger.warning("zscore produced all-NaN (%s)", cause)

    return sanitize_result(result)


# ---------------------------------------------------------------------------
# despike -- detect and normalize aggressive data spikes (Hampel filter)
# ---------------------------------------------------------------------------

_HAMPEL_SCALE = 1.4826  # makes MAD consistent with std for normal distributions


@overload
def despike(
    df: pd.DataFrame,
    window: int = 21,
    threshold: float = 5.0,
    method: DespikeMethod = "median",
) -> pd.DataFrame: ...
@overload
def despike(
    df: pd.Series,
    window: int = 21,
    threshold: float = 5.0,
    method: DespikeMethod = "median",
) -> pd.Series: ...
def despike(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    window: int = 21,
    threshold: float = 5.0,
    method: DespikeMethod = "median",
) -> pd.DataFrame | pd.Series:
    """Detect and normalize aggressive data spikes using a Hampel filter.

    Uses rolling median and MAD (Median Absolute Deviation) to identify
    points that deviate dramatically from their local neighborhood.
    Designed for Bloomberg-style data where single data points spike
    to anomalous values.

    The modified z-score for each point is:
    ``|x - rolling_median| / (1.4826 * MAD)``

    Points exceeding the threshold are replaced according to ``method``.

    Args:
        df: Input data.
        window: Rolling window size (must be odd, >= 3). Centered window
            so neighbors on both sides are considered.
        threshold: Number of MADs to consider a spike. Higher values
            catch only more extreme anomalies. Default ``5.0`` is
            conservative (~5 sigma equivalent).
        method: Replacement strategy for detected spikes:
            ``'median'`` replaces with rolling median (default).
            ``'interpolate'`` sets spikes to NaN and interpolates linearly.
    """
    params = validate_params(
        _DespikeParams, window=window, threshold=threshold, method=method
    )
    data = validate_numeric(coerce_input(df))
    logger.debug(
        "despike: window=%s, threshold=%s, method='%s'",
        params.window,
        params.threshold,
        params.method,
    )

    rolling_median = data.rolling(params.window, center=True, min_periods=3).median()

    deviation = (data - rolling_median).abs()
    mad = deviation.rolling(params.window, center=True, min_periods=3).median()

    # Scaled MAD (consistent estimator of std for normal distribution)
    scaled_mad = _HAMPEL_SCALE * mad

    # When MAD=0 (locally constant data) and deviation>0, z-score is infinite
    # (any deviation from a constant neighborhood is infinitely many MADs away).
    # When MAD=0 and deviation=0, z-score is 0 (matches the constant value).
    modified_z = deviation / scaled_mad.replace(0, np.nan)
    has_deviation = deviation > 0
    modified_z = modified_z.where(
        scaled_mad.notna() & (scaled_mad != 0),
        other=np.where(has_deviation, np.inf, 0.0),
    )

    is_spike = modified_z > params.threshold

    # Count spikes for logging
    if isinstance(is_spike, pd.DataFrame):
        spike_count = int(is_spike.sum().sum())
    else:
        spike_count = int(is_spike.sum())

    if spike_count > 0:
        # Replacing spikes is what the caller asked for, so this is a report,
        # not a warning about an unrequested change.
        logger.info(
            "despike: replaced %s spike(s) using method='%s'",
            spike_count,
            params.method,
        )

    result = data.copy()
    if params.method == "median":
        result = result.where(~is_spike, rolling_median)
    else:
        # interpolate() fills every gap it finds, so it used to impute the NaNs
        # the caller supplied as well. Only the points this filter blanked out
        # are its to fill back in.
        was_missing = data.isna()
        result = result.where(~is_spike, np.nan)
        result = result.interpolate(method="linear").where(~was_missing)

    return sanitize_result(result)


# ---------------------------------------------------------------------------
# resample -- downsample temporal data to a target frequency
# ---------------------------------------------------------------------------

# User-friendly aliases -> pandas offset aliases
_RESAMPLE_OFFSETS: dict[str, str] = {
    "day": "D",
    "D": "D",
    "week": "W",
    "W": "W",
    "month": "ME",
    "M": "ME",
    "quarter": "QE",
    "Q": "QE",
    "year": "YE",
    "Y": "YE",
    "annual": "YE",
}


@overload
def resample(
    df: pd.DataFrame, freq: ResampleFreq = ..., method: ResampleMethod = ...
) -> pd.DataFrame: ...
@overload
def resample(
    df: pd.Series, freq: ResampleFreq = ..., method: ResampleMethod = ...
) -> pd.Series: ...
def resample(
    df: pd.DataFrame | pd.Series | dict | list | np.ndarray,
    freq: ResampleFreq = "month",
    method: ResampleMethod = "last",
) -> pd.DataFrame | pd.Series:
    """Resample temporal data to a target frequency.

    Downsamples data by grouping observations into time periods and
    applying an aggregation method.  Useful for reducing data density
    before plotting (e.g. daily -> monthly).

    Args:
        df: Input data.  Index must be DatetimeIndex.
        freq: Target frequency.  Accepts friendly names (``'day'``,
            ``'week'``, ``'month'``, ``'quarter'``, ``'year'``,
            ``'annual'``) or short codes (``'D'``, ``'W'``, ``'M'``,
            ``'Q'``, ``'Y'``).  Defaults to ``'month'``.
        method: Aggregation method -- ``'last'`` (default), ``'first'``,
            ``'mean'``, or ``'sum'``.

    Raises:
        TransformError: If data is empty, index is not DatetimeIndex,
            or parameters are invalid.
    """
    data = coerce_input(df)

    if data.empty:
        raise TransformError("Input data is empty")

    # Checked before validate_numeric: the index is what makes the call
    # meaningful at all, and validating the values first would emit a
    # frequency-detection warning about an index we are about to reject.
    if not isinstance(data.index, pd.DatetimeIndex):
        raise TransformError(
            f"resample requires DatetimeIndex, got {type(data.index).__name__}"
        )

    data = validate_numeric(data)

    params = validate_params(_ResampleParams, freq=freq, method=method)
    offset = _RESAMPLE_OFFSETS[params.freq]

    resampler = data.resample(offset)
    result = sanitize_result(getattr(resampler, params.method)())

    if isinstance(result, pd.Series):
        return result.dropna()
    return result.dropna(how="all")
