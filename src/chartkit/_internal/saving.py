"""Shared chart saving logic."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from ..settings import get_charts_path, get_config

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from matplotlib.figure import Figure

__all__ = ["save_figure"]


def save_figure(
    fig: Figure,
    path: str,
    dpi: int | None = None,
    bbox_inches: str | None = None,
) -> None:
    """Save a matplotlib figure, resolving relative paths to charts directory.

    Args:
        fig: Figure to write.
        path: Output path. Relative paths resolve against the configured
            charts directory, which is created if missing.
        dpi: Resolution override. ``None`` uses ``layout.dpi``.
        bbox_inches: Bounding box override. ``None`` uses ``layout.save_bbox``.
            Pass ``"standard"`` to keep the figure at exactly ``figsize``.
    """
    config = get_config()
    if dpi is None:
        dpi = config.layout.dpi
    if bbox_inches is None:
        bbox_inches = config.layout.save_bbox

    path_obj = Path(path)
    if not path_obj.is_absolute():
        charts_path = get_charts_path()
        charts_path.mkdir(parents=True, exist_ok=True)
        path_obj = charts_path / path_obj

    logger.info("Saving: %s (dpi=%s, bbox=%s)", path_obj, dpi, bbox_inches)

    # matplotlib spells "no cropping" as None, not as a string.
    effective_bbox = None if bbox_inches == "standard" else bbox_inches
    fig.savefig(path_obj, bbox_inches=effective_bbox, dpi=dpi)
