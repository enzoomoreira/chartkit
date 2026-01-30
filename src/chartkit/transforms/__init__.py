"""
Transformacoes de dados temporais.

Funcoes para transformar series temporais em diferentes representacoes,
como variacoes percentuais, acumulados e normalizacoes.

Uso standalone:
    from chartkit import yoy, mom, accum_12m
    df_yoy = yoy(df)  # Variacao ano-contra-ano

Uso encadeado (via accessor):
    df.chartkit.yoy().mom().plot()
"""

from .accessor import TransformAccessor
from .temporal import (
    accum_12m,
    annualize_daily,
    compound_rolling,
    diff,
    mom,
    normalize,
    to_month_end,
    yoy,
)

__all__ = [
    "TransformAccessor",
    "yoy",
    "mom",
    "accum_12m",
    "diff",
    "normalize",
    "annualize_daily",
    "compound_rolling",
    "to_month_end",
]
