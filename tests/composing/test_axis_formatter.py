from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from chartkit.composing.compose import _apply_axis_formatter


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


class TestApplyAxisFormatter:
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

    def test_duplicate_same_units_no_error(self) -> None:
        _, ax = plt.subplots()
        applied: dict = {"left": None, "right": None}
        _apply_axis_formatter(ax, "left", "BRL", applied)
        _apply_axis_formatter(ax, "left", "BRL", applied)
        assert applied["left"] == "BRL"

    def test_conflicting_units_warns_keeps_first(self) -> None:
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
