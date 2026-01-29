"""
Tema visual para graficos.

Gerencia cores, fontes e estilos do matplotlib de forma centralizada,
usando configuracoes do modulo settings.
"""

from typing import Optional

import matplotlib.pyplot as plt

from .fonts import load_font
from ..settings import get_config
from ..settings.schema import ColorsConfig


class ChartingTheme:
    """
    Gerencia a identidade visual dos graficos.

    Esta classe encapsula todas as configuracoes visuais padronizadas:
    paleta de cores, fonte customizada e parametros do matplotlib
    para consistencia visual.

    O tema usa lazy loading para acessar configuracoes, permitindo
    que mudancas via configure() sejam refletidas automaticamente.

    Attributes:
        font: FontProperties do matplotlib com a fonte carregada.

    Example:
        >>> from chartkit.styling.theme import theme
        >>> theme.apply()  # Aplica tema globalmente
        >>> print(theme.colors.primary)
    """

    def __init__(self) -> None:
        """
        Inicializa o tema com configuracoes lazy-loaded.

        A fonte e carregada imediatamente pois precisa ser registrada
        no matplotlib.font_manager.
        """
        self._font = None

    @property
    def font(self):
        """
        Retorna FontProperties configurada para o tema.

        Usa lazy loading para permitir que configuracoes sejam
        alteradas via configure() antes do primeiro uso.
        """
        if self._font is None:
            self._font = load_font()
        return self._font

    @property
    def colors(self) -> ColorsConfig:
        """
        Retorna a paleta de cores atual.

        Acessa a configuracao dinamicamente, permitindo que mudancas
        via configure() sejam refletidas.
        """
        return get_config().colors

    @property
    def font_name(self) -> str:
        """
        Retorna o nome da fonte configurada para o tema.

        Returns:
            Nome da fonte carregada ou fallback do sistema
            caso a fonte nao tenha sido encontrada.
        """
        return self.font.get_name()

    def apply(self) -> "ChartingTheme":
        """
        Aplica o tema globalmente no matplotlib.

        Configura rcParams do matplotlib com cores, fontes e layout
        definidos na configuracao atual.

        Returns:
            Self para encadeamento.
        """
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
