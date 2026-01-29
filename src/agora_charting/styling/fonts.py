"""
Carregamento de fontes customizadas para graficos.
"""

import matplotlib.font_manager as fm
from pathlib import Path

from ..settings import get_config


# Caminho base para assets (relativo ao modulo)
ASSETS_PATH = Path(__file__).parent.parent / "assets"


def load_font() -> fm.FontProperties:
    """
    Carrega fonte customizada para graficos.

    Busca o arquivo de fonte configurado em settings. O caminho pode ser:
    - Relativo a pasta assets/ (ex: 'fonts/MeuFont.ttf')
    - Absoluto (ex: '/usr/share/fonts/custom.ttf')

    Returns:
        FontProperties da fonte se disponivel, caso contrario
        fallback para a fonte configurada (default: sans-serif).
    """
    config = get_config()
    font_file = config.fonts.file

    # Verifica se e caminho absoluto ou relativo
    font_path = Path(font_file)
    if not font_path.is_absolute():
        font_path = ASSETS_PATH / font_file

    if font_path.exists():
        fm.fontManager.addfont(str(font_path))
        return fm.FontProperties(fname=str(font_path))

    return fm.FontProperties(family=config.fonts.fallback)
