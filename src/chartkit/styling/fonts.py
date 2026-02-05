"""Carregamento de fontes customizadas."""

from pathlib import Path

import matplotlib.font_manager as fm
from loguru import logger

from ..settings import get_assets_path, get_config


def load_font() -> fm.FontProperties:
    """Carrega fonte customizada configurada em settings.

    Resolucao do caminho:
    - Absoluto: usa diretamente
    - Relativo: resolve contra assets_path
    - Vazio: usa fallback (default: sans-serif)
    """
    config = get_config()
    font_file = config.fonts.file

    if not font_file:
        logger.debug("Nenhuma fonte configurada, usando fallback")
        return fm.FontProperties(family=[config.fonts.fallback])

    font_path = Path(font_file)
    if not font_path.is_absolute():
        assets_path = get_assets_path()
        font_path = assets_path / font_file
        logger.debug("Resolvendo fonte relativa: {} -> {}", font_file, font_path)

    if font_path.exists():
        try:
            fm.fontManager.addfont(str(font_path))
            logger.info("Fonte carregada: {}", font_path)
            return fm.FontProperties(fname=str(font_path))
        except Exception as e:
            logger.warning("Erro ao carregar fonte {}: {}", font_path, e)
            return fm.FontProperties(family=[config.fonts.fallback])

    logger.warning(
        "Fonte nao encontrada: {}. Usando fallback: {}",
        font_path,
        config.fonts.fallback,
    )
    return fm.FontProperties(family=[config.fonts.fallback])
