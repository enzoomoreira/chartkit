"""Tema visual para graficos."""

import matplotlib.pyplot as plt

from .fonts import load_font
from ..settings import get_config
from ..settings.schema import ColorsConfig


class ChartingTheme:
    """Gerencia a identidade visual dos graficos.

    Singleton que encapsula cores, fontes e rcParams do matplotlib.
    Usa lazy loading para refletir mudancas via ``configure()``.
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
        """Aplica o tema globalmente nos rcParams do matplotlib."""
        config = get_config()
        plt.style.use("seaborn-v0_8-white")

        rc_params = {
            # Fontes
            "font.family": self.font_name,
            "font.size": config.fonts.sizes.default,
            "axes.titlesize": config.fonts.sizes.title,
            "axes.labelsize": config.fonts.sizes.axis_label,
            # Cores
            "text.color": config.colors.text,
            "axes.labelcolor": config.colors.text,
            "xtick.color": config.colors.text,
            "ytick.color": config.colors.text,
            "axes.edgecolor": config.colors.text,
            # Grid desabilitado (apenas axis lines)
            "axes.grid": False,
            # Layout
            "figure.figsize": config.layout.figsize,
            "figure.facecolor": config.colors.background,
            "axes.facecolor": config.colors.background,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": True,
            "axes.spines.bottom": True,
        }

        plt.rcParams.update(rc_params)
        return self


# Instancia global singleton
theme = ChartingTheme()
