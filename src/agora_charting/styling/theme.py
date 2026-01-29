from dataclasses import dataclass
from typing import List

import matplotlib.pyplot as plt

from .fonts import load_font

@dataclass
class ColorPalette:
    """Paleta de cores para graficos - gradiente institucional verde."""

    # Cores principais (gradiente de verde)
    primary: str = "#00464D"      # Verde escuro institucional
    secondary: str = "#006B6B"    # Verde medio
    tertiary: str = "#008B8B"     # Teal
    quaternary: str = "#20B2AA"   # Light sea green
    quinary: str = "#5F9EA0"      # Cadet blue
    senary: str = "#2E8B57"       # Sea green

    # Cores semanticas
    text: str = "#00464D"
    grid: str = "lightgray"
    background: str = "white"
    positive: str = "#00464D"
    negative: str = "#8B0000"     # Vermelho escuro (discreto)

    def cycle(self) -> List[str]:
        """Retorna lista de cores em gradiente verde para multiplas series."""
        return [
            self.primary,
            self.secondary,
            self.tertiary,
            self.quaternary,
            self.quinary,
            self.senary,
        ]

class AgoraTheme:
    """
    Gerencia a identidade visual dos graficos Agora.

    Esta classe encapsula todas as configuracoes visuais padronizadas:
    paleta de cores institucional, fonte Inter customizada e parametros
    do matplotlib para consistencia visual.

    Attributes:
        colors: Instancia de ColorPalette com cores institucionais.
        font: FontProperties do matplotlib com a fonte Inter carregada.

    Example:
        >>> from agora_charting.styling.theme import theme
        >>> theme.apply()  # Aplica tema globalmente
        >>> print(theme.font_name)  # 'Inter'
    """

    def __init__(self) -> None:
        """
        Inicializa o tema Agora com configuracoes padrao.

        Carrega a fonte Inter do diretorio de assets e configura
        a paleta de cores institucional para visualizacoes.
        """
        self.colors = ColorPalette()
        self.font = load_font()
        
    @property
    def font_name(self) -> str:
        """
        Retorna o nome da fonte configurada para o tema.

        Returns:
            Nome da fonte carregada (Inter) ou fallback do sistema
            caso a fonte nao tenha sido encontrada.
        """
        return self.font.get_name()

    def apply(self):
        """Aplica o tema globalmente no matplotlib."""
        plt.style.use('seaborn-v0_8-white')

        rc_params = {
            # Fontes
            'font.family': self.font_name,
            'font.size': 11,
            'axes.titlesize': 18,  # Titulo maior
            'axes.labelsize': 11,

            # Cores
            'text.color': self.colors.text,
            'axes.labelcolor': self.colors.text,
            'xtick.color': self.colors.text,
            'ytick.color': self.colors.text,
            'axes.edgecolor': self.colors.text,

            # Grid desabilitado (apenas axis lines)
            'axes.grid': False,

            # Layout
            'figure.figsize': (10, 6),
            'figure.facecolor': self.colors.background,
            'axes.facecolor': self.colors.background,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'axes.spines.left': True,
            'axes.spines.bottom': True,
        }

        plt.rcParams.update(rc_params)
        return self

# Instancia global
theme = AgoraTheme()
