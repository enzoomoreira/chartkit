"""Tests for chartkit.transforms.temporal.zscore.

Covers: global z-score, rolling window, constant data, validation,
multi-column behavior.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import zscore


class TestZscoreGlobal:
    def test_known_global_zscore(self, known_zscore_data: pd.Series) -> None:
        """[10, 20, 30] mean=20 std=10 -> [-1, 0, 1]."""
        result = zscore(known_zscore_data)
        assert result.iloc[0] == pytest.approx(-1.0)
        assert result.iloc[1] == pytest.approx(0.0)
        assert result.iloc[2] == pytest.approx(1.0)

    def test_constant_data_produces_all_nan(self, constant_series: pd.Series) -> None:
        """std=0 -> division by zero -> all NaN (with warning)."""
        result = zscore(constant_series)
        assert result.isna().all()


class TestZscoreRolling:
    def test_rolling_window_3(self, monthly_rates: pd.DataFrame) -> None:
        """min_periods=3 -> first 2 values are NaN."""
        result = zscore(monthly_rates, window=3)
        assert result["cdi"].iloc[:2].isna().all()
        assert not np.isnan(result["cdi"].iloc[2])

    def test_rolling_window_2_minimum(self) -> None:
        """Window=2 is the minimum valid rolling window."""
        idx = pd.date_range("2023-01-31", periods=4, freq="ME")
        df = pd.DataFrame({"val": [10.0, 20.0, 30.0, 40.0]}, index=idx)
        result = zscore(df, window=2)
        assert np.isnan(result["val"].iloc[0])
        assert not np.isnan(result["val"].iloc[1])


class TestZscoreValidation:
    def test_window_1_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match=">= 2"):
            zscore(monthly_rates, window=1)

    def test_window_0_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="greater than 0"):
            zscore(monthly_rates, window=0)


class TestZscoreMultiColumn:
    def test_multi_column_independent(self, monthly_rates: pd.DataFrame) -> None:
        """Each column is standardized independently."""
        result = zscore(monthly_rates)
        assert list(result.columns) == ["cdi", "ipca"]
        # Mean of each z-scored column should be ~0
        assert result["cdi"].mean() == pytest.approx(0.0, abs=1e-10)
        assert result["ipca"].mean() == pytest.approx(0.0, abs=1e-10)

    def test_mixed_dtypes_drops_non_numeric(
        self, multi_series_monthly: pd.DataFrame
    ) -> None:
        result = zscore(multi_series_monthly)
        assert "category" not in result.columns
