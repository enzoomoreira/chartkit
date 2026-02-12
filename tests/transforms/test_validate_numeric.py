from __future__ import annotations

import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms._validation import validate_numeric


class TestValidateNumericSeries:
    def test_numeric_series_passthrough(self, single_series: pd.Series) -> None:
        result = validate_numeric(single_series)
        assert result is single_series

    def test_non_numeric_series_raises(self) -> None:
        s = pd.Series(["a", "b", "c"])
        with pytest.raises(TransformError, match="must be numeric"):
            validate_numeric(s)

    def test_empty_series_raises(self, empty_series: pd.Series) -> None:
        with pytest.raises(TransformError, match="empty"):
            validate_numeric(empty_series)

    def test_non_datetime_index_no_raise(
        self, non_datetime_index_df: pd.DataFrame
    ) -> None:
        # loguru logs warning (not stdlib warnings), just verify no exception
        s = non_datetime_index_df["val"]
        result = validate_numeric(s)
        assert len(result) == 5

    def test_datetime_index_no_warning(self, single_series: pd.Series) -> None:
        result = validate_numeric(single_series)
        assert isinstance(result.index, pd.DatetimeIndex)


class TestValidateNumericDataFrame:
    def test_numeric_df_passthrough(self, monthly_rates: pd.DataFrame) -> None:
        result = validate_numeric(monthly_rates)
        assert result is monthly_rates

    def test_mixed_df_drops_non_numeric(
        self, multi_series_monthly: pd.DataFrame
    ) -> None:
        result = validate_numeric(multi_series_monthly)
        assert "category" not in result.columns
        assert len(result.columns) == 3

    def test_all_non_numeric_df_raises(self) -> None:
        df = pd.DataFrame({"a": ["x", "y"], "b": ["z", "w"]})
        with pytest.raises(TransformError, match="No numeric columns"):
            validate_numeric(df)

    def test_empty_df_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            validate_numeric(empty_df)

    def test_non_datetime_index_df(self, non_datetime_index_df: pd.DataFrame) -> None:
        # Should not raise, just logs warning
        result = validate_numeric(non_datetime_index_df)
        assert len(result) == 5


class TestValidateNumericReturnType:
    def test_returns_series_for_series_input(self, single_series: pd.Series) -> None:
        result = validate_numeric(single_series)
        assert isinstance(result, pd.Series)

    def test_returns_dataframe_for_df_input(self, monthly_rates: pd.DataFrame) -> None:
        result = validate_numeric(monthly_rates)
        assert isinstance(result, pd.DataFrame)
