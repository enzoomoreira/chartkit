"""Tests for frequency resolution: normalize_freq_code, infer_freq, resolve_periods.

Consolidates test_resolve_periods.py (26 tests -> 12) + test_validate_params.py.
Uses parametrize for freq alias mappings.
"""

from __future__ import annotations

import pandas as pd
import pytest

from chartkit._internal.frequency import infer_freq, normalize_freq_code
from chartkit.exceptions import TransformError
from chartkit.transforms._validation import (
    _DiffParams,
    _FreqResolvedParams,
    _NormalizeParams,
    _RollingParams,
    _ZScoreParams,
    resolve_periods,
    validate_params,
)


# ---------------------------------------------------------------------------
# normalize_freq_code
# ---------------------------------------------------------------------------


class TestNormalizeFreqCode:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("M", "ME"),
            ("Q", "QE"),
            ("Y", "YE"),
            ("monthly", "ME"),
            ("quarterly", "QE"),
            ("yearly", "YE"),
            ("annual", "YE"),
            ("D", "D"),
            ("B", "B"),
            ("daily", "D"),
            ("business", "B"),
            ("weekly", "W"),
        ],
        ids=[
            "M->ME",
            "Q->QE",
            "Y->YE",
            "monthly->ME",
            "quarterly->QE",
            "yearly->YE",
            "annual->YE",
            "D->D",
            "B->B",
            "daily->D",
            "business->B",
            "weekly->W",
        ],
    )
    def test_alias_mapping(self, raw: str, expected: str) -> None:
        assert normalize_freq_code(raw) == expected

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("W-SUN", "W"),
            ("QE-DEC", "QE"),
            ("BYE-DEC", "BYE"),
            ("YS-JAN", "YS"),
        ],
        ids=["W-SUN", "QE-DEC", "BYE-DEC", "YS-JAN"],
    )
    def test_anchored_prefix_stripping(self, raw: str, expected: str) -> None:
        assert normalize_freq_code(raw) == expected

    def test_already_normalized_passthrough(self) -> None:
        assert normalize_freq_code("ME") == "ME"

    def test_unknown_passthrough(self) -> None:
        assert normalize_freq_code("UNKNOWN") == "UNKNOWN"


# ---------------------------------------------------------------------------
# infer_freq
# ---------------------------------------------------------------------------


class TestInferFreq:
    def test_monthly_data(self, monthly_index: pd.DatetimeIndex) -> None:
        df = pd.DataFrame({"val": range(len(monthly_index))}, index=monthly_index)
        result = infer_freq(df)
        assert result in ("ME", "MS")

    def test_daily_business_data(self, daily_index: pd.DatetimeIndex) -> None:
        df = pd.DataFrame({"val": range(len(daily_index))}, index=daily_index)
        result = infer_freq(df)
        assert result in ("B", "D")

    def test_too_short_returns_none(self) -> None:
        idx = pd.date_range("2023-01-01", periods=2, freq="ME")
        df = pd.DataFrame({"val": [1, 2]}, index=idx)
        assert infer_freq(df) is None

    def test_non_datetime_returns_none(self) -> None:
        df = pd.DataFrame({"val": [1, 2, 3, 4]})
        assert infer_freq(df) is None

    def test_irregular_returns_none(self) -> None:
        idx = pd.DatetimeIndex(["2023-01-01", "2023-02-15", "2023-05-20", "2023-11-01"])
        df = pd.DataFrame({"val": [1, 2, 3, 4]}, index=idx)
        assert infer_freq(df) is None


# ---------------------------------------------------------------------------
# resolve_periods
# ---------------------------------------------------------------------------


class TestResolvePeriods:
    def test_explicit_periods_returned_as_is(self, monthly_rates: pd.DataFrame) -> None:
        assert resolve_periods(monthly_rates, "month", periods=5, freq=None) == 5

    def test_explicit_periods_ignores_data(self) -> None:
        """Even without DatetimeIndex, explicit periods works."""
        df = pd.DataFrame({"val": [1.0, 2.0, 3.0]})
        assert resolve_periods(df, "month", periods=7, freq=None) == 7

    @pytest.mark.parametrize(
        "freq, transform, expected",
        [
            ("M", "month", 1),
            ("M", "year", 12),
            ("D", "year", 365),
            ("B", "annualize", 252),
            ("Q", "year", 4),
        ],
        ids=["M-month", "M-year", "D-year", "B-annualize", "Q-year"],
    )
    def test_explicit_freq_lookup(
        self,
        monthly_rates: pd.DataFrame,
        freq: str,
        transform: str,
        expected: int,
    ) -> None:
        result = resolve_periods(monthly_rates, transform, periods=None, freq=freq)
        assert result == expected

    def test_unknown_explicit_freq_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="Unknown frequency"):
            resolve_periods(monthly_rates, "month", periods=None, freq="XYZ")

    def test_auto_detect_monthly_year(self, monthly_rates: pd.DataFrame) -> None:
        result = resolve_periods(monthly_rates, "year", periods=None, freq=None)
        assert result == 12

    def test_no_freq_no_periods_int_index_raises(self) -> None:
        df = pd.DataFrame({"val": [1.0, 2.0, 3.0, 4.0]})
        with pytest.raises(TransformError, match="Cannot determine frequency"):
            resolve_periods(df, "month", periods=None, freq=None)


# ---------------------------------------------------------------------------
# validate_params (Pydantic models)
# ---------------------------------------------------------------------------


class TestFreqResolvedParamsValidation:
    def test_both_none_valid(self) -> None:
        p = validate_params(_FreqResolvedParams)
        assert p.periods is None and p.freq is None

    def test_both_specified_raises(self) -> None:
        with pytest.raises(TransformError, match="Cannot specify both"):
            validate_params(_FreqResolvedParams, periods=12, freq="M")

    def test_negative_periods_raises(self) -> None:
        with pytest.raises(TransformError):
            validate_params(_FreqResolvedParams, periods=-1)

    def test_zero_periods_raises(self) -> None:
        with pytest.raises(TransformError):
            validate_params(_FreqResolvedParams, periods=0)


class TestRollingParamsValidation:
    def test_both_specified_raises(self) -> None:
        with pytest.raises(TransformError, match="Cannot specify both"):
            validate_params(_RollingParams, window=6, freq="M")

    def test_negative_window_raises(self) -> None:
        with pytest.raises(TransformError):
            validate_params(_RollingParams, window=-1)


class TestDiffParamsValidation:
    def test_positive_valid(self) -> None:
        assert validate_params(_DiffParams, periods=1).periods == 1

    def test_negative_valid(self) -> None:
        assert validate_params(_DiffParams, periods=-1).periods == -1

    def test_zero_raises(self) -> None:
        with pytest.raises(TransformError, match="non-zero"):
            validate_params(_DiffParams, periods=0)


class TestZScoreParamsValidation:
    def test_none_window_valid(self) -> None:
        assert validate_params(_ZScoreParams).window is None

    def test_window_1_raises(self) -> None:
        with pytest.raises(TransformError, match=">= 2"):
            validate_params(_ZScoreParams, window=1)


class TestNormalizeParamsValidation:
    def test_defaults_valid(self) -> None:
        p = validate_params(_NormalizeParams)
        assert p.base is None and p.base_date is None

    def test_base_positive_valid(self) -> None:
        assert validate_params(_NormalizeParams, base=100).base == 100
