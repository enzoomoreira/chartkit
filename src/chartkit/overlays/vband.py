import pandas as pd
from matplotlib.axes import Axes

from .._internal.collision import register_passive
from ..settings import get_config
from ..styling.theme import theme

__all__ = ["add_vband"]


def add_vband(
    ax: Axes,
    start: str | pd.Timestamp,
    end: str | pd.Timestamp,
    color: str | None = None,
    alpha: float | None = None,
    label: str | None = None,
) -> None:
    """Adiciona banda vertical sombreada entre duas datas.

    Util para marcar periodos de recessao, crises, mudancas de politica, etc.

    Args:
        start: Data de inicio do periodo (string parseable ou Timestamp).
        end: Data de fim do periodo (string parseable ou Timestamp).
    """
    config = get_config()

    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)

    band_color = color if color is not None else theme.colors.grid
    band_alpha = alpha if alpha is not None else config.bands.alpha

    patch = ax.axvspan(
        start_ts,
        end_ts,
        color=band_color,
        alpha=band_alpha,
        label=label,
        zorder=config.layout.zorder.bands,
    )
    register_passive(ax, patch)
