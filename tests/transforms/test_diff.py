from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import diff


class TestDiff:
    def test_basic_diff(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"val": [10.0, 12.0, 15.0]}, index=idx)
        result = diff(df)
        assert np.isnan(result["val"].iloc[0])
        assert result["val"].iloc[1] == pytest.approx(2.0)
        assert result["val"].iloc[2] == pytest.approx(3.0)

    def test_negative_periods(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"val": [10.0, 12.0, 15.0]}, index=idx)
        result = diff(df, periods=-1)
        # Forward diff: val[0]-val[1]=-2, val[1]-val[2]=-3, val[2]=NaN
        assert result["val"].iloc[0] == pytest.approx(-2.0)
        assert result["val"].iloc[1] == pytest.approx(-3.0)
        assert np.isnan(result["val"].iloc[2])

    def test_zero_periods_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="non-zero"):
            diff(monthly_rates, periods=0)

    def test_accepts_series(self, single_series: pd.Series) -> None:
        result = diff(single_series)
        assert isinstance(result, pd.Series)

    def test_accepts_dataframe(self, monthly_rates: pd.DataFrame) -> None:
        result = diff(monthly_rates)
        assert isinstance(result, pd.DataFrame)

    def test_empty_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            diff(empty_df)

    def test_default_periods_is_1(self, monthly_rates: pd.DataFrame) -> None:
        result = diff(monthly_rates)
        # First row should be NaN (periods=1)
        assert result.iloc[0].isna().all()
        assert not result.iloc[1].isna().any()
