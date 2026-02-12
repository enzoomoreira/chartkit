"""
Internal library utilities.

This module contains helper functions that are not part of the public API.
Do not import directly from this module in external code.
"""

from .collision import (
    register_fixed,
    register_line_obstacle,
    register_moveable,
    register_passive,
    resolve_collisions,
    resolve_composed_collisions,
)
from .extraction import extract_plot_data, should_show_legend
from .formatting import FORMATTERS
from .highlight import normalize_highlight
from .plot_validation import validate_plot_params
from .saving import save_figure

__all__ = [
    "FORMATTERS",
    "extract_plot_data",
    "normalize_highlight",
    "register_fixed",
    "register_line_obstacle",
    "register_moveable",
    "register_passive",
    "resolve_collisions",
    "resolve_composed_collisions",
    "save_figure",
    "should_show_legend",
    "validate_plot_params",
]
