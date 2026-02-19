"""Tests for chartkit.transforms.temporal.annualize.

Covers: known-value correctness, freq resolution (explicit, auto-detect),
validation.
"""

from __future__ import annotations

import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import annualize


class TestAnnualizeKnownValues:
    def test_monthly_1pct_annualized(self) -> None:
        """1% monthly -> ((1.01)^12 - 1)*100 = 12.6825%."""
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"rate": [1.0, 1.0, 1.0]}, index=idx)
        result = annualize(df)
        expected = ((1.01) ** 12 - 1) * 100
        assert result["rate"].iloc[0] == pytest.approx(expected, rel=1e-6)

    def test_freq_override_business_daily(self) -> None:
        """freq='B' overrides auto-detect -> 252 periods."""
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"rate": [0.04, 0.04, 0.04]}, index=idx)
        result = annualize(df, freq="B")
        expected = ((1 + 0.04 / 100) ** 252 - 1) * 100
        assert result["rate"].iloc[0] == pytest.approx(expected, rel=1e-4)


class TestAnnualizeFreqResolution:
    def test_explicit_periods(self, monthly_rates: pd.DataFrame) -> None:
        result = annualize(monthly_rates, periods=12)
        expected = ((1 + monthly_rates / 100) ** 12 - 1) * 100
        pd.testing.assert_frame_equal(result, expected)

    def test_auto_detect_monthly(self, monthly_rates: pd.DataFrame) -> None:
        """Auto-detect ME -> 12 periods per year."""
        result = annualize(monthly_rates)
        expected = ((1 + monthly_rates / 100) ** 12 - 1) * 100
        pd.testing.assert_frame_equal(result, expected)


class TestAnnualizeValidation:
    def test_both_periods_and_freq_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="Cannot specify both"):
            annualize(monthly_rates, periods=12, freq="M")
