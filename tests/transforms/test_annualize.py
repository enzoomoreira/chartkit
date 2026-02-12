from __future__ import annotations

import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import annualize


class TestAnnualizeCorrectness:
    def test_monthly_rate_annualized(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"rate": [1.0, 1.0, 1.0]}, index=idx)
        result = annualize(df)
        # ((1 + 0.01)^12 - 1) * 100 = 12.6825%
        expected = ((1.01) ** 12 - 1) * 100
        assert result["rate"].iloc[0] == pytest.approx(expected, rel=1e-6)

    def test_freq_override_business_daily(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"rate": [0.04, 0.04, 0.04]}, index=idx)
        # freq="B" overrides auto-detect, resolves to 252 periods
        result = annualize(df, freq="B")
        expected = ((1 + 0.04 / 100) ** 252 - 1) * 100
        assert result["rate"].iloc[0] == pytest.approx(expected, rel=1e-4)


class TestAnnualizeFreqResolution:
    def test_explicit_periods(self, monthly_rates: pd.DataFrame) -> None:
        result = annualize(monthly_rates, periods=12)
        expected = ((1 + monthly_rates / 100) ** 12 - 1) * 100
        pd.testing.assert_frame_equal(result, expected)

    def test_explicit_freq(self, monthly_rates: pd.DataFrame) -> None:
        result = annualize(monthly_rates, freq="M")
        # freq="M" -> ME -> 12 periods (same as explicit_periods)
        expected = ((1 + monthly_rates / 100) ** 12 - 1) * 100
        pd.testing.assert_frame_equal(result, expected)

    def test_auto_detect(self, monthly_rates: pd.DataFrame) -> None:
        result = annualize(monthly_rates)
        # auto-detect ME -> 12 periods
        expected = ((1 + monthly_rates / 100) ** 12 - 1) * 100
        pd.testing.assert_frame_equal(result, expected)


class TestAnnualizeInputTypes:
    def test_accepts_series(self, single_series: pd.Series) -> None:
        result = annualize(single_series, freq="M")
        assert isinstance(result, pd.Series)

    def test_accepts_dataframe(self, monthly_rates: pd.DataFrame) -> None:
        result = annualize(monthly_rates)
        assert isinstance(result, pd.DataFrame)


class TestAnnualizeEdgeCases:
    def test_empty_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            annualize(empty_df, freq="M")

    def test_both_periods_freq_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="Cannot specify both"):
            annualize(monthly_rates, periods=12, freq="M")
