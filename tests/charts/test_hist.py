from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.charts.enhancers.hist import plot_hist


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def datetime_index() -> pd.DatetimeIndex:
    return pd.date_range("2023-01-31", periods=50, freq="ME")


class TestPlotHist:
    def test_single_column(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series(range(50), index=datetime_index, name="v")
        plot_hist(ax, datetime_index, series, highlight=[])
        assert len(ax.patches) > 0

    def test_multi_column(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": range(50), "b": range(50, 100)},
            index=datetime_index,
        )
        plot_hist(ax, datetime_index, df, highlight=[])
        assert len(ax.patches) > 0

    def test_stacked(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": range(50), "b": range(50, 100)},
            index=datetime_index,
        )
        plot_hist(ax, datetime_index, df, highlight=[], stacked=True)
        assert len(ax.patches) > 0

    def test_bins_kwarg(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series(range(50), index=datetime_index, name="v")
        plot_hist(ax, datetime_index, series, highlight=[], bins=5)
        assert len(ax.patches) == 5

    def test_color_override(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series(range(50), index=datetime_index, name="v")
        plot_hist(ax, datetime_index, series, highlight=[], color="red")
        for patch in ax.patches:
            assert patch.get_facecolor()[:3] == pytest.approx((1.0, 0.0, 0.0), abs=0.01)

    def test_labels_set(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"revenue": range(50), "cost": range(50, 100)},
            index=datetime_index,
        )
        plot_hist(ax, datetime_index, df, highlight=[])
        _, labels = ax.get_legend_handles_labels()
        assert "revenue" in labels
        assert "cost" in labels
