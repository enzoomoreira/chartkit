"""Custom font loading."""

from __future__ import annotations

from pathlib import Path

import matplotlib.font_manager as fm
from loguru import logger

from ..settings import get_assets_path, get_config

__all__ = ["clear_font_cache", "load_font"]

# fontManager.addfont() does not deduplicate, so reloading the same file on
# every chart grows matplotlib's font list for the lifetime of the process
# and slowly degrades font resolution for everything else running in it.
_FONT_CACHE: dict[tuple[str, str], fm.FontProperties] = {}


def clear_font_cache() -> None:
    """Drop cached fonts so a changed file is picked up again."""
    _FONT_CACHE.clear()


def load_font() -> fm.FontProperties:
    """Load the custom font configured in settings.

    Path resolution:
    - Absolute: used directly
    - Relative: resolved against assets_path
    - Empty: uses fallback (default: sans-serif)
    """
    config = get_config()
    font_file = config.fonts.file
    fallback = config.fonts.fallback

    if not font_file:
        logger.debug("No font configured, using fallback")
        return fm.FontProperties(family=[fallback])

    font_path = Path(font_file)
    if not font_path.is_absolute():
        font_path = get_assets_path() / font_file
        logger.debug("Resolving relative font: {} -> {}", font_file, font_path)

    key = (str(font_path), fallback)
    cached = _FONT_CACHE.get(key)
    if cached is not None:
        return cached

    _FONT_CACHE[key] = _load_from_path(font_path, fallback)
    return _FONT_CACHE[key]


def _load_from_path(font_path: Path, fallback: str) -> fm.FontProperties:
    if not font_path.exists():
        logger.warning(
            "Font not found: {}. Using fallback: {}",
            font_path,
            fallback,
        )
        return fm.FontProperties(family=[fallback])

    try:
        fm.fontManager.addfont(str(font_path))
        logger.info("Font loaded: {}", font_path)
        return fm.FontProperties(fname=str(font_path))
    except Exception as e:
        logger.warning("Error loading font {}: {}", font_path, e)
        return fm.FontProperties(family=[fallback])
