"""MetricRegistry registration and application tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.metrics.registry import MetricRegistry

# Ensure builtins are registered
import chartkit.metrics.builtin  # noqa: F401


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


class TestRegistry:
    def test_builtin_metrics_registered(self) -> None:
        available = MetricRegistry.available()
        for name in [
            "ath",
            "atl",
            "avg",
            "band",
            "hline",
            "ma",
            "std_band",
            "target",
            "vband",
        ]:
            assert name in available

    def test_available_returns_sorted(self) -> None:
        available = MetricRegistry.available()
        assert available == sorted(available)

    def test_register_custom_and_available(self) -> None:
        @MetricRegistry.register("_test_custom_metric")
        def _handler(ax, x, y):
            pass

        assert "_test_custom_metric" in MetricRegistry.available()

    def test_register_decorator_returns_func(self) -> None:
        def my_func(ax, x, y):
            pass

        result = MetricRegistry.register("_test_deco_return")(my_func)
        assert result is my_func


class TestRegistryApply:
    def test_apply_calls_handler_with_ax_and_data(self) -> None:
        handler = MagicMock()
        MetricRegistry.register("_test_apply_basic")(handler)

        _, ax = plt.subplots()
        idx = pd.date_range("2023-01-01", periods=5, freq="ME")
        y_data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx)

        MetricRegistry.apply(ax, idx, y_data, "_test_apply_basic")
        handler.assert_called_once_with(ax, idx, y_data)

    def test_apply_passes_params_to_handler(self) -> None:
        handler = MagicMock()
        MetricRegistry.register("_test_apply_params", param_names=["window"])(handler)

        _, ax = plt.subplots()
        idx = pd.date_range("2023-01-01", periods=5, freq="ME")
        y_data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx)

        MetricRegistry.apply(ax, idx, y_data, "_test_apply_params:10")
        handler.assert_called_once_with(ax, idx, y_data, window=10)
