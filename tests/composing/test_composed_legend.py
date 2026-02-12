from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from chartkit.composing.compose import _apply_composed_legend


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


class TestApplyComposedLegend:
    def test_auto_hidden_single_label(self) -> None:
        _, ax = plt.subplots()
        ax.plot([1, 2], [1, 2], label="series_a")
        _apply_composed_legend(ax, None, legend=None)
        assert ax.get_legend() is None

    def test_auto_shown_multiple_labels(self) -> None:
        _, ax = plt.subplots()
        ax.plot([1, 2], [1, 2], label="series_a")
        ax.plot([1, 2], [2, 3], label="series_b")
        _apply_composed_legend(ax, None, legend=None)
        legend = ax.get_legend()
        assert legend is not None
        texts = [t.get_text() for t in legend.get_texts()]
        assert texts == ["series_a", "series_b"]

    def test_force_true_single_label(self) -> None:
        _, ax = plt.subplots()
        ax.plot([1, 2], [1, 2], label="only")
        _apply_composed_legend(ax, None, legend=True)
        assert ax.get_legend() is not None

    def test_force_false_suppresses(self) -> None:
        _, ax = plt.subplots()
        ax.plot([1, 2], [1, 2], label="a")
        ax.plot([1, 2], [2, 3], label="b")
        _apply_composed_legend(ax, None, legend=False)
        assert ax.get_legend() is None

    def test_consolidates_right_axis_labels(self) -> None:
        fig, ax_left = plt.subplots()
        ax_right = ax_left.twinx()
        ax_left.plot([1, 2], [1, 2], label="left_series")
        ax_right.plot([1, 2], [10, 20], label="right_series")
        _apply_composed_legend(ax_left, ax_right, legend=None)

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

        _apply_composed_legend(ax_left, ax_right, legend=None)
        assert ax_right.get_legend() is None

    def test_no_labels_no_legend(self) -> None:
        _, ax = plt.subplots()
        ax.plot([1, 2], [1, 2])
        _apply_composed_legend(ax, None, legend=None)
        assert ax.get_legend() is None
