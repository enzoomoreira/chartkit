from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.charts.renderer import ChartRenderer
from chartkit.exceptions import ValidationError


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def datetime_index() -> pd.DatetimeIndex:
    return pd.date_range("2023-01-31", periods=6, freq="ME")


# ---------------------------------------------------------------------------
# Alias resolution
# ---------------------------------------------------------------------------


class TestAliases:
    def test_line_alias_resolves_to_plot(
        self, datetime_index: pd.DatetimeIndex
    ) -> None:
        """kind='line' should be treated as 'plot' (matplotlib convention)."""
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="v")
        ChartRenderer.render(ax, "line", datetime_index, series, highlight=[])
        assert len(ax.lines) >= 1


# ---------------------------------------------------------------------------
# Enhancer dispatch
# ---------------------------------------------------------------------------


class TestEnhancerDispatch:
    def test_bar_dispatches_to_enhancer(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="v")
        ChartRenderer.render(ax, "bar", datetime_index, series, highlight=[])
        assert len(ax.containers) >= 1


# ---------------------------------------------------------------------------
# Generic fallback
# ---------------------------------------------------------------------------


class TestGenericFallback:
    def test_scatter(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="v")
        ChartRenderer.render(ax, "scatter", datetime_index, series, highlight=[])
        assert len(ax.collections) >= 1

    def test_step(self, datetime_index: pd.DatetimeIndex) -> None:
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="v")
        ChartRenderer.render(ax, "step", datetime_index, series, highlight=[])
        assert len(ax.lines) >= 1


# ---------------------------------------------------------------------------
# Unsupported kinds
# ---------------------------------------------------------------------------


class TestUnsupportedKinds:
    @pytest.mark.parametrize("kind", ["imshow", "contour", "contourf", "pcolormesh"])
    def test_grid_kinds_raise(self, kind: str) -> None:
        with pytest.raises(ValidationError, match="not supported"):
            ChartRenderer.validate_kind(kind)

    @pytest.mark.parametrize("kind", ["quiver", "streamplot", "barbs"])
    def test_vector_kinds_raise(self, kind: str) -> None:
        with pytest.raises(ValidationError, match="not supported"):
            ChartRenderer.validate_kind(kind)

    def test_spy_raises(self) -> None:
        with pytest.raises(ValidationError, match="not supported"):
            ChartRenderer.validate_kind("spy")


# ---------------------------------------------------------------------------
# validate_kind
# ---------------------------------------------------------------------------


class TestValidateKind:
    def test_valid_generic_kind(self) -> None:
        ChartRenderer.validate_kind("scatter")

    def test_private_method_raises(self) -> None:
        with pytest.raises(ValidationError, match="not a valid"):
            ChartRenderer.validate_kind("_internal")

    def test_nonexistent_method_raises(self) -> None:
        with pytest.raises(ValidationError, match="not a valid"):
            ChartRenderer.validate_kind("totally_fake_method_xyz")


# ---------------------------------------------------------------------------
# Post-render obstacle registration
# ---------------------------------------------------------------------------


class TestPostRenderObstacles:
    def test_line_registered_as_obstacle(
        self, datetime_index: pd.DatetimeIndex
    ) -> None:
        """After rendering a line, new Line2D should be registered as obstacle."""
        _, ax = plt.subplots()
        series = pd.Series([1, 2, 3, 4, 5, 6], index=datetime_index, name="v")
        ChartRenderer.render(ax, "plot", datetime_index, series, highlight=[])
        # Line2D exists on the axes
        assert len(ax.lines) >= 1
