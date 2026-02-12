"""Pluggable chart types via ChartRegistry. Imports trigger automatic registration."""

from .registry import ChartRegistry
from .bar import plot_bar
from .line import plot_line
from .stacked_bar import plot_stacked_bar

__all__ = [
    "ChartRegistry",
    "plot_bar",
    "plot_line",
    "plot_stacked_bar",
]
