from __future__ import annotations

from chartkit.metrics.registry import MetricRegistry

# Ensure builtins are registered
import chartkit.metrics.builtin  # noqa: F401


class TestMetricRegistry:
    def test_builtin_metrics_registered(self) -> None:
        available = MetricRegistry.available()
        expected = [
            "ath",
            "atl",
            "avg",
            "band",
            "hline",
            "ma",
            "std_band",
            "target",
            "vband",
        ]
        for name in expected:
            assert name in available

    def test_available_returns_sorted(self) -> None:
        available = MetricRegistry.available()
        assert available == sorted(available)

    def test_register_and_available(self) -> None:
        @MetricRegistry.register("test_metric")
        def _handler(ax, x, y):
            pass

        assert "test_metric" in MetricRegistry.available()

    def test_clear_removes_all(self) -> None:
        MetricRegistry.clear()
        assert MetricRegistry.available() == []

    def test_register_decorator_returns_func(self) -> None:
        def my_func(ax, x, y):
            pass

        result = MetricRegistry.register("test_deco")(my_func)
        assert result is my_func

    def test_hline_uses_series_false(self) -> None:
        entry = MetricRegistry._metrics["hline"]
        assert entry.uses_series is False

    def test_ath_uses_series_true(self) -> None:
        entry = MetricRegistry._metrics["ath"]
        assert entry.uses_series is True

    def test_ma_has_window_param(self) -> None:
        entry = MetricRegistry._metrics["ma"]
        assert "window" in entry.param_names
