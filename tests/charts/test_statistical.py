from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from chartkit.charts.enhancers.statistical import plot_boxplot, plot_violinplot


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def data_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {"a": rng.normal(0, 1, 100), "b": rng.normal(2, 1.5, 100)},
    )


class TestPlotBoxplot:
    def test_single_column(self, data_df: pd.DataFrame) -> None:
        _, ax = plt.subplots()
        series = data_df["a"]
        series.name = "a"
        plot_boxplot(ax, data_df.index, series, highlight=[])
        assert len(ax.patches) >= 1

    def test_multi_column(self, data_df: pd.DataFrame) -> None:
        _, ax = plt.subplots()
        plot_boxplot(ax, data_df.index, data_df, highlight=[])
        assert len(ax.patches) >= 2

    def test_color_override(self, data_df: pd.DataFrame) -> None:
        _, ax = plt.subplots()
        series = data_df["a"]
        series.name = "a"
        plot_boxplot(ax, data_df.index, series, highlight=[], color="red")
        for patch in ax.patches:
            fc = patch.get_facecolor()
            assert fc[0] == pytest.approx(1.0, abs=0.01)  # red channel

    def test_tick_labels(self, data_df: pd.DataFrame) -> None:
        _, ax = plt.subplots()
        plot_boxplot(ax, data_df.index, data_df, highlight=[])
        labels = [t.get_text() for t in ax.get_xticklabels()]
        assert "a" in labels
        assert "b" in labels


class TestPlotViolinplot:
    def test_single_column(self, data_df: pd.DataFrame) -> None:
        _, ax = plt.subplots()
        series = data_df["a"]
        series.name = "a"
        plot_violinplot(ax, data_df.index, series, highlight=[])
        # violinplot creates PolyCollections
        assert len(ax.collections) >= 1

    def test_multi_column(self, data_df: pd.DataFrame) -> None:
        _, ax = plt.subplots()
        plot_violinplot(ax, data_df.index, data_df, highlight=[])
        assert len(ax.collections) >= 2

    def test_color_override(self, data_df: pd.DataFrame) -> None:
        _, ax = plt.subplots()
        series = data_df["a"]
        series.name = "a"
        plot_violinplot(ax, data_df.index, series, highlight=[], color="blue")
        assert len(ax.collections) >= 1

    def test_tick_labels(self, data_df: pd.DataFrame) -> None:
        _, ax = plt.subplots()
        plot_violinplot(ax, data_df.index, data_df, highlight=[])
        labels = [t.get_text() for t in ax.get_xticklabels()]
        assert "a" in labels
        assert "b" in labels
