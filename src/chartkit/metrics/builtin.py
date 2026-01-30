"""
Metricas built-in para graficos.

Registra metricas padrao como ATH, ATL, media movel, etc.
Estas metricas sao wrappers finos sobre as funcoes de overlay existentes.

Metricas disponiveis:
- 'ath': Linha no All-Time High
- 'atl': Linha no All-Time Low
- 'ma:N': Media movel de N periodos (ex: 'ma:12')
- 'hline:V': Linha horizontal no valor V (ex: 'hline:3.0')
- 'band:L:U': Banda sombreada entre L e U (ex: 'band:1.5:4.5')
"""

from __future__ import annotations

from .registry import MetricRegistry


def register_builtin_metrics() -> None:
    """
    Registra metricas padrao no registry.

    Chamado automaticamente ao importar o package metrics.
    """
    # Imports locais para evitar dependencias circulares
    from ..overlays import (
        add_ath_line,
        add_atl_line,
        add_band,
        add_hline,
        add_moving_average,
    )

    @MetricRegistry.register("ath")
    def metric_ath(ax, x_data, y_data, **kwargs) -> None:
        """
        Adiciona linha no All-Time High.

        Uso: metrics=['ath']
        """
        add_ath_line(ax, y_data, **kwargs)

    @MetricRegistry.register("atl")
    def metric_atl(ax, x_data, y_data, **kwargs) -> None:
        """
        Adiciona linha no All-Time Low.

        Uso: metrics=['atl']
        """
        add_atl_line(ax, y_data, **kwargs)

    @MetricRegistry.register("ma", param_names=["window"])
    def metric_ma(ax, x_data, y_data, window: int, **kwargs) -> None:
        """
        Adiciona linha de media movel.

        Args:
            window: Numero de periodos para media movel.

        Uso: metrics=['ma:12'] para media movel de 12 periodos.
        """
        add_moving_average(ax, x_data, y_data, window=window, **kwargs)

    @MetricRegistry.register("hline", param_names=["value"])
    def metric_hline(ax, x_data, y_data, value: float, **kwargs) -> None:
        """
        Adiciona linha horizontal em valor especifico.

        Args:
            value: Valor Y onde a linha sera desenhada.

        Uso: metrics=['hline:3.0'] para linha em y=3.0.
        """
        add_hline(ax, value=value, **kwargs)

    @MetricRegistry.register("band", param_names=["lower", "upper"])
    def metric_band(
        ax, x_data, y_data, lower: float, upper: float, **kwargs
    ) -> None:
        """
        Adiciona banda sombreada entre dois valores.

        Args:
            lower: Limite inferior da banda.
            upper: Limite superior da banda.

        Uso: metrics=['band:1.5:4.5'] para banda entre 1.5 e 4.5.
        """
        add_band(ax, lower=lower, upper=upper, **kwargs)
