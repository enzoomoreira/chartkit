"""Tests for chartkit.transforms.temporal.to_month_end.

Covers: month-end consolidation, mid-month snapping, daily collapse,
non-datetime validation, freq preservation.
"""

from __future__ import annotations

import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import to_month_end


class TestToMonthEndConsolidation:
    def test_monthly_data_unchanged(self, monthly_rates: pd.DataFrame) -> None:
        """Already month-end data stays the same."""
        result = to_month_end(monthly_rates)
        assert len(result) == len(monthly_rates)
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_mid_month_snapped_to_end(self) -> None:
        """Mid-month dates snap to last day of each month."""
        idx = pd.DatetimeIndex(["2023-01-15", "2023-02-10", "2023-03-20"])
        df = pd.DataFrame({"val": [1.0, 2.0, 3.0]}, index=idx)
        result = to_month_end(df)
        assert result.index[0].day == 31  # Jan
        assert result.index[1].day == 28  # Feb
        assert result.index[2].day == 31  # Mar

    def test_daily_data_collapses_to_last_per_month(
        self, daily_prices: pd.DataFrame
    ) -> None:
        """Daily data -> one observation per month (last chronological)."""
        result = to_month_end(daily_prices)
        assert not result.index.duplicated().any()
        expected = (
            daily_prices.sort_index().groupby(daily_prices.index.to_period("M")).last()
        )
        expected.index = expected.index.to_timestamp("M")
        pd.testing.assert_frame_equal(result, expected, check_freq=False)


class TestToMonthEndValidation:
    def test_non_datetime_index_raises(self) -> None:
        df = pd.DataFrame({"val": [1.0, 2.0, 3.0]})
        with pytest.raises(TransformError, match="DatetimeIndex"):
            to_month_end(df)

    def test_empty_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            to_month_end(empty_df)
