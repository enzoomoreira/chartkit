from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from .temporal import (
    accum,
    annualize,
    diff,
    drawdown,
    normalize,
    to_month_end,
    variation,
    zscore,
)

if TYPE_CHECKING:
    from ..result import PlotResult


class TransformAccessor:
    """Accessor encadeavel para transforms sobre DataFrames e Series.

    Cada metodo retorna um novo TransformAccessor, permitindo encadeamento.
    Finalize com ``.plot()`` para gerar o grafico ou ``.df`` para obter os dados.
    Series sao convertidas para DataFrame internamente.

    Example:
        >>> df.chartkit.variation(horizon='year').plot(title="Variacao Anual")
        >>> transformed = df.chartkit.normalize().df
    """

    def __init__(self, df: pd.DataFrame | pd.Series) -> None:
        self._df = df.to_frame() if isinstance(df, pd.Series) else df

    def variation(
        self,
        horizon: str = "month",
        periods: int | None = None,
        freq: str | None = None,
    ) -> TransformAccessor:
        """Variacao percentual entre periodos."""
        return TransformAccessor(variation(self._df, horizon, periods, freq))

    def accum(
        self, window: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Variacao acumulada via produto composto em janela movel."""
        return TransformAccessor(accum(self._df, window, freq))

    def diff(self, periods: int = 1) -> TransformAccessor:
        """Diferenca absoluta entre periodos."""
        return TransformAccessor(diff(self._df, periods))

    def normalize(
        self, base: int | None = None, base_date: str | None = None
    ) -> TransformAccessor:
        """Normaliza serie para um valor base em uma data especifica."""
        return TransformAccessor(normalize(self._df, base, base_date))

    def annualize(
        self, periods: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Anualiza taxa periodica via juros compostos."""
        return TransformAccessor(annualize(self._df, periods, freq))

    def drawdown(self) -> TransformAccessor:
        """Distancia percentual do pico historico."""
        return TransformAccessor(drawdown(self._df))

    def zscore(self, window: int | None = None) -> TransformAccessor:
        """Padronizacao estatistica (z-score)."""
        return TransformAccessor(zscore(self._df, window))

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
