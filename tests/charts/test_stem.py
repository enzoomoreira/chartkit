from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.charts.enhancers.stem import plot_stem


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def datetime_index() -> pd.DatetimeIndex:
    return pd.date_range("2023-01-31", periods=6, freq="ME")


class TestPlotStem:
    def test_series_renders(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="v")
        plot_stem(ax, datetime_index, series, highlight=[])
        assert len(ax.containers) == 1

    def test_dataframe_renders(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [1, 2, 3, 4, 5, 6], "b": [6, 5, 4, 3, 2, 1]},
            index=datetime_index,
        )
        plot_stem(ax, datetime_index, df, highlight=[])
        assert len(ax.containers) == 2

    def test_color_override(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3], index=datetime_index[:3], name="v")
        plot_stem(ax, datetime_index[:3], series, highlight=[], color="red")
        container = ax.containers[0]
        # Markerline should be red
        assert container.markerline.get_color() == "red"

    def test_labels_set(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"revenue": [1, 2, 3], "cost": [3, 2, 1]},
            index=datetime_index[:3],
        )
        plot_stem(ax, datetime_index[:3], df, highlight=[])
        _, labels = ax.get_legend_handles_labels()
        assert "revenue" in labels
        assert "cost" in labels

    def test_highlight_single_column(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="v")
        plot_stem(ax, datetime_index, series, highlight=["last"])
        ax.figure.canvas.draw()
        assert len(ax.texts) >= 1
