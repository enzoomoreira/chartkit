from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

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

if TYPE_CHECKING:
    from ..result import PlotResult


class TransformAccessor:
    """Accessor encadeavel para transforms sobre DataFrames.

    Cada metodo retorna um novo TransformAccessor, permitindo encadeamento.
    Finalize com ``.plot()`` para gerar o grafico ou ``.df`` para obter os dados.

    Example:
        >>> df.chartkit.yoy().mom().plot(title="Taxa")
        >>> transformed = df.chartkit.normalize().df
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def yoy(self, periods: int | None = None) -> TransformAccessor:
        """Variacao percentual anual (Year-over-Year)."""
        return TransformAccessor(yoy(self._df, periods))

    def mom(self, periods: int | None = None) -> TransformAccessor:
        """Variacao percentual mensal (Month-over-Month)."""
        return TransformAccessor(mom(self._df, periods))

    def accum_12m(self) -> TransformAccessor:
        """Variacao acumulada em 12 meses (produto composto)."""
        return TransformAccessor(accum_12m(self._df))

    def diff(self, periods: int = 1) -> TransformAccessor:
        """Diferenca absoluta entre periodos."""
        return TransformAccessor(diff(self._df, periods))

    def normalize(
        self, base: int | None = None, base_date: str | None = None
    ) -> TransformAccessor:
        """Normaliza serie para um valor base em uma data especifica."""
        return TransformAccessor(normalize(self._df, base, base_date))

    def annualize_daily(self, trading_days: int | None = None) -> TransformAccessor:
        """Anualiza taxa diaria via juros compostos."""
        return TransformAccessor(annualize_daily(self._df, trading_days))

    def compound_rolling(self, window: int | None = None) -> TransformAccessor:
        """Retorno composto em janela movel."""
        return TransformAccessor(compound_rolling(self._df, window))

    def to_month_end(self) -> TransformAccessor:
        """Normaliza indice temporal para fim do mes."""
        return TransformAccessor(to_month_end(self._df))

    def plot(self, **kwargs) -> PlotResult:
        """Finaliza a cadeia de transforms e plota o DataFrame."""
        from ..engine import ChartingPlotter

        plotter = ChartingPlotter(self._df)
        return plotter.plot(**kwargs)

    @property
    def df(self) -> pd.DataFrame:
        return self._df

    def __repr__(self) -> str:
        shape = self._df.shape
        return f"<TransformAccessor: {shape[0]} rows x {shape[1]} cols>"
