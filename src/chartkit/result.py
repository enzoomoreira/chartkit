"""Chainable plot result wrapping a matplotlib Figure/Axes pair."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from loguru import logger

if TYPE_CHECKING:
    from types import TracebackType

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


class Saveable(Protocol):
    def save(self, path: str, dpi: int | None = None) -> None: ...


__all__ = ["PlotResult", "Saveable"]


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
    plotter: Saveable

    def save(self, path: str, dpi: int | None = None) -> PlotResult:
        """Save the chart to a file. Returns ``self`` for chaining.

        Args:
            path: Output file path. If relative, saves to the configured
                charts directory. Format is inferred from extension
                (``.png``, ``.jpg``, ``.svg``, ``.pdf``).
            dpi: Resolution override. ``None`` uses config ``layout.dpi``.
        """
        self.plotter.save(path, dpi=dpi)
        return self

    def show(self) -> PlotResult:
        """Display the chart in an interactive window.

        Hands the figure to pyplot, which then keeps a reference to it, so
        call ``.close()`` afterwards in long-running sessions.
        """
        import matplotlib.pyplot as plt

        logger.debug("PlotResult.show: '{}'", self.ax.get_title() or "Untitled")

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
