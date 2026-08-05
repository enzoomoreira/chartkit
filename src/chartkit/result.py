"""Chainable plot result wrapping a matplotlib Figure/Axes pair."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from types import TracebackType

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


__all__ = ["PlotResult"]


@dataclass
class PlotResult:
    """Plot result with method chaining.

    Wraps matplotlib Figure/Axes. Use ``.save()``/``.show()``
    for output and ``.axes``/``.figure`` for manual customization.

    The figure is not registered with ``pyplot``, so it is released as soon
    as the result goes out of scope. Use ``.close()`` -- or the context
    manager form -- to release it eagerly when generating charts in a loop,
    and after ``.show()``, which does hand the figure to pyplot.
    """

    fig: Figure
    ax: Axes

    def save(self, path: str, dpi: int | None = None) -> PlotResult:
        """Save the chart to a file. Returns ``self`` for chaining.

        Saves ``self.fig``. Routing this through the plotter that built the
        chart used to mean a reused plotter wrote whichever figure it had
        drawn most recently, not this one.

        Args:
            path: Output file path. If relative, saves to the configured
                charts directory. Format is inferred from extension
                (``.png``, ``.jpg``, ``.svg``, ``.pdf``).
            dpi: Resolution override. ``None`` uses config ``layout.dpi``.
        """
        from ._internal.saving import save_figure

        save_figure(self.fig, path, dpi)
        return self

    def show(self) -> PlotResult:
        """Display the chart in an interactive window.

        Hands the figure to pyplot, which then keeps a reference to it, so
        call ``.close()`` afterwards in long-running sessions.
        """
        import matplotlib.pyplot as plt

        logger.debug("PlotResult.show: '%s'", self.ax.get_title() or "Untitled")

        # The figure was built outside pyplot, so it has no manager of its
        # own; borrow one from a throwaway figure.
        manager = plt.figure().canvas.manager
        if manager is not None:
            manager.canvas.figure = self.fig
            self.fig.set_canvas(manager.canvas)

        plt.show()
        return self

    def close(self) -> None:
        """Release the figure and its artists."""
        import matplotlib.pyplot as plt

        # No-op when the figure never reached pyplot, which is the common case.
        plt.close(self.fig)
        self.fig.clear()

    def __enter__(self) -> PlotResult:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    @property
    def axes(self) -> Axes:
        """The matplotlib Axes for manual customization."""
        return self.ax

    @property
    def figure(self) -> Figure:
        """The matplotlib Figure for manual customization."""
        return self.fig

    def describe(self, *, geometry: bool = False) -> dict[str, Any]:
        """Serialise the chart structure as plain data.

        Reports every rendering decision -- series, colours, styles, labels,
        limits and ticks -- for each Axes in the figure, so a chart can be
        asserted on and diffed without rasterising it.

        Args:
            geometry: Also report measured bounding boxes and the pairs of
                labels whose extents intersect. These depend on font
                rasterisation, so use them for live inspection rather than
                as a stored baseline.
        """
        from ._internal.introspection import describe_figure

        return describe_figure(self.fig, geometry=geometry)

    def explain(self) -> str:
        """Describe the chart as text meant to be read in a terminal.

        Same information as ``describe(geometry=True)``, formatted for
        reading rather than for parsing.
        """
        from ._internal.introspection import explain_figure

        return explain_figure(self.fig)

    def _repr_png_(self) -> bytes | None:
        """Render inline in Jupyter.

        The figure is not managed by pyplot, so the inline backend never sees
        it; without this the notebook would only show the repr string.
        """
        from io import BytesIO

        buffer = BytesIO()
        self.fig.savefig(buffer, format="png", bbox_inches="tight")
        return buffer.getvalue()

    def __repr__(self) -> str:
        return f"<PlotResult: {self.ax.get_title() or 'Untitled'}>"
