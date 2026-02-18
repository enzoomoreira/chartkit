from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.charts.enhancers.pie import plot_pie
from chartkit.exceptions import ValidationError


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def categorical_index() -> pd.Index:
    return pd.Index(["Equity", "Fixed Income", "Real Estate", "Cash"])


class TestPlotPie:
    def test_series_renders(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series([40, 30, 20, 10], index=categorical_index, name="allocation")
        plot_pie(ax, categorical_index, series, highlight=[])
        assert len(ax.patches) == 4

    def test_single_col_dataframe(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame({"allocation": [40, 30, 20, 10]}, index=categorical_index)
        plot_pie(ax, categorical_index, df, highlight=[])
        assert len(ax.patches) == 4

    def test_multi_col_raises(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [40, 30, 20, 10], "b": [10, 20, 30, 40]},
            index=categorical_index,
        )
        with pytest.raises(ValidationError, match="single-column"):
            plot_pie(ax, categorical_index, df, highlight=[])

    def test_labels_from_index(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series([40, 30, 20, 10], index=categorical_index, name="allocation")
        plot_pie(ax, categorical_index, series, highlight=[])
        text_labels = [t.get_text() for t in ax.texts]
        assert "Equity" in text_labels
        assert "Cash" in text_labels

    def test_equal_aspect(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series([40, 30, 20, 10], index=categorical_index, name="allocation")
        plot_pie(ax, categorical_index, series, highlight=[])
        assert ax.get_aspect() == 1.0
