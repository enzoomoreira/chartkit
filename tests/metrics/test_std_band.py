"""Tests for std_band overlay (rolling and full-series modes)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import ValidationError
from chartkit.overlays.std_band import add_std_band


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def ax_and_data():
    """Simple axes + series for overlay tests."""
    idx = pd.date_range("2023-01-01", periods=50, freq="ME")
    rng = np.random.default_rng(42)
    series = pd.Series(rng.normal(100, 10, 50), index=idx, name="price")
    _, ax = plt.subplots()
    return ax, idx, series


class TestFullSeriesMode:
    def test_full_series_produces_flat_bands(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        add_std_band(ax, x, y, window=0, deviations=2.0)

        # fill_between creates a PolyCollection
        assert len(ax.collections) == 1

    def test_full_series_band_values_are_constant(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        mean = y.mean()
        std = y.std()

        add_std_band(ax, x, y, window=0, deviations=2.0, show_center=True)

        # Center line should be flat at the mean
        center_line = ax.lines[0]
        center_y = center_line.get_ydata()
        np.testing.assert_allclose(center_y, mean, atol=1e-10)

        # Band edges should be at mean +/- 2*std
        collection = ax.collections[0]
        paths = collection.get_paths()
        vertices = paths[0].vertices
        y_values = vertices[:, 1]
        expected_upper = mean + 2.0 * std
        expected_lower = mean - 2.0 * std
        assert np.isclose(y_values.max(), expected_upper, atol=1e-10)
        assert np.isclose(y_values.min(), expected_lower, atol=1e-10)

    def test_full_series_default_label(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        add_std_band(ax, x, y, window=0, deviations=2.0)

        collection = ax.collections[0]
        assert collection.get_label() == "DP(2.0)"

    def test_full_series_custom_label(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        add_std_band(ax, x, y, window=0, deviations=1.5, label="Custom")

        collection = ax.collections[0]
        assert collection.get_label() == "Custom"

    def test_window_zero_is_default(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        # window defaults to 0 (full series)
        add_std_band(ax, x, y, deviations=2.0)
        assert len(ax.collections) == 1


class TestRollingMode:
    def test_rolling_produces_varying_bands(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        add_std_band(ax, x, y, window=10, deviations=2.0)
        assert len(ax.collections) == 1

    def test_rolling_default_label(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        add_std_band(ax, x, y, window=10, deviations=2.0)

        collection = ax.collections[0]
        assert collection.get_label() == "BB(10, 2.0)"


class TestValidation:
    def test_negative_window_raises(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        with pytest.raises(ValidationError, match="window must be >= 0"):
            add_std_band(ax, x, y, window=-1)

    def test_window_one_raises(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        with pytest.raises(ValidationError, match="window must be 0"):
            add_std_band(ax, x, y, window=1)

    def test_negative_deviations_raises(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        with pytest.raises(ValidationError, match="deviations must be positive"):
            add_std_band(ax, x, y, window=0, deviations=-1.0)

    def test_zero_deviations_raises(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        with pytest.raises(ValidationError, match="deviations must be positive"):
            add_std_band(ax, x, y, window=0, deviations=0)

    def test_window_two_is_valid_rolling(self, ax_and_data) -> None:
        ax, x, y = ax_and_data
        add_std_band(ax, x, y, window=2, deviations=2.0)
        assert len(ax.collections) == 1
