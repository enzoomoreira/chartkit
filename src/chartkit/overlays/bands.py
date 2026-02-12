from matplotlib.axes import Axes

from .._internal.collision import register_passive
from ..settings import get_config
from ..styling.theme import theme


def add_band(
    ax: Axes,
    lower: float,
    upper: float,
    color: str | None = None,
    alpha: float | None = None,
    label: str | None = None,
) -> None:
    """Add horizontal shaded area between two values."""
    config = get_config()

    patch = ax.axhspan(
        lower,
        upper,
        color=color if color is not None else theme.colors.grid,
        alpha=alpha if alpha is not None else config.bands.alpha,
        label=label,
        zorder=config.layout.zorder.bands,
    )
    register_passive(ax, patch)
