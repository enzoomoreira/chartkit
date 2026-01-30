"""
Carregamento de fontes customizadas para graficos.
"""

import logging
from pathlib import Path

import matplotlib.font_manager as fm

from ..settings import get_config
from ..settings.loader import get_assets_path

logger = logging.getLogger(__name__)


def load_font() -> fm.FontProperties:
    """
    Carrega fonte customizada para graficos.

    Busca o arquivo de fonte configurado em settings. O caminho pode ser:
    - Absoluto (ex: '/usr/share/fonts/custom.ttf')
    - Relativo ao assets_path (ex: 'fonts/MeuFont.ttf')
    - Vazio ('') para usar apenas o fallback

    O assets_path e resolvido na seguinte ordem de precedencia:
    1. configure(assets_path=...)
    2. TOML ([fonts].assets_path ou [paths].assets_dir)
    3. Auto-discovery do ASSETS_PATH do projeto host via AST
    4. Fallback: project_root / 'assets' (com warning)

    Returns:
        FontProperties da fonte se disponivel, caso contrario
        fallback para a fonte configurada (default: sans-serif).
    """
    config = get_config()
    font_file = config.fonts.file

    # Se fonte nao configurada, usa fallback diretamente
    if not font_file:
        logger.debug("Nenhuma fonte configurada, usando fallback")
        return fm.FontProperties(family=[config.fonts.fallback])

    # Verifica se e caminho absoluto ou relativo
    font_path = Path(font_file)
    if not font_path.is_absolute():
        assets_path = get_assets_path()
        font_path = assets_path / font_file
        logger.debug(f"Resolvendo fonte relativa: {font_file} -> {font_path}")

    if font_path.exists():
        try:
            fm.fontManager.addfont(str(font_path))
            logger.info(f"Fonte carregada: {font_path}")
            return fm.FontProperties(fname=str(font_path))
        except Exception as e:
            logger.warning(f"Erro ao carregar fonte {font_path}: {e}")
            return fm.FontProperties(family=[config.fonts.fallback])

    logger.warning(
        f"Fonte nao encontrada: {font_path}. "
        f"Usando fallback: {config.fonts.fallback}"
    )
    return fm.FontProperties(family=[config.fonts.fallback])
