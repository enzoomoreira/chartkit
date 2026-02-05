"""
Pandas Accessor para funcionalidade de charting.

Registra o accessor 'chartkit' em todos os DataFrames pandas,
permitindo plotagem e transformacoes encadeadas.

Uso:
    import chartkit

    # Plotagem simples
    df.chartkit.plot()

    # Com metricas
    df.chartkit.plot(metrics=['ath', 'atl', 'ma:12'])

    # Transforms encadeados
    df.chartkit.yoy().plot(title='Variacao YoY')

    # Encadeamento completo
    df.chartkit.annualize_daily().plot(metrics=['ath']).save('chart.png')
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from .engine import ChartingPlotter
from .transforms.accessor import TransformAccessor

if TYPE_CHECKING:
    from .result import PlotResult


@pd.api.extensions.register_dataframe_accessor("chartkit")
class ChartingAccessor:
    """
    Pandas Accessor para funcionalidade de charting.

    Fornece metodos para plotagem e transformacoes de dados diretamente
    a partir de DataFrames pandas.

    Attributes:
        _obj: DataFrame pandas original.

    Example:
        >>> import chartkit
        >>> df.chartkit.plot(title='Meu Grafico')
        >>> df.chartkit.yoy().plot(metrics=['ath']).save('chart.png')
    """

    def __init__(self, pandas_obj: pd.DataFrame) -> None:
        """
        Inicializa o accessor com um DataFrame.

        Args:
            pandas_obj: DataFrame pandas.
        """
        self._obj = pandas_obj

    # =========================================================================
    # Transforms (retornam TransformAccessor para encadeamento)
    # =========================================================================

    def yoy(self, periods: int | None = None) -> TransformAccessor:
        """
        Calcula variacao percentual anual (Year-over-Year).

        Args:
            periods: Numero de periodos para comparacao (default: config.transforms.yoy_periods).

        Returns:
            TransformAccessor para encadeamento.

        Example:
            >>> df.chartkit.yoy().plot()
        """
        return TransformAccessor(self._obj).yoy(periods)

    def mom(self, periods: int | None = None) -> TransformAccessor:
        """
        Calcula variacao percentual mensal (Month-over-Month).

        Args:
            periods: Numero de periodos para comparacao (default: config.transforms.mom_periods).

        Returns:
            TransformAccessor para encadeamento.

        Example:
            >>> df.chartkit.mom().plot()
        """
        return TransformAccessor(self._obj).mom(periods)

    def accum_12m(self) -> TransformAccessor:
        """
        Calcula variacao acumulada em 12 meses.

        Returns:
            TransformAccessor para encadeamento.

        Example:
            >>> df.chartkit.accum_12m().plot()
        """
        return TransformAccessor(self._obj).accum_12m()

    def diff(self, periods: int = 1) -> TransformAccessor:
        """
        Calcula diferenca absoluta entre periodos.

        Args:
            periods: Numero de periodos para diferenca (default: 1).

        Returns:
            TransformAccessor para encadeamento.

        Example:
            >>> df.chartkit.diff().plot()
        """
        return TransformAccessor(self._obj).diff(periods)

    def normalize(
        self, base: int | None = None, base_date: str | None = None
    ) -> TransformAccessor:
        """
        Normaliza serie para um valor base.

        Args:
            base: Valor base para normalizacao (default: config.transforms.normalize_base).
            base_date: Data base para normalizacao. Se None, usa primeira data.

        Returns:
            TransformAccessor para encadeamento.

        Example:
            >>> df.chartkit.normalize(base_date='2020-01-01').plot()
        """
        return TransformAccessor(self._obj).normalize(base, base_date)

    def annualize_daily(self, trading_days: int | None = None) -> TransformAccessor:
        """
        Anualiza taxa diaria para taxa anual.

        Args:
            trading_days: Dias uteis no ano (default: config.transforms.trading_days_per_year).

        Returns:
            TransformAccessor para encadeamento.

        Example:
            >>> df.chartkit.annualize_daily().plot()
        """
        return TransformAccessor(self._obj).annualize_daily(trading_days)

    def compound_rolling(self, window: int | None = None) -> TransformAccessor:
        """
        Calcula retorno composto em janela movel.

        Args:
            window: Tamanho da janela em periodos (default: config.transforms.rolling_window).

        Returns:
            TransformAccessor para encadeamento.

        Example:
            >>> df.chartkit.compound_rolling(12).plot()
        """
        return TransformAccessor(self._obj).compound_rolling(window)

    def to_month_end(self) -> TransformAccessor:
        """
        Normaliza indice temporal para fim do mes.

        Returns:
            TransformAccessor para encadeamento.

        Example:
            >>> df.chartkit.to_month_end().plot()
        """
        return TransformAccessor(self._obj).to_month_end()

    # =========================================================================
    # Plotagem
    # =========================================================================

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
        """
        Cria um grafico padronizado.

        Args:
            x: Coluna para eixo X. Se None, usa o index do DataFrame.
            y: Coluna(s) para eixo Y. Se None, usa todas as colunas numericas.
            kind: Tipo de grafico ('line' ou 'bar').
            title: Titulo do grafico.
            units: Formatacao do eixo Y (ex: '%', 'BRL', 'USD', 'human').
            source: Fonte dos dados para exibir no rodape.
            highlight_last: Se True, destaca o ultimo valor da serie.
            y_origin: Origem do eixo Y para barras ('zero' ou 'auto').
            save_path: Se fornecido, salva o grafico neste caminho.
            metrics: Metrica(s) a aplicar (str ou lista). Formatos:
                - 'ath': All-Time High
                - 'atl': All-Time Low
                - 'ma:N': Media movel de N periodos (ex: 'ma:12')
                - 'hline:V': Linha horizontal no valor V (ex: 'hline:3.0')
                - 'band:L:U': Banda entre L e U (ex: 'band:1.5:4.5')
                - 'metrica@coluna': Aplica na coluna especifica
                  (ex: 'ath@revenue', 'ma:12@costs')
            **kwargs: Argumentos extras passados para matplotlib.

        Returns:
            PlotResult com metodos .save(), .show() e acesso ao axes.

        Example:
            >>> df.chartkit.plot(metrics='ath').save('chart.png')
            >>> df.chartkit.plot(metrics=['ath@revenue', 'ma:12@costs'])
        """
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
