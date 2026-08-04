"""Visual theme for charts."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import matplotlib as mpl
from matplotlib import style as mpl_style

from ..settings import get_config
from ..settings.schema import ColorsConfig
from .fonts import load_font

if TYPE_CHECKING:
    from collections.abc import Iterator

    from matplotlib.font_manager import FontProperties

__all__ = ["ChartingTheme", "theme"]


class ChartingTheme:
    """Manages the visual identity for charts.

    Singleton that encapsulates colors, fonts, and matplotlib rcParams.
    Configuration is read on every access, so ``configure()`` takes effect
    without any explicit invalidation.
    """

    @property
    def font(self) -> FontProperties:
        """The ``FontProperties`` for the configured font."""
        return load_font()

    @property
    def colors(self) -> ColorsConfig:
        """Active color palette from the current configuration."""
        return get_config().colors

    @property
    def font_name(self) -> str:
        """Resolved font family name for matplotlib rcParams."""
        return self.font.get_name()

    def rc_params(self) -> dict[str, Any]:
        """Return the rcParams that express the configured visual identity."""
        config = get_config()
        return {
            # Fonts
            "font.family": self.font_name,
            "font.size": config.fonts.sizes.default,
            "axes.titlesize": config.fonts.sizes.title,
            "axes.labelsize": config.fonts.sizes.axis_label,
            # Colors
            "text.color": config.colors.text,
            "axes.labelcolor": config.colors.text,
            "xtick.color": config.colors.text,
            "ytick.color": config.colors.text,
            "axes.edgecolor": config.colors.text,
            # Grid
            "axes.grid": config.layout.grid.enabled,
            "axes.grid.axis": config.layout.grid.axis,
            "grid.alpha": config.layout.grid.alpha,
            "grid.color": config.layout.grid.color,
            "grid.linestyle": config.layout.grid.linestyle,
            # Layout
            "figure.figsize": config.layout.figsize,
            "figure.facecolor": config.colors.background,
            "axes.facecolor": config.colors.background,
            "axes.spines.top": config.layout.spines.top,
            "axes.spines.right": config.layout.spines.right,
            "axes.spines.left": config.layout.spines.left,
            "axes.spines.bottom": config.layout.spines.bottom,
        }

    @contextmanager
    def context(self) -> Iterator[None]:
        """Scope the theme to a block instead of mutating global rcParams.

        matplotlib reads rcParams as each artist is created, so the entire
        chart -- figure, render, overlays and decorations -- must be built
        inside this block for the theme to take effect.
        """
        config = get_config()
        with (
            mpl_style.context(config.layout.base_style),
            mpl.rc_context(self.rc_params()),
        ):
            yield


# Global singleton instance
theme = ChartingTheme()
