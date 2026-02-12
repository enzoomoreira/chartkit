from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.composing.layer import Layer


@pytest.fixture
def sample_df() -> pd.DataFrame:
    idx = pd.date_range("2023-01-31", periods=12, freq="ME")
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {"price": rng.normal(100, 10, 12), "volume": rng.normal(1000, 100, 12)},
        index=idx,
    )


class TestChartingAccessorLayer:
    def test_returns_layer(self, sample_df: pd.DataFrame) -> None:
        layer = sample_df.chartkit.layer()
        assert isinstance(layer, Layer)

    def test_defaults(self, sample_df: pd.DataFrame) -> None:
        layer = sample_df.chartkit.layer()
        assert layer.kind == "line"
        assert layer.axis == "left"
        assert layer.x is None
        assert layer.y is None

    def test_explicit_params(self, sample_df: pd.DataFrame) -> None:
        layer = sample_df.chartkit.layer(
            kind="bar",
            y="price",
            units="BRL",
            axis="right",
        )
        assert layer.kind == "bar"
        assert layer.y == "price"
        assert layer.units == "BRL"
        assert layer.axis == "right"

    def test_kwargs_forwarded(self, sample_df: pd.DataFrame) -> None:
        layer = sample_df.chartkit.layer(color="red", linewidth=2)
        assert layer.kwargs["color"] == "red"
        assert layer.kwargs["linewidth"] == 2

    def test_dataframe_preserved(self, sample_df: pd.DataFrame) -> None:
        layer = sample_df.chartkit.layer()
        pd.testing.assert_frame_equal(layer.df, sample_df)


class TestTransformAccessorLayer:
    def test_returns_layer(self, sample_df: pd.DataFrame) -> None:
        layer = sample_df.chartkit.variation(horizon="month").layer()
        assert isinstance(layer, Layer)

    def test_transformed_data(self, sample_df: pd.DataFrame) -> None:
        layer = sample_df.chartkit.variation(horizon="month").layer()
        assert layer.df.shape[0] == sample_df.shape[0]

    def test_explicit_params(self, sample_df: pd.DataFrame) -> None:
        layer = sample_df.chartkit.variation().layer(
            kind="bar",
            units="%",
            axis="right",
        )
        assert layer.kind == "bar"
        assert layer.units == "%"
        assert layer.axis == "right"

    def test_kwargs_forwarded(self, sample_df: pd.DataFrame) -> None:
        layer = sample_df.chartkit.variation().layer(color="blue")
        assert layer.kwargs["color"] == "blue"
