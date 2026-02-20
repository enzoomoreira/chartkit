"""
Internal library utilities.

This module contains helper functions that are not part of the public API.
Do not import directly from this module in external code.
"""

from .collision import (
    register_artist_obstacle,
    register_moveable,
    register_passive,
    resolve_collisions,
    resolve_composed_collisions,
)
from .extraction import (
    extract_plot_data,
    resolve_series,
    should_show_legend,
)
from .formatting import FORMATTERS
from .highlight import normalize_highlight
from .pipeline import apply_legend, create_figure, finalize_chart
from .plot_validation import coerce_axis_limits, validate_plot_params
from .saving import save_figure
from .tick_formatting import apply_tick_formatting
from .tick_rotation import apply_tick_rotation

__all__ = [
    "FORMATTERS",
    "apply_legend",
    "apply_tick_formatting",
    "apply_tick_rotation",
    "coerce_axis_limits",
    "create_figure",
    "extract_plot_data",
    "finalize_chart",
    "normalize_highlight",
    "register_artist_obstacle",
    "register_moveable",
    "register_passive",
    "resolve_collisions",
    "resolve_composed_collisions",
    "resolve_series",
    "save_figure",
    "should_show_legend",
    "validate_plot_params",
]
