"""Chart title decoration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..settings import get_config
from ..styling.theme import theme

if TYPE_CHECKING:
    from matplotlib.axes import Axes

__all__ = ["add_title"]


def add_title(ax: Axes, title: str | None) -> None:
    """Apply a styled title to the axes."""
    if not title:
        return
    config = get_config()
    ax.set_title(
        title,
        loc="center",
        pad=config.layout.title.padding,
        fontproperties=theme.font,
        size=config.fonts.sizes.title,
        color=theme.colors.text,
        weight=config.layout.title.weight,
    )
