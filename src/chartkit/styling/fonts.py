"""Custom font loading."""

from pathlib import Path

import matplotlib.font_manager as fm
from loguru import logger

from ..settings import get_assets_path, get_config


def load_font() -> fm.FontProperties:
    """Load custom font configured in settings.

    Path resolution:
    - Absolute: used directly
    - Relative: resolved against assets_path
    - Empty: uses fallback (default: sans-serif)
    """
    config = get_config()
    font_file = config.fonts.file

    if not font_file:
        logger.debug("No font configured, using fallback")
        return fm.FontProperties(family=[config.fonts.fallback])

    font_path = Path(font_file)
    if not font_path.is_absolute():
        assets_path = get_assets_path()
        font_path = assets_path / font_file
        logger.debug("Resolving relative font: {} -> {}", font_file, font_path)

    if font_path.exists():
        try:
            fm.fontManager.addfont(str(font_path))
            logger.info("Font loaded: {}", font_path)
            return fm.FontProperties(fname=str(font_path))
        except Exception as e:
            logger.warning("Error loading font {}: {}", font_path, e)
            return fm.FontProperties(family=[config.fonts.fallback])

    logger.warning(
        "Font not found: {}. Using fallback: {}",
        font_path,
        config.fonts.fallback,
    )
    return fm.FontProperties(family=[config.fonts.fallback])
