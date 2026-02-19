from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.charts.enhancers.area import plot_area


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def datetime_index() -> pd.DatetimeIndex:
    return pd.date_range("2023-01-31", periods=6, freq="ME")


class TestPlotArea:
    def test_single_column(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="v")
        plot_area(ax, datetime_index, series, highlight=[])
        # fill_between creates PolyCollection
        assert len(ax.collections) >= 1

    def test_two_columns_fills_between(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"lower": [1, 2, 3, 4, 5, 6], "upper": [2, 3, 4, 5, 6, 7]},
            index=datetime_index,
        )
        plot_area(ax, datetime_index, df, highlight=[])
        # 1 fill between pair + 2 contour lines
        assert len(ax.collections) == 1
        assert len(ax.lines) == 2

    def test_three_columns_fills_from_zero(
        self, datetime_index: pd.DatetimeIndex
    ) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [1, 2, 3, 4, 5, 6], "b": [6, 5, 4, 3, 2, 1], "c": [3, 3, 3, 3, 3, 3]},
            index=datetime_index,
        )
        plot_area(ax, datetime_index, df, highlight=[])
        # 3 fills from zero + 3 contour lines
        assert len(ax.collections) >= 3

    def test_alpha_kwarg(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="v")
        plot_area(ax, datetime_index, series, highlight=[], alpha=0.5)
        coll = ax.collections[0]
        assert coll.get_alpha() == pytest.approx(0.5)

    def test_highlight_single_column(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="v")
        plot_area(ax, datetime_index, series, highlight=["last"])
        ax.figure.canvas.draw()
        assert len(ax.texts) >= 1

    def test_labels_set(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"revenue": [1, 2, 3], "cost": [3, 2, 1]},
            index=datetime_index[:3],
        )
        plot_area(ax, datetime_index[:3], df, highlight=[])
        _, labels = ax.get_legend_handles_labels()
        assert "revenue" in labels
        assert "cost" in labels
