from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.charts.enhancers.eventplot import plot_eventplot


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def datetime_index() -> pd.DatetimeIndex:
    return pd.date_range("2023-01-31", periods=6, freq="ME")


class TestPlotEventplot:
    def test_single_column(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="v")
        plot_eventplot(ax, datetime_index, series, highlight=[])
        assert len(ax.collections) >= 1

    def test_multi_column(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [1, 2, 3, 4, 5, 6], "b": [6, 5, 4, 3, 2, 1]},
            index=datetime_index,
        )
        plot_eventplot(ax, datetime_index, df, highlight=[])
        assert len(ax.collections) >= 1

    def test_color_override(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3], index=datetime_index[:3], name="v")
        plot_eventplot(ax, datetime_index[:3], series, highlight=[], color="red")
        assert len(ax.collections) >= 1
