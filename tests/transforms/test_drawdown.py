"""Tests for chartkit.transforms.temporal.drawdown.

Covers: known-value correctness, monotonic series, multi-column,
non-positive values, NaN gaps in price data.
"""

from __future__ import annotations

import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import drawdown


class TestDrawdownKnownValues:
    def test_known_drawdown(self, known_drawdown_data: pd.DataFrame) -> None:
        """[100, 120, 90, 110] -> [0%, 0%, -25%, -8.33%]."""
        result = drawdown(known_drawdown_data)
        vals = result["price"]
        assert vals.iloc[0] == pytest.approx(0.0)
        assert vals.iloc[1] == pytest.approx(0.0)
        assert vals.iloc[2] == pytest.approx((90 / 120 - 1) * 100)
        assert vals.iloc[3] == pytest.approx((110 / 120 - 1) * 100)

    def test_monotonic_increasing_all_zero(self) -> None:
        """Always at peak -> drawdown is zero everywhere."""
        idx = pd.date_range("2023-01-31", periods=4, freq="ME")
        df = pd.DataFrame({"price": [100.0, 110.0, 120.0, 130.0]}, index=idx)
        result = drawdown(df)
        assert (result["price"] == 0.0).all()

    def test_monotonic_decreasing(self) -> None:
        """Declining prices accumulate deeper drawdown."""
        idx = pd.date_range("2023-01-31", periods=4, freq="ME")
        df = pd.DataFrame({"price": [100.0, 90.0, 80.0, 70.0]}, index=idx)
        result = drawdown(df)
        assert result["price"].iloc[0] == pytest.approx(0.0)
        assert result["price"].iloc[1] == pytest.approx((90 / 100 - 1) * 100)
        assert result["price"].iloc[-1] == pytest.approx((70 / 100 - 1) * 100)


class TestDrawdownMultiColumn:
    def test_multi_column_drawdown(self, daily_prices: pd.DataFrame) -> None:
        """Drawdown works on DataFrame and returns same columns."""
        result = drawdown(daily_prices)
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == list(daily_prices.columns)
        # All drawdown values should be <= 0
        assert (result <= 0.0).all().all()


class TestDrawdownValidation:
    def test_starts_negative_raises(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"price": [-5.0, -3.0, 10.0]}, index=idx)
        with pytest.raises(TransformError, match="strictly positive"):
            drawdown(df)

    def test_starts_zero_raises(self) -> None:
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"price": [0.0, 10.0, 20.0]}, index=idx)
        with pytest.raises(TransformError, match="strictly positive"):
            drawdown(df)


class TestDrawdownEdgeCases:
    def test_single_value_is_zero(self) -> None:
        idx = pd.date_range("2023-01-31", periods=1, freq="ME")
        df = pd.DataFrame({"price": [100.0]}, index=idx)
        result = drawdown(df)
        assert result["price"].iloc[0] == pytest.approx(0.0)

    def test_nan_gaps_in_price_data(self, gapped_prices: pd.DataFrame) -> None:
        """NaN gaps in prices propagate as NaN in drawdown (cummax ignores NaN)."""
        result = drawdown(gapped_prices)
        # Where input is NaN, drawdown should also be NaN
        nan_positions = gapped_prices["price"].isna()
        assert result["price"][nan_positions].isna().all()
        # Non-NaN positions should be <= 0
        non_nan = result["price"].dropna()
        assert (non_nan <= 0.0).all()
