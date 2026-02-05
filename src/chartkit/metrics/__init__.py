"""Sistema declarativo de metricas para graficos.

Sintaxe: ``metrics=['ath', 'ma:12', 'band:1.5:4.5', 'ath@revenue']``

Metricas built-in: ath, atl, ma:N, hline:V, band:L:U.
Use ``@coluna`` para selecionar coluna alvo em DataFrames multi-serie.
"""

from .builtin import register_builtin_metrics
from .registry import MetricRegistry, MetricSpec

register_builtin_metrics()

__all__ = ["MetricRegistry", "MetricSpec"]
