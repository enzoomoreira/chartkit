"""
Bandas sombreadas para graficos.
"""

from ..settings import get_config
from ..styling.theme import theme


def add_band(
    ax,
    lower: float,
    upper: float,
    color: str = None,
    alpha: float = None,
    label: str = None,
) -> None:
    """
    Adiciona area sombreada entre dois valores horizontais.

    Util para representar bandas de tolerancia, intervalos de confianca,
    ou faixas de referencia.

    Args:
        ax: Matplotlib Axes
        lower: Limite inferior da banda
        upper: Limite superior da banda
        color: Cor da banda (default: config.colors.grid)
        alpha: Transparencia da banda (default: config.bands.alpha)
        label: Rotulo para legenda (opcional)

    Example:
        >>> # Banda de meta de inflacao (1.5% a 4.5%)
        >>> add_band(ax, 1.5, 4.5, color='green', alpha=0.1, label='Meta')
    """
    config = get_config()

    # Valores default da config
    band_color = color if color else theme.colors.grid
    band_alpha = alpha if alpha is not None else config.bands.alpha

    ax.axhspan(
        lower,
        upper,
        color=band_color,
        alpha=band_alpha,
        label=label,
        zorder=0,  # Abaixo de tudo
    )
