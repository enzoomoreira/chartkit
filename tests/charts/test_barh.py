from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.charts.enhancers.bar import plot_barh
from chartkit.exceptions import ValidationError


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def categorical_index() -> pd.Index:
    return pd.Index(["B3", "NYSE", "LSE", "TSE", "HKEX", "SSE"])


class TestPlotBarh:
    def test_single_column(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series([15, 22, 18, 12, 9, 25], index=categorical_index, name="P/L")
        plot_barh(ax, categorical_index, series, highlight=[])
        assert len(ax.patches) == 6

    def test_multi_column(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"2023": [15, 22, 18, 12, 9, 25], "2024": [17, 20, 19, 14, 11, 23]},
            index=categorical_index,
        )
        plot_barh(ax, categorical_index, df, highlight=[])
        assert len(ax.patches) == 12

    def test_sort_ascending(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series([15, 22, 18, 12, 9, 25], index=categorical_index, name="v")
        plot_barh(ax, categorical_index, series, highlight=[], sort="ascending")
        widths = [p.get_width() for p in ax.patches]
        assert widths == sorted(widths)

    def test_sort_multi_col_raises(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [1, 2, 3, 4, 5, 6], "b": [6, 5, 4, 3, 2, 1]},
            index=categorical_index,
        )
        with pytest.raises(ValidationError, match="sort"):
            plot_barh(ax, categorical_index, df, highlight=[], sort="ascending")

    def test_y_origin_zero(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series([5, 10, 15, 20, 25, 30], index=categorical_index, name="v")
        plot_barh(ax, categorical_index, series, highlight=[], y_origin="zero")
        xmin, _ = ax.get_xlim()
        assert xmin <= 0

    def test_color_override(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series([15, 22, 18, 12, 9, 25], index=categorical_index, name="v")
        plot_barh(ax, categorical_index, series, highlight=[], color="red")
        for patch in ax.patches:
            assert patch.get_facecolor()[:3] == pytest.approx((1.0, 0.0, 0.0), abs=0.01)
