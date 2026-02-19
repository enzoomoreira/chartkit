"""Tests for chartkit.transforms.temporal.variation.

Covers: known-value correctness, horizons (month/year), multi-column,
freq resolution, quarterly data edge case, irregular timeseries.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import variation


class TestVariationKnownValues:
    def test_month_over_month_known(self, known_variation_data: pd.DataFrame) -> None:
        """[100, 110, 99, 108] -> MoM: [NaN, +10%, -10%, +9.09%]."""
        result = variation(known_variation_data, horizon="month")
        vals = result["price"].to_list()
        assert np.isnan(vals[0])
        assert vals[1] == pytest.approx(10.0)
        assert vals[2] == pytest.approx(-10.0)
        assert vals[3] == pytest.approx(100 * (108 / 99 - 1))

    def test_year_over_year_monthly_data(self, monthly_rates: pd.DataFrame) -> None:
        """YoY on 24-month data: first 12 are NaN, 13th is computed."""
        result = variation(monthly_rates, horizon="year")
        assert result["cdi"].iloc[:12].isna().all()
        assert not np.isnan(result["cdi"].iloc[12])

    def test_explicit_periods_overrides_auto(self, monthly_rates: pd.DataFrame) -> None:
        """periods=3 produces NaN in positions [0..2] regardless of freq."""
        result = variation(monthly_rates, periods=3)
        assert result["cdi"].iloc[:3].isna().all()
        assert not np.isnan(result["cdi"].iloc[3])


class TestVariationMultiColumn:
    def test_multi_column_preserves_shape(self, monthly_rates: pd.DataFrame) -> None:
        """All numeric columns are transformed, shape is preserved."""
        result = variation(monthly_rates, horizon="month")
        assert list(result.columns) == list(monthly_rates.columns)
        assert len(result) == len(monthly_rates)

    def test_mixed_dtypes_drops_non_numeric(
        self, multi_series_monthly: pd.DataFrame
    ) -> None:
        """String column 'category' is dropped silently."""
        result = variation(multi_series_monthly, horizon="month")
        assert "category" not in result.columns


class TestVariationFreqResolution:
    def test_freq_override(self, monthly_rates: pd.DataFrame) -> None:
        """freq='M' forces year -> 12 periods even when auto-detect would match."""
        result = variation(monthly_rates, horizon="year", freq="M")
        assert result.iloc[:12].isna().all().all()

    def test_auto_detect_monthly_month_horizon(
        self, monthly_rates: pd.DataFrame
    ) -> None:
        """Auto-detect ME + horizon='month' -> 1 period."""
        result = variation(monthly_rates, horizon="month")
        assert result.iloc[0].isna().all()
        assert not result.iloc[1].isna().any()


class TestVariationHorizons:
    def test_invalid_horizon_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="Invalid horizon"):
            variation(monthly_rates, horizon="week")

    def test_quarterly_data_month_horizon_resolves_to_1(
        self, quarterly_rates: pd.DataFrame
    ) -> None:
        """horizon='month' on quarterly data -> periods=1 (period-over-period)."""
        result = variation(quarterly_rates, horizon="month")
        assert np.isnan(result["rate"].iloc[0])
        assert not np.isnan(result["rate"].iloc[1])
        # Second value: pct_change(1) = (2.5/2.0 - 1)*100 = 25%
        assert result["rate"].iloc[1] == pytest.approx(25.0)


class TestVariationEdgeCases:
    def test_inf_sanitized_to_nan(self) -> None:
        """Division by zero (100/0) produces inf -> sanitized to NaN."""
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"val": [0.0, 100.0, 50.0]}, index=idx)
        result = variation(df, horizon="month")
        assert np.isnan(result["val"].iloc[1])

    def test_irregular_timeseries_requires_explicit_freq(
        self, irregular_daily_prices: pd.DataFrame
    ) -> None:
        """Irregular dates fail auto-detect; must pass periods= or freq=."""
        with pytest.raises(TransformError, match="Cannot determine frequency"):
            variation(irregular_daily_prices, horizon="month")
        # With explicit periods it works fine
        result = variation(irregular_daily_prices, horizon="month", periods=1)
        assert len(result) == len(irregular_daily_prices)
