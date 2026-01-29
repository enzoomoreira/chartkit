"""
Sistema de configuracao do agora-charting.

Fornece configuracao centralizada via arquivos TOML ou programaticamente.

Locais de busca (ordem de precedencia):
    1. configure(config_path=...) - Caminho explicito
    2. .charting.toml ou charting.toml - Projeto local
    3. pyproject.toml [tool.charting] - Secao no pyproject
    4. ~/.config/charting/config.toml - Usuario global (Linux/Mac)
    5. %APPDATA%/charting/config.toml - Usuario global (Windows)
    6. Defaults built-in

Uso:
    # Sem configuracao (usa defaults)
    >>> from agora_charting.settings import get_config
    >>> config = get_config()
    >>> print(config.colors.primary)

    # Com configuracao programatica
    >>> from agora_charting.settings import configure
    >>> configure(branding={'company_name': 'Minha Empresa'})

    # Com arquivo TOML
    >>> configure(config_path=Path('./minha-config.toml'))
"""

from .loader import (
    configure,
    get_charts_path,
    get_config,
    get_outputs_path,
    reset_config,
)
from .schema import ChartingConfig

__all__ = [
    # Funcoes principais
    "configure",
    "get_config",
    "reset_config",
    # Paths
    "get_outputs_path",
    "get_charts_path",
    # Schema
    "ChartingConfig",
]
