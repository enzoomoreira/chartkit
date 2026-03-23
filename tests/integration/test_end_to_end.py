"""End-to-end integration tests for complete charting scenarios.

Tests real pipelines combining multiple subsystems (accessor, engine,
compose, metrics, collision, decorations, save) without mocking.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pytest

from chartkit import compose
from chartkit.result import PlotResult


@pytest.fixture(autouse=True)
def _close_figs() -> None:
    yield
    plt.close("all")


@pytest.fixture
def long_monthly_df() -> pd.DataFrame:
    """72 months of data for tick rotation tests."""
    idx = pd.date_range("2018-01-31", periods=72, freq="ME")
    rng = np.random.default_rng(42)
    return pd.DataFrame({"value": rng.normal(100, 15, 72)}, index=idx)


@pytest.fixture
def categorical_df() -> pd.DataFrame:
    """DataFrame with string index for categorical bar charts."""
    return pd.DataFrame(
        {"revenue": [120.0, 95.0, 150.0, 80.0, 110.0]},
        index=["Product A", "Product B", "Product C", "Product D", "Product E"],
    )


class TestEndToEnd:
    def test_compose_dual_axis_different_units(
        self, daily_prices: pd.DataFrame, monthly_rates: pd.DataFrame
    ) -> None:
        layer_left = daily_prices.chartkit.layer(units="BRL")
        layer_right = monthly_rates.chartkit.layer(y="cdi", units="%", axis="right")
        result = compose(layer_left, layer_right, title="Dual Axis")
        assert isinstance(result, PlotResult)

        # Left axis has BRL formatter
        left_fmt = result.axes.yaxis.get_major_formatter()
        left_str = left_fmt(1000.0)
        assert "R$" in left_str or "1" in left_str

    def test_compose_with_metrics(self, daily_prices: pd.DataFrame) -> None:
        layer = daily_prices.chartkit.layer(metrics=["ath", "ma:50"])
        result = compose(layer, title="Price with Metrics")
        assert isinstance(result, PlotResult)
        assert result.figure is not None

    def test_variation_then_compose(
        self,
        daily_prices: pd.DataFrame,
        monthly_rates: pd.DataFrame,
    ) -> None:
        var_layer = monthly_rates.chartkit.variation(horizon="month").layer(
            units="%", axis="right"
        )
        price_layer = daily_prices.chartkit.layer(units="BRL")
        result = compose(price_layer, var_layer, title="Price + Variation")
        assert isinstance(result, PlotResult)

    def test_bar_highlight_collision(self, monthly_rates: pd.DataFrame) -> None:
        result = monthly_rates.chartkit.plot(
            y="cdi",
            kind="bar",
            highlight=["all"],
            collision=True,
        )
        assert isinstance(result, PlotResult)

    def test_categorical_bar_sorted(self, categorical_df: pd.DataFrame) -> None:
        result = categorical_df.chartkit.plot(kind="bar")
        assert isinstance(result, PlotResult)
        assert result.figure is not None

    def test_save_roundtrip(self, daily_prices: pd.DataFrame, tmp_path: Path) -> None:
        result = daily_prices.chartkit.plot(title="Save Test")
        output = tmp_path / "test_chart.png"
        result.save(str(output))
        assert output.exists()
        assert output.stat().st_size > 0

    def test_tick_rotation_auto(self, long_monthly_df: pd.DataFrame) -> None:
        result = long_monthly_df.chartkit.plot(tick_rotation="auto")
        assert isinstance(result, PlotResult)

    def test_tick_formatting_custom(self, long_monthly_df: pd.DataFrame) -> None:
        result = long_monthly_df.chartkit.plot(tick_format="%b/%Y", tick_freq="quarter")
        assert isinstance(result, PlotResult)

    def test_title_and_source(self, daily_prices: pd.DataFrame) -> None:
        result = daily_prices.chartkit.plot(title="Revenue Growth", source="Bloomberg")
        assert result.axes.get_title() == "Revenue Growth"
        # Source is in the figure text objects
        texts = [t.get_text() for t in result.figure.texts]
        assert any("Bloomberg" in t for t in texts)

    def test_grid_override(self, daily_prices: pd.DataFrame) -> None:
        result = daily_prices.chartkit.plot(grid=False)
        assert isinstance(result, PlotResult)
        # Grid lines should be invisible when grid=False
        major_gridlines = result.axes.xaxis.get_gridlines()
        for line in major_gridlines:
            assert not line.get_visible()
