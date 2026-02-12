from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import variation


class TestVariationCorrectness:
    def test_month_over_month_known(self, known_variation_data: pd.DataFrame) -> None:
        result = variation(known_variation_data, horizon="month")
        vals = result["price"].to_list()
        assert np.isnan(vals[0])
        assert vals[1] == pytest.approx(10.0)
        assert vals[2] == pytest.approx(-10.0)
        assert vals[3] == pytest.approx(100 * (108 / 99 - 1))

    def test_year_over_year_monthly_data(self, monthly_rates: pd.DataFrame) -> None:
        result = variation(monthly_rates, horizon="year")
        # First 12 values should be NaN (no prior year)
        assert result["cdi"].iloc[:12].isna().all()
        # 13th value should exist
        assert not np.isnan(result["cdi"].iloc[12])

    def test_with_explicit_periods(self, monthly_rates: pd.DataFrame) -> None:
        result = variation(monthly_rates, periods=3)
        # First 3 values should be NaN
        assert result["cdi"].iloc[:3].isna().all()
        assert not np.isnan(result["cdi"].iloc[3])


class TestVariationInputTypes:
    def test_accepts_series(self, single_series: pd.Series) -> None:
        result = variation(single_series, horizon="month")
        assert isinstance(result, pd.Series)

    def test_accepts_dataframe(self, monthly_rates: pd.DataFrame) -> None:
        result = variation(monthly_rates, horizon="month")
        assert isinstance(result, pd.DataFrame)

    def test_accepts_dict(self) -> None:
        result = variation({"price": [100.0, 110.0, 99.0, 108.0]}, periods=1)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4
        assert result["price"].iloc[1] == pytest.approx(10.0)

    def test_accepts_list(self) -> None:
        result = variation([100.0, 110.0, 99.0], periods=1)
        assert isinstance(result, pd.Series)
        assert len(result) == 3
        assert result.iloc[1] == pytest.approx(10.0)


class TestVariationHorizon:
    def test_invalid_horizon_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="Invalid horizon"):
            variation(monthly_rates, horizon="week")

    def test_month_horizon(self, monthly_rates: pd.DataFrame) -> None:
        result = variation(monthly_rates, horizon="month")
        assert len(result) == len(monthly_rates)

    def test_year_horizon(self, monthly_rates: pd.DataFrame) -> None:
        result = variation(monthly_rates, horizon="year")
        assert len(result) == len(monthly_rates)


class TestVariationFreqResolution:
    def test_freq_override(self, monthly_rates: pd.DataFrame) -> None:
        result = variation(monthly_rates, horizon="year", freq="M")
        # freq="M" -> year -> 12 periods
        assert result.iloc[:12].isna().all().all()

    def test_auto_detect_monthly(self, monthly_rates: pd.DataFrame) -> None:
        result = variation(monthly_rates, horizon="month")
        # Auto-detect ME -> month -> 1 period
        assert result.iloc[0].isna().all()
        assert not result.iloc[1].isna().any()


class TestVariationEdgeCases:
    def test_empty_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            variation(empty_df, horizon="month")

    def test_inf_sanitized(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"val": [0.0, 100.0, 50.0]}, index=idx)
        result = variation(df, horizon="month")
        # 100/0 -> inf -> should be NaN
        assert np.isnan(result["val"].iloc[1])

    def test_mixed_dtypes_filtered(self, multi_series_monthly: pd.DataFrame) -> None:
        result = variation(multi_series_monthly, horizon="month")
        assert "category" not in result.columns
