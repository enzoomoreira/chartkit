from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from .engine import ChartingPlotter
from .transforms.accessor import TransformAccessor

if TYPE_CHECKING:
    from .result import PlotResult


@pd.api.extensions.register_dataframe_accessor("chartkit")
class ChartingAccessor:
    """Pandas accessor para plotagem e transforms encadeados.

    Registrado automaticamente ao importar chartkit.
    Transforms retornam ``TransformAccessor``; ``.plot()`` retorna ``PlotResult``.
    """

    def __init__(self, pandas_obj: pd.DataFrame) -> None:
        self._obj = pandas_obj

    def yoy(self, periods: int | None = None) -> TransformAccessor:
        """Variacao percentual anual (Year-over-Year)."""
        return TransformAccessor(self._obj).yoy(periods)

    def mom(self, periods: int | None = None) -> TransformAccessor:
        """Variacao percentual mensal (Month-over-Month)."""
        return TransformAccessor(self._obj).mom(periods)

    def accum_12m(self) -> TransformAccessor:
        """Variacao acumulada em 12 meses (produto composto)."""
        return TransformAccessor(self._obj).accum_12m()

    def diff(self, periods: int = 1) -> TransformAccessor:
        """Diferenca absoluta entre periodos."""
        return TransformAccessor(self._obj).diff(periods)

    def normalize(
        self, base: int | None = None, base_date: str | None = None
    ) -> TransformAccessor:
        """Normaliza serie para um valor base em uma data especifica."""
        return TransformAccessor(self._obj).normalize(base, base_date)

    def annualize_daily(self, trading_days: int | None = None) -> TransformAccessor:
        """Anualiza taxa diaria via juros compostos."""
        return TransformAccessor(self._obj).annualize_daily(trading_days)

    def compound_rolling(self, window: int | None = None) -> TransformAccessor:
        """Retorno composto em janela movel."""
        return TransformAccessor(self._obj).compound_rolling(window)

    def to_month_end(self) -> TransformAccessor:
        """Normaliza indice temporal para fim do mes."""
        return TransformAccessor(self._obj).to_month_end()

    def plot(
        self,
        x: str | None = None,
        y: str | list[str] | None = None,
        kind: str = "line",
        title: str | None = None,
        units: str | None = None,
        source: str | None = None,
        highlight_last: bool = False,
        y_origin: str = "zero",
        save_path: str | None = None,
        metrics: str | list[str] | None = None,
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
            highlight_last=highlight_last,
            y_origin=y_origin,
            save_path=save_path,
            metrics=metrics,
            **kwargs,
        )
