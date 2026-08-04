"""Renderer access that does not depend on the active matplotlib backend.

Measuring text and artist extents requires a renderer. ``canvas.get_renderer()``
is only defined on Agg-derived canvases, so calling it directly makes every
chart fail under the pdf, svg and ps backends -- exactly the ones used for
headless report generation.

Figures created by chartkit own an Agg canvas, so the fast path always
applies. The fallback covers figures that reached us on some other canvas,
which happens after ``PlotResult.show()`` hands a figure to an interactive
backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from matplotlib.backends.backend_agg import RendererAgg

if TYPE_CHECKING:
    from matplotlib.backend_bases import RendererBase
    from matplotlib.figure import Figure

__all__ = ["get_renderer"]


def get_renderer(fig: Figure) -> RendererBase:
    """Return a renderer able to measure artists on *fig*."""
    canvas_getter = getattr(fig.canvas, "get_renderer", None)
    if canvas_getter is not None:
        return canvas_getter()

    # A standalone renderer measures identically without swapping the
    # figure's canvas, which would corrupt the caller's backend.
    width, height = fig.get_size_inches()
    return RendererAgg(int(width * fig.dpi), int(height * fig.dpi), fig.dpi)
