from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.charts.enhancers.bar import plot_bar, plot_barh
from chartkit.exceptions import ValidationError


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def datetime_index() -> pd.DatetimeIndex:
    return pd.date_range("2023-01-31", periods=6, freq="ME")


@pytest.fixture
def numeric_index() -> pd.Index:
    return pd.Index([1, 2, 3, 4, 5, 6])


@pytest.fixture
def categorical_index() -> pd.Index:
    return pd.Index(["B3", "NYSE", "LSE", "TSE", "HKEX", "SSE"])


# ---------------------------------------------------------------------------
# Bar -- single column
# ---------------------------------------------------------------------------


class TestBarSingleColumn:
    def test_series_creates_one_container(
        self, datetime_index: pd.DatetimeIndex
    ) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="revenue")
        plot_bar(ax, datetime_index, series, highlight=[])
        assert len(ax.containers) == 1
        assert len(ax.containers[0]) == 6

    def test_single_col_dataframe(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame({"revenue": [1, 2, 3, 4, 5, 6]}, index=datetime_index)
        plot_bar(ax, datetime_index, df, highlight=[])
        assert len(ax.containers) == 1

    def test_label_from_series_name(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3], index=datetime_index[:3], name="sales")
        plot_bar(ax, datetime_index[:3], series, highlight=[])
        _, labels = ax.get_legend_handles_labels()
        assert "sales" in labels

    def test_no_label_when_name_is_none(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3], index=datetime_index[:3])
        plot_bar(ax, datetime_index[:3], series, highlight=[])
        _, labels = ax.get_legend_handles_labels()
        assert labels == []


# ---------------------------------------------------------------------------
# Bar -- multi column (grouped)
# ---------------------------------------------------------------------------


class TestBarMultiColumn:
    def test_grouped_bars_created(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [1, 2, 3, 4, 5, 6], "b": [6, 5, 4, 3, 2, 1]},
            index=datetime_index,
        )
        plot_bar(ax, datetime_index, df, highlight=[])
        assert len(ax.containers) == 2

    def test_each_column_has_label(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"revenue": [1, 2, 3, 4, 5, 6], "cost": [6, 5, 4, 3, 2, 1]},
            index=datetime_index,
        )
        plot_bar(ax, datetime_index, df, highlight=[])
        _, labels = ax.get_legend_handles_labels()
        assert "revenue" in labels
        assert "cost" in labels

    def test_three_columns(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {
                "a": [1, 2, 3, 4, 5, 6],
                "b": [2, 3, 4, 5, 6, 7],
                "c": [3, 4, 5, 6, 7, 8],
            },
            index=datetime_index,
        )
        plot_bar(ax, datetime_index, df, highlight=[])
        assert len(ax.containers) == 3

    def test_user_color_override(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [1, 2, 3], "b": [3, 2, 1]},
            index=datetime_index[:3],
        )
        plot_bar(ax, datetime_index[:3], df, highlight=[], color="red")
        for container in ax.containers:
            for patch in container:
                assert patch.get_facecolor()[:3] == pytest.approx(
                    (1.0, 0.0, 0.0), abs=0.01
                )

    def test_numeric_index(self, numeric_index: pd.Index) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [1, 2, 3, 4, 5, 6], "b": [6, 5, 4, 3, 2, 1]},
            index=numeric_index,
        )
        plot_bar(ax, numeric_index, df, highlight=[])
        assert len(ax.containers) == 2

    def test_grouped_bar_offset_symmetry(
        self, datetime_index: pd.DatetimeIndex
    ) -> None:
        """Offsets for grouped bars should be symmetric around the group center."""
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [10, 20, 30, 40, 50, 60], "b": [60, 50, 40, 30, 20, 10]},
            index=datetime_index,
        )
        plot_bar(ax, datetime_index, df, highlight=[])
        # Each container holds bars for one column; widths should be equal
        widths_a = [p.get_width() for p in ax.containers[0]]
        widths_b = [p.get_width() for p in ax.containers[1]]
        assert widths_a[0] == pytest.approx(widths_b[0])
        # Centers of the two groups at the same time point should be symmetric
        for pa, pb in zip(ax.containers[0], ax.containers[1]):
            center = (pa.get_x() + pa.get_width() + pb.get_x()) / 2
            assert pa.get_x() + pa.get_width() == pytest.approx(center, abs=1e-6)


# ---------------------------------------------------------------------------
# Bar -- y_origin
# ---------------------------------------------------------------------------


class TestBarYOrigin:
    def test_zero_includes_zero_positive(
        self, datetime_index: pd.DatetimeIndex
    ) -> None:
        _, ax = plt.subplots()
        series = pd.Series([5, 10, 15, 20, 25, 30], index=datetime_index, name="v")
        plot_bar(ax, datetime_index, series, highlight=[], y_origin="zero")
        ymin, _ = ax.get_ylim()
        assert ymin <= 0

    def test_auto_adjusts_limits(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series(
            [100, 110, 105, 115, 120, 125], index=datetime_index, name="v"
        )
        plot_bar(ax, datetime_index, series, highlight=[], y_origin="auto")
        ymin, _ = ax.get_ylim()
        assert ymin > 0

    def test_invalid_y_origin_raises(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3], index=datetime_index[:3], name="v")
        with pytest.raises(ValidationError, match="y_origin"):
            plot_bar(ax, datetime_index[:3], series, highlight=[], y_origin="invalid")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Bar -- categorical
# ---------------------------------------------------------------------------


class TestBarCategorical:
    def test_sort_ascending(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series(
            [15.2, 22.1, 18.5, 12.3, 9.8, 25.4], index=categorical_index, name="P/L"
        )
        plot_bar(ax, categorical_index, series, highlight=[], sort="ascending")
        heights = [p.get_height() for p in ax.containers[0]]
        assert heights == sorted(heights)

    def test_sort_descending(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series(
            [15.2, 22.1, 18.5, 12.3, 9.8, 25.4], index=categorical_index, name="P/L"
        )
        plot_bar(ax, categorical_index, series, highlight=[], sort="descending")
        heights = [p.get_height() for p in ax.containers[0]]
        assert heights == sorted(heights, reverse=True)

    def test_sort_invalid_raises(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=categorical_index, name="v")
        with pytest.raises(ValidationError, match="sort"):
            plot_bar(ax, categorical_index, series, highlight=[], sort="invalid")

    def test_sort_multi_col_raises(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [1, 2, 3, 4, 5, 6], "b": [6, 5, 4, 3, 2, 1]},
            index=categorical_index,
        )
        with pytest.raises(ValidationError, match="sort"):
            plot_bar(ax, categorical_index, df, highlight=[], sort="ascending")

    def test_color_cycle(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series(
            [15.2, 22.1, 18.5, 12.3, 9.8, 25.4], index=categorical_index, name="P/L"
        )
        plot_bar(ax, categorical_index, series, highlight=[], color="cycle")
        patches = ax.containers[0]
        face_colors = [p.get_facecolor() for p in patches]
        assert face_colors[0] != face_colors[1]

    def test_color_cycle_multi_col_raises(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        df = pd.DataFrame(
            {"a": [1, 2, 3, 4, 5, 6], "b": [6, 5, 4, 3, 2, 1]},
            index=categorical_index,
        )
        with pytest.raises(ValidationError, match="cycle"):
            plot_bar(ax, categorical_index, df, highlight=[], color="cycle")


# ---------------------------------------------------------------------------
# Bar -- highlight
# ---------------------------------------------------------------------------


class TestBarHighlight:
    def test_highlight_with_duplicate_datetime_index(
        self, datetime_index: pd.DatetimeIndex
    ) -> None:
        _, ax = plt.subplots()
        duplicated_index = datetime_index.repeat(2)
        series = pd.Series(range(1, len(duplicated_index) + 1), index=duplicated_index)
        plot_bar(ax, duplicated_index, series, highlight=["last"])
        ax.figure.canvas.draw()

    def test_highlight_all_categorical(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series(
            [15.2, 22.1, 18.5, 12.3, 9.8, 25.4], index=categorical_index, name="P/L"
        )
        plot_bar(ax, categorical_index, series, highlight=["all"])
        ax.figure.canvas.draw()
        assert len(ax.texts) == 6

    def test_highlight_all_with_sort(self, categorical_index: pd.Index) -> None:
        _, ax = plt.subplots()
        series = pd.Series(
            [15.2, 22.1, 18.5, 12.3, 9.8, 25.4], index=categorical_index, name="P/L"
        )
        plot_bar(ax, categorical_index, series, highlight=["all"], sort="descending")
        ax.figure.canvas.draw()
        assert len(ax.texts) == 6


# ---------------------------------------------------------------------------
# Barh (horizontal)
# ---------------------------------------------------------------------------


class TestBarh:
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
