"""Tests for chartkit.transforms.temporal.accum.

Covers: compound product correctness, window sizes, freq resolution,
config fallback, edge cases including -100% rate.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import accum


class TestAccumKnownValues:
    def test_known_compound_product_window_3(
        self, known_accum_data: pd.DataFrame
    ) -> None:
        """[1%, 2%, 3%] window=3 -> (1.01*1.02*1.03 - 1)*100."""
        result = accum(known_accum_data, window=3)
        expected = (1.01 * 1.02 * 1.03 - 1) * 100
        assert result["rate"].iloc[-1] == pytest.approx(expected, rel=1e-6)

    def test_window_2_partial(self) -> None:
        """Window=2 computes product of 2 consecutive periods."""
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"rate": [1.0, 2.0, 3.0]}, index=idx)
        result = accum(df, window=2)
        expected = (1.01 * 1.02 - 1) * 100
        assert result["rate"].iloc[1] == pytest.approx(expected, rel=1e-6)

    def test_minus_100_rate_zeroes_product(self) -> None:
        """A -100% rate (total loss) zeros out the compound product."""
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"rate": [5.0, -100.0, 10.0]}, index=idx)
        result = accum(df, window=3)
        # (1.05 * 0.0 * 1.10 - 1) * 100 = -100%
        assert result["rate"].iloc[-1] == pytest.approx(-100.0, rel=1e-6)


class TestAccumFreqResolution:
    def test_explicit_window(self, monthly_rates: pd.DataFrame) -> None:
        """window=6 -> first 5 values are NaN (min_periods=6)."""
        result = accum(monthly_rates, window=6)
        assert result["cdi"].iloc[:5].isna().all()
        assert not np.isnan(result["cdi"].iloc[5])

    def test_explicit_freq(self, monthly_rates: pd.DataFrame) -> None:
        """freq='M' -> accum window=12."""
        result = accum(monthly_rates, freq="M")
        assert result["cdi"].iloc[:11].isna().all()

    def test_auto_detect_monthly(self, monthly_rates: pd.DataFrame) -> None:
        """Auto-detect ME -> accum window=12."""
        result = accum(monthly_rates)
        assert result["cdi"].iloc[:11].isna().all()

    def test_fallback_to_config_accum_window(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-datetime index falls back to config.transforms.accum_window."""
        mock_config = MagicMock()
        mock_config.transforms.accum_window = 3
        monkeypatch.setattr(
            "chartkit.transforms.temporal.get_config", lambda: mock_config
        )
        df = pd.DataFrame({"rate": [1.0, 2.0, 3.0, 4.0, 5.0]})
        result = accum(df)
        assert result["rate"].iloc[:2].isna().all()
        assert not np.isnan(result["rate"].iloc[2])


class TestAccumEdgeCases:
    def test_all_nan_window_produces_nan(self) -> None:
        """Single row with window>1 -> all NaN (insufficient data)."""
        idx = pd.date_range("2023-01-31", periods=1, freq="ME")
        df = pd.DataFrame({"rate": [1.0]}, index=idx)
        result = accum(df, window=3)
        assert result["rate"].isna().all()

    def test_both_window_and_freq_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="Cannot specify both"):
            accum(monthly_rates, window=6, freq="M")

    def test_multi_column_accum(self, monthly_rates: pd.DataFrame) -> None:
        """Both cdi and ipca columns accumulate independently."""
        result = accum(monthly_rates, window=3)
        assert list(result.columns) == ["cdi", "ipca"]
        assert not result.iloc[2:].isna().all().any()
