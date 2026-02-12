"""Centralized configuration via TOML or programmatic API.

Precedence: configure() > .charting.toml > pyproject.toml [tool.charting]
> ~/.config/charting/config.toml > built-in defaults.
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
