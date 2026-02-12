"""Shared chart saving logic."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from ..settings import get_charts_path, get_config

if TYPE_CHECKING:
    from matplotlib.figure import Figure

__all__ = ["save_figure"]


def save_figure(fig: Figure, path: str, dpi: int | None = None) -> None:
    """Save a matplotlib figure, resolving relative paths to charts directory."""
    config = get_config()
    if dpi is None:
        dpi = config.layout.dpi

    path_obj = Path(path)
    if not path_obj.is_absolute():
        charts_path = get_charts_path()
        charts_path.mkdir(parents=True, exist_ok=True)
        path_obj = charts_path / path_obj

    logger.info("Saving: {} (dpi={})", path_obj, dpi)
    fig.savefig(path_obj, bbox_inches="tight", dpi=dpi)
