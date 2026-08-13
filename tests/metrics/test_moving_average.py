"""Tests for the moving average overlay, including its min_periods contract."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import ValidationError
from chartkit.overlays.moving_average import add_moving_average
from chartkit.settings import configure, get_config


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def ax_and_data():
    """Axes plus a 24-point ramp, so partial averages are easy to reason about."""
    idx = pd.date_range("2024-01-31", periods=24, freq="ME")
    series = pd.Series(range(1, 25), index=idx, dtype=float, name="price")
    _, ax = plt.subplots()
    return ax, idx, series


def _ma_values(ax: plt.Axes) -> np.ndarray:
    """The y data of the last line drawn on *ax*."""
    return np.asarray(ax.lines[-1].get_ydata(), dtype=float)


class TestMinPeriods:
    """The line must not claim a window it did not average over."""

    def test_default_demands_the_full_window(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        add_moving_average(ax, x, y, window=12)

        values = _ma_values(ax)
        # Eleven leading gaps, then the first honest MM12: mean(1..12) == 6.5.
        assert int(np.isnan(values).sum()) == 11
        assert values[11] == pytest.approx(6.5)

    def test_explicit_min_periods_draws_from_a_partial_sample(
        self, ax_and_data
    ) -> None:
        ax, x, y = ax_and_data
        configure(lines={"moving_avg_min_periods": 1})
        add_moving_average(ax, x, y, window=12)

        values = _ma_values(ax)
        assert int(np.isnan(values).sum()) == 0
        # A single observation, which is what min_periods=1 asks for.
        assert values[0] == pytest.approx(1.0)

    def test_min_periods_between_one_and_window(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        configure(lines={"moving_avg_min_periods": 4})
        add_moving_average(ax, x, y, window=12)

        values = _ma_values(ax)
        assert int(np.isnan(values).sum()) == 3
        assert values[3] == pytest.approx(2.5)  # mean(1..4)

    def test_zero_is_rejected_by_the_schema(self) -> None:
        # min_periods=0 would mean "average nothing"; ge=1 rules it out rather
        # than letting it fall through to the full-window branch. configure()
        # only stores the override, so the error surfaces when the config is
        # built -- not at the call that caused it.
        configure(lines={"moving_avg_min_periods": 0})
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            get_config()

    def test_window_longer_than_series_yields_no_line_values(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        add_moving_average(ax, x, y, window=100)

        assert bool(np.isnan(_ma_values(ax)).all())


class TestRendering:
    def test_label_reports_the_requested_window(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        add_moving_average(ax, x, y, window=12)

        assert ax.lines[-1].get_label() == "MM12"

    def test_custom_label_wins(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        add_moving_average(ax, x, y, window=12, label="Média de 12 meses")

        assert ax.lines[-1].get_label() == "Média de 12 meses"

    def test_window_below_one_raises(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        with pytest.raises(ValidationError, match="window must be >= 1"):
            add_moving_average(ax, x, y, window=0)
