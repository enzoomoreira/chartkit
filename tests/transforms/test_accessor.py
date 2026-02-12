from __future__ import annotations

import pandas as pd

from chartkit.transforms.accessor import TransformAccessor
from chartkit.transforms.temporal import (
    accum,
    diff,
    drawdown,
    normalize,
    variation,
    zscore,
)


class TestTransformAccessorChaining:
    def test_variation_returns_accessor(self, monthly_rates: pd.DataFrame) -> None:
        result = TransformAccessor(monthly_rates).variation()
        assert isinstance(result, TransformAccessor)

    def test_chaining_variation_then_normalize(
        self, monthly_rates: pd.DataFrame
    ) -> None:
        result = TransformAccessor(monthly_rates).diff().normalize(base=100)
        assert isinstance(result, TransformAccessor)
        assert not result.df.empty

    def test_df_property_returns_dataframe(self, monthly_rates: pd.DataFrame) -> None:
        accessor = TransformAccessor(monthly_rates)
        assert isinstance(accessor.df, pd.DataFrame)

    def test_series_converted_to_dataframe(self, single_series: pd.Series) -> None:
        accessor = TransformAccessor(single_series)
        assert isinstance(accessor.df, pd.DataFrame)

    def test_repr_format(self, monthly_rates: pd.DataFrame) -> None:
        accessor = TransformAccessor(monthly_rates)
        r = repr(accessor)
        assert "TransformAccessor" in r
        assert "rows" in r
        assert "cols" in r


class TestTransformAccessorDelegation:
    def test_variation_delegates(self, monthly_rates: pd.DataFrame) -> None:
        result = TransformAccessor(monthly_rates).variation(horizon="month").df
        expected = variation(monthly_rates, horizon="month")
        pd.testing.assert_frame_equal(result, expected)

    def test_accum_delegates(self, monthly_rates: pd.DataFrame) -> None:
        result = TransformAccessor(monthly_rates).accum(window=3).df
        expected = accum(monthly_rates, window=3)
        pd.testing.assert_frame_equal(result, expected)

    def test_diff_delegates(self, monthly_rates: pd.DataFrame) -> None:
        result = TransformAccessor(monthly_rates).diff().df
        expected = diff(monthly_rates)
        pd.testing.assert_frame_equal(result, expected)

    def test_normalize_delegates(self, monthly_rates: pd.DataFrame) -> None:
        result = TransformAccessor(monthly_rates).normalize(base=100).df
        expected = normalize(monthly_rates, base=100)
        pd.testing.assert_frame_equal(result, expected)

    def test_drawdown_delegates(self, daily_prices: pd.DataFrame) -> None:
        result = TransformAccessor(daily_prices).drawdown().df
        expected = drawdown(daily_prices)
        pd.testing.assert_frame_equal(result, expected)

    def test_zscore_delegates(self, monthly_rates: pd.DataFrame) -> None:
        result = TransformAccessor(monthly_rates).zscore().df
        expected = zscore(monthly_rates)
        pd.testing.assert_frame_equal(result, expected)
