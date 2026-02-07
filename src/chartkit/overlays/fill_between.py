import pandas as pd
from matplotlib.axes import Axes

from .._internal.collision import register_passive
from ..settings import get_config
from ..styling.theme import theme

__all__ = ["add_fill_between"]


def add_fill_between(
    ax: Axes,
    x: pd.Index | pd.Series,
    y1: pd.Series,
    y2: pd.Series,
    color: str | None = None,
    alpha: float | None = None,
    label: str | None = None,
) -> None:
    """Adiciona area sombreada entre duas series.

    Util para visualizar spreads, diferencas entre expectativa e realizado,
    intervalos de confianca, etc.

    Args:
        y1: Serie inferior (ou primeira serie).
        y2: Serie superior (ou segunda serie).
    """
    config = get_config()

    fill_color = color if color is not None else theme.colors.primary
    fill_alpha = alpha if alpha is not None else config.bands.alpha

    patch = ax.fill_between(
        x,
        y1,
        y2,
        color=fill_color,
        alpha=fill_alpha,
        label=label,
        zorder=config.layout.zorder.bands,
    )
    register_passive(ax, patch)
