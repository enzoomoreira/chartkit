from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from .engine import ChartingPlotter
from .transforms.accessor import TransformAccessor

if TYPE_CHECKING:
    from .engine import ChartKind, HighlightInput, UnitFormat
    from .result import PlotResult


@pd.api.extensions.register_dataframe_accessor("chartkit")
@pd.api.extensions.register_series_accessor("chartkit")
class ChartingAccessor:
    """Pandas accessor para plotagem e transforms encadeados.

    Registrado automaticamente ao importar chartkit.
    Aceita DataFrame e Series (Series e convertida para DataFrame internamente).
    Transforms retornam ``TransformAccessor``; ``.plot()`` retorna ``PlotResult``.
    """

    def __init__(self, pandas_obj: pd.DataFrame | pd.Series) -> None:
        self._obj = (
            pandas_obj.to_frame() if isinstance(pandas_obj, pd.Series) else pandas_obj
        )

    def yoy(
        self, periods: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Variacao percentual anual (Year-over-Year)."""
        return TransformAccessor(self._obj).yoy(periods, freq)

    def mom(
        self, periods: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Variacao percentual mensal (Month-over-Month)."""
        return TransformAccessor(self._obj).mom(periods, freq)

    def accum(
        self, window: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Variacao acumulada via produto composto em janela movel."""
        return TransformAccessor(self._obj).accum(window, freq)

    def diff(self, periods: int = 1) -> TransformAccessor:
        """Diferenca absoluta entre periodos."""
        return TransformAccessor(self._obj).diff(periods)

    def normalize(
        self, base: int | None = None, base_date: str | None = None
    ) -> TransformAccessor:
        """Normaliza serie para um valor base em uma data especifica."""
        return TransformAccessor(self._obj).normalize(base, base_date)

    def annualize(
        self, periods: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Anualiza taxa periodica via juros compostos."""
        return TransformAccessor(self._obj).annualize(periods, freq)

    def compound_rolling(
        self, window: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Retorno composto em janela movel."""
        return TransformAccessor(self._obj).compound_rolling(window, freq)

    def drawdown(self) -> TransformAccessor:
        """Distancia percentual do pico historico."""
        return TransformAccessor(self._obj).drawdown()

    def zscore(self, window: int | None = None) -> TransformAccessor:
        """Padronizacao estatistica (z-score)."""
        return TransformAccessor(self._obj).zscore(window)

    def to_month_end(self) -> TransformAccessor:
        """Normaliza indice temporal para fim do mes."""
        return TransformAccessor(self._obj).to_month_end()

    def plot(
        self,
        x: str | None = None,
        y: str | list[str] | None = None,
        *,
        kind: ChartKind = "line",
        title: str | None = None,
        units: UnitFormat | None = None,
        source: str | None = None,
        highlight: HighlightInput = False,
        metrics: str | list[str] | None = None,
        fill_between: tuple[str, str] | None = None,
        legend: bool | None = None,
        **kwargs,
    ) -> PlotResult:
        """Cria grafico padronizado. Ver ``ChartingPlotter.plot()`` para docs completas."""
        plotter = ChartingPlotter(self._obj)
        return plotter.plot(
            x=x,
            y=y,
            kind=kind,
            title=title,
            units=units,
            source=source,
            highlight=highlight,
            metrics=metrics,
            fill_between=fill_between,
            legend=legend,
            **kwargs,
        )
