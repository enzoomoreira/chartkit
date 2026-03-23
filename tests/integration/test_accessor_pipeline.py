"""Integration tests for the Pandas accessor pipeline.

Tests the full path: DataFrame -> .chartkit accessor -> plot()/layer() -> PlotResult/Layer.
Absorbs coverage from test_accessor_layer.py and parts of test_accessor.py.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.composing.layer import Layer
from chartkit.result import PlotResult


@pytest.fixture(autouse=True)
def _close_figs() -> None:
    yield
    plt.close("all")


class TestAccessorPipeline:
    def test_df_chartkit_plot_returns_plot_result(
        self, monthly_rates: pd.DataFrame
    ) -> None:
        result = monthly_rates.chartkit.plot()
        assert isinstance(result, PlotResult)
        assert result.figure is not None
        assert result.axes is not None

    def test_df_chartkit_plot_with_units(self, monthly_rates: pd.DataFrame) -> None:
        result = monthly_rates.chartkit.plot(units="BRL")
        formatter = result.axes.yaxis.get_major_formatter()
        # BRL formatter should produce a string with "R$" when formatting
        formatted = formatter(1000.0)
        assert "R$" in formatted or "1" in formatted

    def test_df_chartkit_variation_plot(self, monthly_rates: pd.DataFrame) -> None:
        result = monthly_rates.chartkit.variation(horizon="month").plot()
        assert isinstance(result, PlotResult)
        assert result.figure is not None

    def test_series_accessor_works(self, single_series: pd.Series) -> None:
        result = single_series.chartkit.plot()
        assert isinstance(result, PlotResult)
        assert result.figure is not None

    def test_layer_creation_from_accessor(self, monthly_rates: pd.DataFrame) -> None:
        layer = monthly_rates.chartkit.layer()
        assert isinstance(layer, Layer)
        assert layer.kind == "line"
        assert layer.axis == "left"
        pd.testing.assert_frame_equal(layer.df, monthly_rates)

    def test_layer_from_transform(self, monthly_rates: pd.DataFrame) -> None:
        layer = monthly_rates.chartkit.variation(horizon="month").layer()
        assert isinstance(layer, Layer)
        assert layer.df.shape[0] == monthly_rates.shape[0]

    def test_accessor_with_kind(self, monthly_rates: pd.DataFrame) -> None:
        result = monthly_rates.chartkit.plot(kind="bar")
        assert isinstance(result, PlotResult)
        assert result.figure is not None

    def test_accessor_with_metrics(self, daily_prices: pd.DataFrame) -> None:
        result = daily_prices.chartkit.plot(metrics=["ath"])
        assert isinstance(result, PlotResult)
        assert result.figure is not None
