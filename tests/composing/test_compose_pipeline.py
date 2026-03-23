"""Compose pipeline tests: dual-axis rendering, formatters, legend, validation, extract_data."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit._internal.extraction import extract_plot_data
from chartkit._internal.pipeline import apply_legend  # noqa: F811
from chartkit.composing.compose import (
    _apply_axis_formatter,
    _validate_layers,
    compose,
)
from chartkit.composing.layer import Layer
from chartkit.exceptions import ValidationError
from chartkit.result import PlotResult


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


def _make_layer(
    n: int = 5,
    cols: list[str] | None = None,
    axis: str = "left",
    **kwargs,
) -> Layer:
    cols = cols or ["val"]
    idx = pd.date_range("2023-01-01", periods=n, freq="ME")
    data = {c: range(1, n + 1) for c in cols}
    df = pd.DataFrame(data, index=idx)
    return Layer(df=df, axis=axis, **kwargs)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_no_layers_raises(self) -> None:
        with pytest.raises(ValidationError, match="at least one layer"):
            compose()

    def test_all_right_raises(self) -> None:
        with pytest.raises(ValidationError, match="axis='right'"):
            compose(_make_layer(axis="right"))

    def test_all_right_multiple_raises(self) -> None:
        with pytest.raises(ValidationError, match="axis='right'"):
            _validate_layers(
                (_make_layer(axis="right"), _make_layer(axis="right")), None
            )

    def test_invalid_legend_type_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid plot parameters"):
            compose(_make_layer(), legend=1)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Compose rendering
# ---------------------------------------------------------------------------


class TestComposeRendering:
    def test_single_layer_returns_plot_result(self) -> None:
        result = compose(_make_layer())
        assert isinstance(result, PlotResult)
        assert result.fig is not None
        assert result.ax is not None

    def test_dual_axis(self) -> None:
        left = _make_layer(cols=["price"])
        right = _make_layer(cols=["rate"], axis="right")
        result = compose(left, right)
        assert result.fig is not None

    def test_multiple_left_layers(self) -> None:
        l1 = _make_layer(cols=["a"])
        l2 = _make_layer(cols=["b"])
        result = compose(l1, l2)
        assert result.fig is not None

    def test_title_applied(self) -> None:
        result = compose(_make_layer(), title="My Title")
        assert result.ax.get_title() == "My Title"

    def test_no_title_is_empty(self) -> None:
        result = compose(_make_layer())
        assert result.ax.get_title() == ""

    def test_figsize_override(self) -> None:
        result = compose(_make_layer(), figsize=(4.0, 3.0))
        w, h = result.fig.get_size_inches()
        assert abs(w - 4.0) < 0.1
        assert abs(h - 3.0) < 0.1

    def test_units_applied_on_axis(self) -> None:
        layer = _make_layer(units="%")
        result = compose(layer)
        formatter = result.ax.yaxis.get_major_formatter()
        assert formatter is not None


# ---------------------------------------------------------------------------
# Axis formatter
# ---------------------------------------------------------------------------


class TestAxisFormatter:
    def test_none_units_does_nothing(self) -> None:
        _, ax = plt.subplots()
        applied: dict = {"left": None, "right": None}
        _apply_axis_formatter(ax, "left", None, applied)
        assert applied["left"] is None

    def test_valid_units_applied(self) -> None:
        _, ax = plt.subplots()
        applied: dict = {"left": None, "right": None}
        _apply_axis_formatter(ax, "left", "%", applied)
        assert applied["left"] == "%"

    def test_conflicting_units_keeps_first(self) -> None:
        _, ax = plt.subplots()
        applied: dict = {"left": None, "right": None}
        _apply_axis_formatter(ax, "left", "BRL", applied)
        _apply_axis_formatter(ax, "left", "USD", applied)
        assert applied["left"] == "BRL"

    def test_left_and_right_independent(self) -> None:
        _, ax = plt.subplots()
        applied: dict = {"left": None, "right": None}
        _apply_axis_formatter(ax, "left", "%", applied)
        _apply_axis_formatter(ax, "right", "BRL", applied)
        assert applied["left"] == "%"
        assert applied["right"] == "BRL"


# ---------------------------------------------------------------------------
# Composed legend
# ---------------------------------------------------------------------------


class TestComposedLegend:
    def test_auto_hidden_single_label(self) -> None:
        _, ax = plt.subplots()
        ax.plot([1, 2], [1, 2], label="series_a")
        apply_legend(ax, None, legend=None)
        assert ax.get_legend() is None

    def test_auto_shown_multiple_labels(self) -> None:
        _, ax = plt.subplots()
        ax.plot([1, 2], [1, 2], label="series_a")
        ax.plot([1, 2], [2, 3], label="series_b")
        apply_legend(ax, None, legend=None)
        legend = ax.get_legend()
        assert legend is not None
        texts = [t.get_text() for t in legend.get_texts()]
        assert texts == ["series_a", "series_b"]

    def test_force_false_suppresses(self) -> None:
        _, ax = plt.subplots()
        ax.plot([1, 2], [1, 2], label="a")
        ax.plot([1, 2], [2, 3], label="b")
        apply_legend(ax, None, legend=False)
        assert ax.get_legend() is None

    def test_consolidates_dual_axis_labels(self) -> None:
        fig, ax_left = plt.subplots()
        ax_right = ax_left.twinx()
        ax_left.plot([1, 2], [1, 2], label="left_series")
        ax_right.plot([1, 2], [10, 20], label="right_series")
        apply_legend(ax_left, ax_right, legend=None)

        legend = ax_left.get_legend()
        assert legend is not None
        texts = [t.get_text() for t in legend.get_texts()]
        assert "left_series" in texts
        assert "right_series" in texts

    def test_right_axis_legend_removed(self) -> None:
        fig, ax_left = plt.subplots()
        ax_right = ax_left.twinx()
        ax_left.plot([1, 2], [1, 2], label="left")
        ax_right.plot([1, 2], [10, 20], label="right")
        ax_right.legend()
        assert ax_right.get_legend() is not None

        apply_legend(ax_left, ax_right, legend=None)
        assert ax_right.get_legend() is None


# ---------------------------------------------------------------------------
# Extract data
# ---------------------------------------------------------------------------


class TestExtractData:
    @pytest.fixture
    def sample_df(self) -> pd.DataFrame:
        idx = pd.date_range("2023-01-01", periods=3, freq="ME")
        return pd.DataFrame(
            {"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0], "cat": ["x", "y", "z"]},
            index=idx,
        )

    def test_x_none_uses_index(self, sample_df: pd.DataFrame) -> None:
        x_data, _ = extract_plot_data(sample_df, x=None, y=None)
        pd.testing.assert_index_equal(x_data, sample_df.index)

    def test_x_column(self, sample_df: pd.DataFrame) -> None:
        x_data, _ = extract_plot_data(sample_df, x="a", y=None)
        pd.testing.assert_series_equal(x_data, sample_df["a"])

    def test_y_none_selects_numeric(self, sample_df: pd.DataFrame) -> None:
        _, y_data = extract_plot_data(sample_df, x=None, y=None)
        assert isinstance(y_data, pd.DataFrame)
        assert list(y_data.columns) == ["a", "b"]

    def test_y_single_string(self, sample_df: pd.DataFrame) -> None:
        _, y_data = extract_plot_data(sample_df, x=None, y="a")
        assert isinstance(y_data, pd.Series)
        assert y_data.name == "a"
