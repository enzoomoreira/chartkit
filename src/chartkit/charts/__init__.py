"""
Tipos de graficos.

Este modulo contem as funcoes de renderizacao para cada tipo de grafico
suportado pela biblioteca.
"""

from .line import plot_line
from .bar import plot_bar

__all__ = [
    "plot_line",
    "plot_bar",
]
