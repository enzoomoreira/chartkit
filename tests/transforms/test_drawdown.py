from __future__ import annotations

import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import drawdown


class TestDrawdownCorrectness:
    def test_known_drawdown(self, known_drawdown_data: pd.DataFrame) -> None:
        result = drawdown(known_drawdown_data)
        vals = result["price"]
        assert vals.iloc[0] == pytest.approx(0.0)
        assert vals.iloc[1] == pytest.approx(0.0)
        assert vals.iloc[2] == pytest.approx((90 / 120 - 1) * 100)
        assert vals.iloc[3] == pytest.approx((110 / 120 - 1) * 100)

    def test_monotonic_increasing(self) -> None:
        idx = pd.date_range("2023-01-31", periods=4, freq="ME")
        df = pd.DataFrame({"price": [100.0, 110.0, 120.0, 130.0]}, index=idx)
        result = drawdown(df)
        # Always at peak -> all zeros
        assert (result["price"] == 0.0).all()

    def test_monotonic_decreasing(self) -> None:
        idx = pd.date_range("2023-01-31", periods=4, freq="ME")
        df = pd.DataFrame({"price": [100.0, 90.0, 80.0, 70.0]}, index=idx)
        result = drawdown(df)
        assert result["price"].iloc[0] == pytest.approx(0.0)
        assert result["price"].iloc[1] == pytest.approx((90 / 100 - 1) * 100)
        assert result["price"].iloc[-1] == pytest.approx((70 / 100 - 1) * 100)


class TestDrawdownValidation:
    def test_starts_negative_raises(self) -> None:
        # cummax starts at -5 (<=0) -> raises
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"price": [-5.0, -3.0, 10.0]}, index=idx)
        with pytest.raises(TransformError, match="strictly positive"):
            drawdown(df)

    def test_starts_zero_raises(self) -> None:
        # cummax starts at 0 (<=0) -> raises
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"price": [0.0, 10.0, 20.0]}, index=idx)
        with pytest.raises(TransformError, match="strictly positive"):
            drawdown(df)


class TestDrawdownInputTypes:
    def test_accepts_series(self) -> None:
        idx = pd.date_range("2023-01-31", periods=4, freq="ME")
        s = pd.Series([100.0, 120.0, 90.0, 110.0], index=idx, name="price")
        result = drawdown(s)
        assert isinstance(result, pd.Series)

    def test_accepts_dataframe(self, daily_prices: pd.DataFrame) -> None:
        result = drawdown(daily_prices)
        assert isinstance(result, pd.DataFrame)


class TestDrawdownEdgeCases:
    def test_empty_raises(self, empty_df: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="empty"):
            drawdown(empty_df)

    def test_single_value(self) -> None:
        idx = pd.date_range("2023-01-31", periods=1, freq="ME")
        df = pd.DataFrame({"price": [100.0]}, index=idx)
        result = drawdown(df)
        assert result["price"].iloc[0] == pytest.approx(0.0)
