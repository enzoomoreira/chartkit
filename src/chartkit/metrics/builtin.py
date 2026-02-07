from __future__ import annotations

from .registry import MetricRegistry


def register_builtin_metrics() -> None:
    """Registra metricas padrao no registry (chamado no import do package)."""
    from ..overlays import (
        add_ath_line,
        add_atl_line,
        add_band,
        add_hline,
        add_moving_average,
    )

    @MetricRegistry.register("ath")
    def metric_ath(ax, x_data, y_data, **kwargs) -> None:
        add_ath_line(ax, y_data, **kwargs)

    @MetricRegistry.register("atl")
    def metric_atl(ax, x_data, y_data, **kwargs) -> None:
        add_atl_line(ax, y_data, **kwargs)

    @MetricRegistry.register("ma", param_names=["window"])
    def metric_ma(ax, x_data, y_data, window: int, **kwargs) -> None:
        add_moving_average(ax, x_data, y_data, window=window, **kwargs)

    @MetricRegistry.register("hline", param_names=["value"], uses_series=False)
    def metric_hline(ax, x_data, y_data, value: float, **kwargs) -> None:
        add_hline(ax, value=value, **kwargs)

    @MetricRegistry.register("band", param_names=["lower", "upper"], uses_series=False)
    def metric_band(
        ax, x_data, y_data, lower: float, upper: float, **kwargs
    ) -> None:
        add_band(ax, lower=lower, upper=upper, **kwargs)
