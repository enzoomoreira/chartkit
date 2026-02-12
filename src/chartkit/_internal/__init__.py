"""
Internal library utilities.

This module contains helper functions that are not part of the public API.
Do not import directly from this module in external code.
"""

from .collision import (
    register_fixed,
    register_moveable,
    register_passive,
    resolve_collisions,
)

__all__ = [
    "register_fixed",
    "register_moveable",
    "register_passive",
    "resolve_collisions",
]
