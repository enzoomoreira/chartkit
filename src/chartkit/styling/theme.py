"""Visual theme for charts."""

import matplotlib.pyplot as plt

from .fonts import load_font
from ..settings import get_config
from ..settings.schema import ColorsConfig


class ChartingTheme:
    """Manages the visual identity for charts.

    Singleton that encapsulates colors, fonts, and matplotlib rcParams.
    Uses lazy loading to reflect changes via ``configure()``.
    """

    def __init__(self) -> None:
        self._font = None

    @property
    def font(self):
        if self._font is None:
            self._font = load_font()
        return self._font

    @property
    def colors(self) -> ColorsConfig:
        return get_config().colors

    @property
    def font_name(self) -> str:
        return self.font.get_name()

    def apply(self) -> "ChartingTheme":
        """Apply the theme globally to matplotlib rcParams."""
        config = get_config()
        plt.style.use(config.layout.base_style)

        rc_params = {
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
            "axes.grid": config.layout.grid,
            # Layout
            "figure.figsize": config.layout.figsize,
            "figure.facecolor": config.colors.background,
            "axes.facecolor": config.colors.background,
            "axes.spines.top": config.layout.spines.top,
            "axes.spines.right": config.layout.spines.right,
            "axes.spines.left": config.layout.spines.left,
            "axes.spines.bottom": config.layout.spines.bottom,
        }

        plt.rcParams.update(rc_params)
        return self


# Global singleton instance
theme = ChartingTheme()
