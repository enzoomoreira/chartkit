from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from loguru import logger

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from .engine import ChartingPlotter


@dataclass
class PlotResult:
    """Plot result with method chaining.

    Wraps matplotlib Figure/Axes. Use ``.save()``/``.show()``
    for output and ``.axes``/``.figure`` for manual customization.
    """

    fig: Figure
    ax: Axes
    plotter: ChartingPlotter

    def save(self, path: str, dpi: int | None = None) -> PlotResult:
        """Save the chart to a file.

        Args:
            path: If relative, saves to the configured charts directory.
        """
        self.plotter.save(path, dpi=dpi)
        return self

    def show(self) -> PlotResult:
        """Display the chart in an interactive window."""
        logger.debug("PlotResult.show: '{}'", self.ax.get_title() or "Untitled")
        plt.show()
        return self

    @property
    def axes(self) -> Axes:
        return self.ax

    @property
    def figure(self) -> Figure:
        return self.fig

    def _ipython_display_(self, **kwargs: object) -> None:
        # No-op: matplotlib's inline backend already renders the figure.
        pass

    def __repr__(self) -> str:
        return f"<PlotResult: {self.ax.get_title() or 'Untitled'}>"
