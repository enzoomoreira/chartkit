from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from chartkit.charts.enhancers.stacked_bar import plot_stacked_bar


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def datetime_index() -> pd.DatetimeIndex:
    return pd.date_range("2023-01-31", periods=6, freq="ME")


@pytest.fixture
def categorical_index() -> pd.Index:
    return pd.Index(["B3", "NYSE", "LSE", "TSE", "HKEX", "SSE"])


class TestStackedBar:
    def test_single_series_fallback(self, datetime_index: pd.DatetimeIndex) -> None:
        """A single Series should render as a normal bar chart (1 container)."""
        _, ax = plt.subplots()
        series = pd.Series([10, 20, 30, 40, 50, 60], index=datetime_index, name="rev")
        plot_stacked_bar(ax, datetime_index, series, highlight=[])
        assert len(ax.containers) == 1
        assert len(ax.containers[0]) == 6

    def test_multi_col_stacking(self, datetime_index: pd.DatetimeIndex) -> None:
        """Multiple columns produce one container per column, all stacked."""
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [10, 20, 30, 40, 50, 60], "b": [5, 10, 15, 20, 25, 30]},
            index=datetime_index,
        )
        plot_stacked_bar(ax, datetime_index, df, highlight=[])
        assert len(ax.containers) == 2

    def test_nan_filled_with_zero(self, datetime_index: pd.DatetimeIndex) -> None:
        """NaN values should be filled with zero so stacking does not break."""
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [10, np.nan, 30, 40, 50, 60], "b": [5, 10, np.nan, 20, 25, 30]},
            index=datetime_index,
        )
        plot_stacked_bar(ax, datetime_index, df, highlight=[])
        # All 12 patches drawn (6 per column, NaN becomes 0-height)
        assert len(ax.patches) == 12

    def test_bottom_accumulation(self, datetime_index: pd.DatetimeIndex) -> None:
        """Second column bars should sit on top of the first."""
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [10, 20, 30, 40, 50, 60], "b": [5, 5, 5, 5, 5, 5]},
            index=datetime_index,
        )
        plot_stacked_bar(ax, datetime_index, df, highlight=[])
        # Bottom of second column patches = height of first column patches
        for pa, pb in zip(ax.containers[0], ax.containers[1]):
            assert pb.get_y() == pytest.approx(pa.get_height(), abs=0.01)

    def test_highlight_shows_total(self, datetime_index: pd.DatetimeIndex) -> None:
        """Highlight should annotate total (sum of columns), not individual values."""
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [10, 20, 30, 40, 50, 60], "b": [5, 10, 15, 20, 25, 30]},
            index=datetime_index,
        )
        plot_stacked_bar(ax, datetime_index, df, highlight=["last"])
        ax.figure.canvas.draw()
        assert len(ax.texts) >= 1

    def test_categorical_index(self, categorical_index: pd.Index) -> None:
        """Stacked bar should work with categorical (string) indices."""
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [10, 20, 30, 40, 50, 60], "b": [5, 10, 15, 20, 25, 30]},
            index=categorical_index,
        )
        plot_stacked_bar(ax, categorical_index, df, highlight=[])
        assert len(ax.containers) == 2
