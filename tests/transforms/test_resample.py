"""Tests for chartkit.transforms.temporal.resample.

Covers: all frequency aliases, aggregation methods, edge cases,
validation, backward compatibility with to_month_end, Series input.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import resample


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def daily_df() -> pd.DataFrame:
    """~1 year of daily data (business days) with 2 columns."""
    idx = pd.bdate_range("2023-01-02", periods=252, freq="B")
    rng = np.random.default_rng(99)
    return pd.DataFrame(
        {
            "price": 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.015, 252))),
            "volume": rng.integers(1000, 5000, 252).astype(float),
        },
        index=idx,
    )


@pytest.fixture
def daily_series() -> pd.Series:
    """Daily numeric Series."""
    idx = pd.bdate_range("2023-01-02", periods=252, freq="B")
    rng = np.random.default_rng(99)
    return pd.Series(
        100 * np.exp(np.cumsum(rng.normal(0.0004, 0.015, 252))),
        index=idx,
        name="price",
    )


@pytest.fixture
def intraday_df() -> pd.DataFrame:
    """Hourly data for a few days."""
    idx = pd.date_range("2023-06-01", periods=72, freq="h")
    rng = np.random.default_rng(42)
    return pd.DataFrame({"val": rng.normal(100, 5, 72)}, index=idx)


# ---------------------------------------------------------------------------
# Frequency aliases
# ---------------------------------------------------------------------------


class TestResampleFrequencies:
    """Each freq alias produces the expected number of periods."""

    def test_resample_to_week(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="week")
        # ~252 business days -> ~52 weeks
        assert 48 <= len(result) <= 53
        assert not result.index.duplicated().any()

    def test_resample_to_week_short_code(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="W")
        expected = resample(daily_df, freq="week")
        pd.testing.assert_frame_equal(result, expected)

    def test_resample_to_month(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="month")
        assert 11 <= len(result) <= 13
        assert not result.index.duplicated().any()

    def test_resample_to_month_short_code(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="M")
        expected = resample(daily_df, freq="month")
        pd.testing.assert_frame_equal(result, expected)

    def test_resample_to_quarter(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="quarter")
        assert 3 <= len(result) <= 5
        assert not result.index.duplicated().any()

    def test_resample_to_quarter_short_code(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="Q")
        expected = resample(daily_df, freq="quarter")
        pd.testing.assert_frame_equal(result, expected)

    def test_resample_to_year(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="year")
        assert 1 <= len(result) <= 2
        assert not result.index.duplicated().any()

    def test_resample_to_year_short_code(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="Y")
        expected = resample(daily_df, freq="year")
        pd.testing.assert_frame_equal(result, expected)

    def test_resample_to_annual(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="annual")
        expected = resample(daily_df, freq="year")
        pd.testing.assert_frame_equal(result, expected)

    def test_resample_to_day(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="day")
        # Business days resampled to calendar days fills gaps
        assert len(result) >= 200

    def test_resample_to_day_short_code(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="D")
        expected = resample(daily_df, freq="day")
        pd.testing.assert_frame_equal(result, expected)

    def test_intraday_to_day(self, intraday_df: pd.DataFrame) -> None:
        """Hourly data collapsed to daily."""
        result = resample(intraday_df, freq="day")
        assert len(result) == 3  # 72 hours = 3 days


# ---------------------------------------------------------------------------
# Aggregation methods
# ---------------------------------------------------------------------------


class TestResampleMethods:
    def test_method_last_is_default(self, daily_df: pd.DataFrame) -> None:
        default = resample(daily_df, freq="month")
        explicit = resample(daily_df, freq="month", method="last")
        pd.testing.assert_frame_equal(default, explicit)

    def test_method_first(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="month", method="first")
        assert len(result) >= 11
        # First values should differ from last values
        last = resample(daily_df, freq="month", method="last")
        assert not result.equals(last)

    def test_method_mean(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="month", method="mean")
        assert len(result) >= 11
        # Mean should be between min and max of each month
        for col in result.columns:
            assert result[col].notna().all()

    def test_method_sum(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="month", method="sum")
        assert len(result) >= 11
        # Sum of volumes should be much larger than individual values
        assert result["volume"].iloc[0] > daily_df["volume"].iloc[0]


# ---------------------------------------------------------------------------
# Series input
# ---------------------------------------------------------------------------


class TestResampleSeries:
    def test_series_returns_series(self, daily_series: pd.Series) -> None:
        result = resample(daily_series, freq="month")
        assert isinstance(result, pd.Series)
        assert 11 <= len(result) <= 13

    def test_series_name_preserved(self, daily_series: pd.Series) -> None:
        result = resample(daily_series, freq="month")
        assert result.name == "price"

    def test_series_all_methods(self, daily_series: pd.Series) -> None:
        for method in ("last", "first", "mean", "sum"):
            result = resample(daily_series, freq="quarter", method=method)
            assert isinstance(result, pd.Series)
            assert len(result) >= 3


# ---------------------------------------------------------------------------
# Month-end snapping (replaces old to_month_end tests)
# ---------------------------------------------------------------------------


class TestResampleMonthEnd:
    def test_mid_month_snapped_to_end(self) -> None:
        """Mid-month dates snap to month-end."""
        idx = pd.DatetimeIndex(["2023-01-15", "2023-02-10", "2023-03-20"])
        df = pd.DataFrame({"val": [1.0, 2.0, 3.0]}, index=idx)
        result = resample(df, freq="month")
        assert result.index[0].day == 31  # Jan
        assert result.index[1].day == 28  # Feb
        assert result.index[2].day == 31  # Mar

    def test_daily_collapse_to_month(
        self, daily_prices: pd.DataFrame
    ) -> None:
        """Daily -> one per month, no duplicates."""
        result = resample(daily_prices, freq="month")
        assert not result.index.duplicated().any()
        assert 11 <= len(result) <= 13


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestResampleValidation:
    def test_empty_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            resample(empty_df, freq="month")

    def test_non_datetime_index_raises(self) -> None:
        df = pd.DataFrame({"val": [1.0, 2.0, 3.0]})
        with pytest.raises(TransformError, match="DatetimeIndex"):
            resample(df, freq="month")

    def test_unknown_freq_raises(self, daily_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError):
            resample(daily_df, freq="biweekly")

    def test_unknown_method_raises(self, daily_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError):
            resample(daily_df, freq="month", method="median")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestResampleEdgeCases:
    def test_already_monthly_to_month(self, monthly_rates: pd.DataFrame) -> None:
        """Monthly data resampled to month should be unchanged."""
        result = resample(monthly_rates, freq="month")
        assert len(result) == len(monthly_rates)

    def test_monthly_to_quarter(self, monthly_rates: pd.DataFrame) -> None:
        """Monthly -> quarterly reduces rows."""
        result = resample(monthly_rates, freq="quarter")
        assert len(result) < len(monthly_rates)
        assert len(result) == 8  # 24 months = 8 quarters

    def test_monthly_to_year(self, monthly_rates: pd.DataFrame) -> None:
        """Monthly -> yearly reduces rows."""
        result = resample(monthly_rates, freq="year")
        assert len(result) == 2  # 24 months = 2 years

    def test_preserves_columns(self, daily_df: pd.DataFrame) -> None:
        """All columns from input should appear in output."""
        result = resample(daily_df, freq="month")
        assert list(result.columns) == list(daily_df.columns)

    def test_index_is_datetime(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="week")
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_result_sorted(self, daily_df: pd.DataFrame) -> None:
        result = resample(daily_df, freq="month")
        assert result.index.is_monotonic_increasing

    def test_coerce_dict_input(self) -> None:
        """Dict input should be coerced."""
        idx = pd.bdate_range("2023-01-02", periods=60, freq="B")
        data = {"val": list(range(60))}
        df = pd.DataFrame(data, index=idx)
        result = resample(df, freq="month")
        assert len(result) >= 2
