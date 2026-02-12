from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import zscore


class TestZscoreGlobal:
    def test_known_global_zscore(self, known_zscore_data: pd.Series) -> None:
        result = zscore(known_zscore_data)
        # [10, 20, 30] mean=20 std=10 -> [-1, 0, 1]
        assert result.iloc[0] == pytest.approx(-1.0)
        assert result.iloc[1] == pytest.approx(0.0)
        assert result.iloc[2] == pytest.approx(1.0)

    def test_constant_data_all_nan(self, constant_series: pd.Series) -> None:
        result = zscore(constant_series)
        assert result.isna().all()


class TestZscoreRolling:
    def test_rolling_window_3(self, monthly_rates: pd.DataFrame) -> None:
        result = zscore(monthly_rates, window=3)
        # First 2 values should be NaN (min_periods=3)
        assert result["cdi"].iloc[:2].isna().all()
        # Third value should exist
        assert not np.isnan(result["cdi"].iloc[2])

    def test_rolling_window_2_minimum(self) -> None:
        idx = pd.date_range("2023-01-31", periods=4, freq="ME")
        df = pd.DataFrame({"val": [10.0, 20.0, 30.0, 40.0]}, index=idx)
        result = zscore(df, window=2)
        # First value NaN, second should be computed
        assert np.isnan(result["val"].iloc[0])
        assert not np.isnan(result["val"].iloc[1])


class TestZscoreValidation:
    def test_window_1_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match=">= 2"):
            zscore(monthly_rates, window=1)

    def test_window_0_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="greater than 0"):
            zscore(monthly_rates, window=0)


class TestZscoreInputTypes:
    def test_accepts_series(self, single_series: pd.Series) -> None:
        result = zscore(single_series)
        assert isinstance(result, pd.Series)

    def test_accepts_dataframe(self, monthly_rates: pd.DataFrame) -> None:
        result = zscore(monthly_rates)
        assert isinstance(result, pd.DataFrame)


class TestZscoreEdgeCases:
    def test_empty_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            zscore(empty_df)

    def test_mixed_dtypes_filtered(self, multi_series_monthly: pd.DataFrame) -> None:
        result = zscore(multi_series_monthly)
        assert "category" not in result.columns
