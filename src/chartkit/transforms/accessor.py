"""
Accessor encadeavel para transforms.

Permite aplicar transformacoes em cadeia e finalizar com .plot():

    df.chartkit.yoy().mom().plot()

Cada metodo de transform retorna um novo TransformAccessor,
permitindo encadeamento sem modificar o DataFrame original.
"""

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
    """
    Accessor encadeavel para transforms.

    Cada metodo de transform retorna um novo TransformAccessor
    contendo o DataFrame transformado, permitindo encadeamento.
    O metodo .plot() finaliza a cadeia e retorna um PlotResult.

    Attributes:
        _df: DataFrame com os dados (possivelmente transformados).

    Example:
        >>> # Encadeamento de transforms
        >>> df.chartkit.annualize_daily().yoy().plot(title='Taxa YoY')

        >>> # Acesso ao DataFrame transformado
        >>> df_yoy = df.chartkit.yoy().df
    """

    def __init__(self, df: pd.DataFrame) -> None:
        """
        Inicializa o accessor com um DataFrame.

        Args:
            df: DataFrame pandas com os dados.
        """
        self._df = df

    # =========================================================================
    # Transforms (cada um retorna novo TransformAccessor)
    # =========================================================================

    def yoy(self, periods: int = 12) -> TransformAccessor:
        """
        Calcula variacao percentual anual (Year-over-Year).

        Assume dados mensais por default (12 periodos = 1 ano).

        Args:
            periods: Numero de periodos para comparacao (default: 12).

        Returns:
            Novo TransformAccessor com dados transformados.

        Example:
            >>> df.chartkit.yoy().plot()  # YoY para dados mensais
            >>> df.chartkit.yoy(periods=4).plot()  # YoY para dados trimestrais
        """
        return TransformAccessor(yoy(self._df, periods))

    def mom(self, periods: int = 1) -> TransformAccessor:
        """
        Calcula variacao percentual mensal (Month-over-Month).

        Args:
            periods: Numero de periodos para comparacao (default: 1).

        Returns:
            Novo TransformAccessor com dados transformados.

        Example:
            >>> df.chartkit.mom().plot()  # Variacao mensal
        """
        return TransformAccessor(mom(self._df, periods))

    def accum_12m(self) -> TransformAccessor:
        """
        Calcula variacao acumulada em 12 meses.

        Util para indices de inflacao mensal (ex: IPCA mensal -> IPCA 12m).
        Formula: (Produto(1 + x/100) - 1) * 100

        Returns:
            Novo TransformAccessor com dados transformados.

        Example:
            >>> df.chartkit.accum_12m().plot()  # IPCA acumulado 12m
        """
        return TransformAccessor(accum_12m(self._df))

    def diff(self, periods: int = 1) -> TransformAccessor:
        """
        Calcula diferenca absoluta entre periodos.

        Args:
            periods: Numero de periodos para diferenca (default: 1).

        Returns:
            Novo TransformAccessor com dados transformados.

        Example:
            >>> df.chartkit.diff().plot()  # Diferenca para periodo anterior
        """
        return TransformAccessor(diff(self._df, periods))

    def normalize(
        self, base: int = 100, base_date: str | None = None
    ) -> TransformAccessor:
        """
        Normaliza serie para um valor base em uma data especifica.

        Util para comparar series com escalas diferentes.

        Args:
            base: Valor base para normalizacao (default: 100).
            base_date: Data base para normalizacao. Se None, usa primeira data.

        Returns:
            Novo TransformAccessor com dados transformados.

        Example:
            >>> df.chartkit.normalize().plot()  # Base 100 na primeira data
            >>> df.chartkit.normalize(base_date='2020-01-01').plot()
        """
        return TransformAccessor(normalize(self._df, base, base_date))

    def annualize_daily(self, trading_days: int = 252) -> TransformAccessor:
        """
        Anualiza taxa diaria para taxa anual usando juros compostos.

        Formula: ((1 + r_diaria) ^ dias_uteis - 1) * 100

        Args:
            trading_days: Dias uteis no ano (default: 252 para Brasil).

        Returns:
            Novo TransformAccessor com dados transformados.

        Example:
            >>> df.chartkit.annualize_daily().plot()  # CDI diario -> anual
        """
        return TransformAccessor(annualize_daily(self._df, trading_days))

    def compound_rolling(self, window: int = 12) -> TransformAccessor:
        """
        Calcula retorno composto em janela movel.

        Multiplica os fatores (1 + taxa) ao longo da janela.
        Util para calcular Selic acumulada 12 meses.

        Args:
            window: Tamanho da janela em periodos (default: 12).

        Returns:
            Novo TransformAccessor com dados transformados.

        Example:
            >>> df.chartkit.compound_rolling(12).plot()  # Selic 12m
        """
        return TransformAccessor(compound_rolling(self._df, window))

    def to_month_end(self) -> TransformAccessor:
        """
        Normaliza indice temporal para fim do mes.

        Util para alinhar series com frequencias diferentes.

        Returns:
            Novo TransformAccessor com dados transformados.

        Example:
            >>> df.chartkit.to_month_end().plot()
        """
        return TransformAccessor(to_month_end(self._df))

    # =========================================================================
    # Terminadores
    # =========================================================================

    def plot(self, **kwargs) -> PlotResult:
        """
        Plota o DataFrame transformado.

        Finaliza a cadeia de transforms e cria o grafico.
        Aceita todos os argumentos de ChartingPlotter.plot().

        Args:
            **kwargs: Argumentos passados para ChartingPlotter.plot().

        Returns:
            PlotResult com metodos .save(), .show() e acesso ao axes.

        Example:
            >>> df.chartkit.yoy().plot(title='Variacao YoY', metrics=['ath'])
        """
        # Import local para evitar dependencia circular
        from ..engine import ChartingPlotter

        plotter = ChartingPlotter(self._df)
        return plotter.plot(**kwargs)

    @property
    def df(self) -> pd.DataFrame:
        """
        Retorna o DataFrame transformado.

        Util para inspecionar ou usar os dados transformados
        fora do contexto de plotagem.

        Returns:
            DataFrame com as transformacoes aplicadas.

        Example:
            >>> df_yoy = df.chartkit.yoy().df
            >>> df_yoy.describe()
        """
        return self._df

    def __repr__(self) -> str:
        """Representacao amigavel do accessor."""
        shape = self._df.shape
        return f"<TransformAccessor: {shape[0]} rows x {shape[1]} cols>"
