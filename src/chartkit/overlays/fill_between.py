import pandas as pd
from loguru import logger
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
    """Add shaded area between two series.

    Useful for visualizing spreads, differences between expected and actual,
    confidence intervals, etc.

    Args:
        y1: Lower series (or first series).
        y2: Upper series (or second series).
    """
    config = get_config()

    if len(y1) != len(y2):
        logger.warning(
            "fill_between: y1 ({}) and y2 ({}) have different lengths",
            len(y1),
            len(y2),
        )

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
