"""
Resultado de plotagem que permite method chaining.

Encapsula Figure e Axes do matplotlib, expondo metodos
para salvar, mostrar e configurar o grafico de forma encadeavel.

Uso:
    result = df.chartkit.plot()
    result.save('chart.png').show()

    # Acesso ao Axes (backwards compatibility)
    ax = result.axes
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from .engine import ChartingPlotter


@dataclass
class PlotResult:
    """
    Resultado de plotagem que permite method chaining.

    Encapsula a figura e axes do matplotlib, expondo metodos
    para salvar, mostrar e configurar o grafico.

    Attributes:
        fig: Matplotlib Figure.
        ax: Matplotlib Axes.
        plotter: Referencia ao ChartingPlotter para acesso a config.

    Example:
        >>> result = df.chartkit.plot(title='Meu Grafico')
        >>> result.save('chart.png').show()

        >>> # Acesso ao Axes para customizacao manual
        >>> result.axes.set_xlim([...])
    """

    fig: Figure
    ax: Axes
    plotter: ChartingPlotter

    def save(self, path: str, dpi: int | None = None) -> PlotResult:
        """
        Salva o grafico em arquivo.

        Args:
            path: Caminho do arquivo (ex: 'grafico.png').
                  Se relativo, salva no diretorio de charts configurado.
            dpi: Resolucao em DPI (default: config.layout.dpi).

        Returns:
            Self para encadeamento.

        Example:
            >>> df.chartkit.plot().save('chart.png')
            >>> df.chartkit.plot().save('chart.png', dpi=150).show()
        """
        self.plotter.save(path, dpi=dpi)
        return self

    def show(self) -> PlotResult:
        """
        Exibe o grafico em janela interativa.

        Returns:
            Self para encadeamento.

        Example:
            >>> df.chartkit.plot().show()
            >>> df.chartkit.plot().save('chart.png').show()
        """
        plt.show()
        return self

    @property
    def axes(self) -> Axes:
        """
        Acesso direto ao Matplotlib Axes.

        Util para customizacoes manuais e backwards compatibility
        com codigo que espera um Axes.

        Returns:
            Matplotlib Axes.

        Example:
            >>> result = df.chartkit.plot()
            >>> result.axes.set_xlim(['2020-01-01', '2024-12-31'])
            >>> result.axes.axhline(5, color='red')
        """
        return self.ax

    @property
    def figure(self) -> Figure:
        """
        Acesso direto ao Matplotlib Figure.

        Returns:
            Matplotlib Figure.

        Example:
            >>> result = df.chartkit.plot()
            >>> result.figure.set_size_inches(12, 6)
        """
        return self.fig

    def __repr__(self) -> str:
        """Representacao amigavel do resultado."""
        return f"<PlotResult: {self.ax.get_title() or 'Untitled'}>"
