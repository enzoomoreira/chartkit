"""Chart types plugaveis via ChartRegistry. Imports disparam registro automatico."""

from .registry import ChartRegistry
from .bar import plot_bar
from .line import plot_line

__all__ = [
    "ChartRegistry",
    "plot_bar",
    "plot_line",
]
