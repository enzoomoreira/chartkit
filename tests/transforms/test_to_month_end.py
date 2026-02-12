from __future__ import annotations

import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import to_month_end


class TestToMonthEnd:
    def test_monthly_data_unchanged(self, monthly_rates: pd.DataFrame) -> None:
        result = to_month_end(monthly_rates)
        # Month-end dates should stay the same (already ME frequency)
        assert len(result) == len(monthly_rates)
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_mid_month_snapped(self) -> None:
        idx = pd.DatetimeIndex(["2023-01-15", "2023-02-10", "2023-03-20"])
        df = pd.DataFrame({"val": [1.0, 2.0, 3.0]}, index=idx)
        result = to_month_end(df)
        assert result.index[0].day == 31  # Jan 31
        assert result.index[1].day == 28  # Feb 28
        assert result.index[2].day == 31  # Mar 31

    def test_daily_data_creates_duplicates(self, daily_prices: pd.DataFrame) -> None:
        result = to_month_end(daily_prices)
        # Multiple daily dates map to same month-end
        assert result.index.duplicated().any()


class TestToMonthEndValidation:
    def test_non_datetime_index_raises(self) -> None:
        df = pd.DataFrame({"val": [1.0, 2.0, 3.0]})
        with pytest.raises(TransformError, match="DatetimeIndex"):
            to_month_end(df)

    def test_empty_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            to_month_end(empty_df)


class TestToMonthEndInputTypes:
    def test_accepts_series(self, single_series: pd.Series) -> None:
        result = to_month_end(single_series)
        assert isinstance(result, pd.Series)

    def test_accepts_dataframe(self, monthly_rates: pd.DataFrame) -> None:
        result = to_month_end(monthly_rates)
        assert isinstance(result, pd.DataFrame)
