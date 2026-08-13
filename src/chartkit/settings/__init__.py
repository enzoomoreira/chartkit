"""Centralized configuration via TOML or programmatic API.

Precedence, highest first:

1. ``configure(**overrides)``
2. ``CHARTKIT_*`` environment variables (nested with ``__``, e.g.
   ``CHARTKIT_LAYOUT__DPI``)
3. ``configure(config_path=...)``, when given
4. ``.chartkit/config.toml``
5. ``pyproject.toml`` under ``[tool.chartkit]``
6. The user config directory -- ``%APPDATA%/chartkit/config.toml`` on Windows,
   ``~/.config/chartkit/config.toml`` elsewhere
7. Built-in defaults

Set ``CHARTKIT_NO_AUTO_CONFIG=1`` to skip steps 4 to 6 entirely, leaving only
explicit configuration and environment variables.
"""

from .loader import (
    configure,
    get_assets_path,
    get_charts_path,
    get_config,
    get_outputs_path,
    reset_config,
)
from .schema import ChartingConfig

__all__ = [
    "configure",
    "get_config",
    "reset_config",
    "get_outputs_path",
    "get_charts_path",
    "get_assets_path",
    "ChartingConfig",
]
