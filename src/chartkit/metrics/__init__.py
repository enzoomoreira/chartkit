"""
Sistema de metricas para graficos.

Metricas sao elementos visuais aplicados ao grafico de forma declarativa.
Em vez de flags booleanas (show_ath=True), use uma lista (ou str) de metricas:

    df.chartkit.plot(metrics='ath')
    df.chartkit.plot(metrics=['ath', 'atl', 'ma:12'])

Sintaxe '@' para selecionar coluna alvo:
    df.chartkit.plot(y=['revenue', 'costs'], metrics=['ath@revenue', 'ma:3@costs'])

Metricas disponiveis:
- 'ath': Linha no All-Time High
- 'atl': Linha no All-Time Low
- 'ma:N': Media movel de N periodos (ex: 'ma:12')
- 'hline:V': Linha horizontal no valor V (ex: 'hline:3.0')
- 'band:L:U': Banda sombreada entre L e U (ex: 'band:1.5:4.5')

Para adicionar metricas customizadas:
    from chartkit.metrics import MetricRegistry

    @MetricRegistry.register('my_metric', param_names=['threshold'])
    def my_metric(ax, x_data, y_data, threshold: float):
        ax.axhline(threshold, color='purple', linestyle='--')

    # Uso
    df.chartkit.plot(metrics=['my_metric:5.0'])

Para edge cases (colunas com '@' no nome), use MetricSpec diretamente:
    from chartkit.metrics import MetricSpec
    df.chartkit.plot(metrics=[MetricSpec('ath', series='col@weird')])
"""

from .builtin import register_builtin_metrics
from .registry import MetricRegistry, MetricSpec

# Registra metricas padrao ao importar o package
register_builtin_metrics()

__all__ = ["MetricRegistry", "MetricSpec"]
