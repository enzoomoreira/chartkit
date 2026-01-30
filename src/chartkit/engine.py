"""
Motor de plotagem principal.

Orquestra temas, formatadores e componentes para criar graficos
financeiros padronizados.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from ._internal import resolve_collisions
from .charts.bar import plot_bar
from .charts.line import plot_line
from .decorations import add_footer
from .metrics import MetricRegistry
from .result import PlotResult
from .settings import get_charts_path, get_config
from .styling import (
    compact_currency_formatter,
    currency_formatter,
    human_readable_formatter,
    percent_formatter,
    points_formatter,
    theme,
)


# Mapa de formatadores para eixo Y
_FORMATTERS = {
    "BRL": lambda: currency_formatter("BRL"),
    "USD": lambda: currency_formatter("USD"),
    "BRL_compact": lambda: compact_currency_formatter("BRL"),
    "USD_compact": lambda: compact_currency_formatter("USD"),
    "%": percent_formatter,
    "human": human_readable_formatter,
    "points": points_formatter,
}


class ChartingPlotter:
    """
    Factory de visualizacao financeira padronizada.

    Orquestra temas, formatadores e componentes para criar graficos.

    Attributes:
        df: DataFrame pandas com os dados.
        _fig: Matplotlib Figure (criada em plot()).
        _ax: Matplotlib Axes (criada em plot()).
    """

    def __init__(self, df: pd.DataFrame) -> None:
        """
        Inicializa o motor de plotagem com um DataFrame.

        Args:
            df: DataFrame pandas contendo os dados a serem plotados.
                O indice deve ser do tipo DatetimeIndex para graficos temporais.
        """
        self.df = df
        self._fig = None
        self._ax = None

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
        metrics: list[str] | None = None,
        **kwargs,
    ) -> PlotResult:
        """
        Gera um grafico padronizado.

        Args:
            x: Coluna para eixo X (default: index).
            y: Coluna(s) para eixo Y (default: todas numericas).
            kind: Tipo de grafico ('line' ou 'bar').
            title: Titulo do grafico.
            units: Formatacao do eixo Y ('BRL', 'USD', '%', 'points', 'human').
            source: Fonte dos dados para rodape (ex: 'BCB', 'IBGE').
            highlight_last: Se True, destaca o ultimo valor da serie.
            y_origin: Origem do eixo Y para barras ('zero', 'auto').
            save_path: Caminho para salvar o grafico.
            metrics: Lista de metricas a aplicar. Formatos suportados:
                - 'ath': All-Time High
                - 'atl': All-Time Low
                - 'ma:N': Media movel de N periodos (ex: 'ma:12')
                - 'hline:V': Linha horizontal no valor V (ex: 'hline:3.0')
                - 'band:L:U': Banda entre L e U (ex: 'band:1.5:4.5')
            **kwargs: Argumentos extras para matplotlib.

        Returns:
            PlotResult com metodos .save(), .show() e acesso ao axes.

        Example:
            >>> df.chartkit.plot(metrics=['ath', 'ma:12']).save('chart.png')
        """
        config = get_config()

        # 1. Setup inicial (Style)
        theme.apply()
        fig, ax = plt.subplots(figsize=config.layout.figsize)
        self._fig = fig
        self._ax = ax

        # 2. Resolucao de dados
        x_data = self.df.index if x is None else self.df[x]

        if y is None:
            y_data = self.df.select_dtypes(include=["number"])
        else:
            y_data = self.df[y]

        # 3. Aplica formatter ANTES da plotagem
        self._apply_y_formatter(ax, units)

        # 4. Plotagem Core
        if kind == "line":
            plot_line(ax, x_data, y_data, highlight_last, **kwargs)
        elif kind == "bar":
            plot_bar(
                ax, x_data, y_data, highlight=highlight_last, y_origin=y_origin, **kwargs
            )
        else:
            raise ValueError(f"Chart type '{kind}' not supported.")

        # 5. Aplica metricas
        if metrics:
            MetricRegistry.apply(ax, x_data, y_data, metrics)

        # 6. Resolver colisoes de labels
        resolve_collisions(ax)

        # 7. Aplicacao de Componentes e Decoracoes
        self._apply_title(ax, title)
        self._apply_decorations(fig, source)

        # 8. Output
        if save_path:
            self.save(save_path)

        return PlotResult(fig=self._fig, ax=ax, plotter=self)

    def _apply_y_formatter(self, ax, units: str | None) -> None:
        """
        Aplica formatador no eixo Y baseado na unidade especificada.

        Args:
            ax: Matplotlib Axes onde o formatador sera aplicado.
            units: Identificador da unidade ('BRL', 'USD', '%', 'human', 'points')
                ou None para usar formatacao padrao.
        """
        if units and units in _FORMATTERS:
            ax.yaxis.set_major_formatter(_FORMATTERS[units]())

    def _apply_title(self, ax, title: str | None) -> None:
        """
        Aplica titulo centralizado no topo do grafico.

        Args:
            ax: Matplotlib Axes onde o titulo sera aplicado.
            title: Texto do titulo ou None para nao exibir titulo.
        """
        if title:
            config = get_config()
            ax.set_title(
                title,
                loc="center",
                pad=config.layout.title.padding,
                fontproperties=theme.font,
                size=config.fonts.sizes.title,
                color=theme.colors.text,
                weight=config.layout.title.weight,
            )

    def _apply_decorations(self, fig, source: str | None) -> None:
        """
        Aplica decoracoes visuais finais ao grafico.

        Args:
            fig: Matplotlib Figure onde as decoracoes serao aplicadas.
            source: Fonte dos dados para exibir no rodape.
        """
        add_footer(fig, source)

    def save(self, path: str, dpi: int | None = None) -> None:
        """
        Salva o grafico atual em arquivo.

        Args:
            path: Caminho do arquivo (ex: 'grafico.png').
            dpi: Resolucao em DPI (default: config.layout.dpi).

        Raises:
            RuntimeError: Se nenhum grafico foi gerado ainda.
        """
        if self._fig is None:
            raise RuntimeError("Nenhum grafico gerado. Chame plot() primeiro.")

        config = get_config()

        if dpi is None:
            dpi = config.layout.dpi

        path_obj = Path(path)
        if not path_obj.is_absolute():
            charts_path = get_charts_path()
            charts_path.mkdir(parents=True, exist_ok=True)
            path_obj = charts_path / path_obj

        self._fig.savefig(path_obj, bbox_inches="tight", dpi=dpi)
