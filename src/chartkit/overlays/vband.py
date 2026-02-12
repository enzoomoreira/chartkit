import pandas as pd
from loguru import logger
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
    """Add vertical shaded band between two dates.

    Useful for marking recession periods, crises, policy changes, etc.

    Args:
        start: Period start date (parseable string or Timestamp).
        end: Period end date (parseable string or Timestamp).
    """
    config = get_config()

    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)

    if start_ts > end_ts:
        logger.warning("vband: start ({}) is after end ({})", start_ts, end_ts)

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
