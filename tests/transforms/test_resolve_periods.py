from __future__ import annotations

import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms._validation import (
    _infer_freq,
    _normalize_freq_code,
    resolve_periods,
)


class TestNormalizeFreqCode:
    def test_alias_M_to_ME(self) -> None:
        assert _normalize_freq_code("M") == "ME"

    def test_alias_Q_to_QE(self) -> None:
        assert _normalize_freq_code("Q") == "QE"

    def test_alias_Y_to_YE(self) -> None:
        assert _normalize_freq_code("Y") == "YE"

    def test_word_monthly(self) -> None:
        assert _normalize_freq_code("monthly") == "ME"

    def test_word_quarterly(self) -> None:
        assert _normalize_freq_code("quarterly") == "QE"

    def test_word_yearly(self) -> None:
        assert _normalize_freq_code("yearly") == "YE"

    def test_word_annual(self) -> None:
        assert _normalize_freq_code("annual") == "YE"

    def test_anchored_W_SUN(self) -> None:
        assert _normalize_freq_code("W-SUN") == "W"

    def test_anchored_QE_DEC(self) -> None:
        assert _normalize_freq_code("QE-DEC") == "QE"

    def test_anchored_BYE_DEC(self) -> None:
        assert _normalize_freq_code("BYE-DEC") == "BYE"

    def test_already_normalized(self) -> None:
        assert _normalize_freq_code("ME") == "ME"

    def test_unknown_passthrough(self) -> None:
        assert _normalize_freq_code("UNKNOWN") == "UNKNOWN"


class TestInferFreq:
    def test_monthly_data(self, monthly_index: pd.DatetimeIndex) -> None:
        df = pd.DataFrame({"val": range(len(monthly_index))}, index=monthly_index)
        result = _infer_freq(df)
        assert result in ("ME", "MS")

    def test_daily_data(self, daily_index: pd.DatetimeIndex) -> None:
        df = pd.DataFrame({"val": range(len(daily_index))}, index=daily_index)
        result = _infer_freq(df)
        assert result in ("B", "D")

    def test_too_short_returns_none(self) -> None:
        idx = pd.date_range("2023-01-01", periods=2, freq="ME")
        df = pd.DataFrame({"val": [1, 2]}, index=idx)
        assert _infer_freq(df) is None

    def test_non_datetime_returns_none(self) -> None:
        df = pd.DataFrame({"val": [1, 2, 3, 4]})
        assert _infer_freq(df) is None

    def test_irregular_returns_none(self) -> None:
        idx = pd.DatetimeIndex(["2023-01-01", "2023-02-15", "2023-05-20", "2023-11-01"])
        df = pd.DataFrame({"val": [1, 2, 3, 4]}, index=idx)
        assert _infer_freq(df) is None


class TestResolvePeriods:
    def test_explicit_periods_returned(self, monthly_rates: pd.DataFrame) -> None:
        result = resolve_periods(monthly_rates, "month", periods=5, freq=None)
        assert result == 5

    def test_explicit_freq_M_month(self, monthly_rates: pd.DataFrame) -> None:
        result = resolve_periods(monthly_rates, "month", periods=None, freq="M")
        assert result == 1

    def test_explicit_freq_M_year(self, monthly_rates: pd.DataFrame) -> None:
        result = resolve_periods(monthly_rates, "year", periods=None, freq="M")
        assert result == 12

    def test_explicit_freq_D_year(self, daily_prices: pd.DataFrame) -> None:
        result = resolve_periods(daily_prices, "year", periods=None, freq="D")
        assert result == 365

    def test_explicit_freq_B_annualize(self, daily_prices: pd.DataFrame) -> None:
        result = resolve_periods(daily_prices, "annualize", periods=None, freq="B")
        assert result == 252

    def test_unknown_explicit_freq_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="Unknown frequency"):
            resolve_periods(monthly_rates, "month", periods=None, freq="XYZ")

    def test_auto_detect_monthly(self, monthly_rates: pd.DataFrame) -> None:
        result = resolve_periods(monthly_rates, "year", periods=None, freq=None)
        assert result == 12

    def test_no_freq_no_periods_int_index_raises(self) -> None:
        df = pd.DataFrame({"val": [1.0, 2.0, 3.0, 4.0]})
        with pytest.raises(TransformError, match="Cannot determine frequency"):
            resolve_periods(df, "month", periods=None, freq=None)

    def test_explicit_periods_ignores_data(self) -> None:
        df = pd.DataFrame({"val": [1.0, 2.0, 3.0]})
        result = resolve_periods(df, "month", periods=7, freq=None)
        assert result == 7
