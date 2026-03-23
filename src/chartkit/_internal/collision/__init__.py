"""Generic collision resolution engine.

Works with unified path-based collision detection. Extracts geometry
from any matplotlib Artist via matplotlib.path.Path, using
Path.intersects_bbox() (Cython) for precise detection.
"""

from ._engine import (
    _pos_to_numeric,
    draw_composed_debug_overlay,
    draw_debug_overlay,
    resolve_collisions,
    resolve_composed_collisions,
)
from ._obstacles import _PathObstacle, _collect_obstacles
from ._registry import (
    PositionableArtist,
    _artist_obstacles,
    _labels,
    _passive,
    register_artist_obstacle,
    register_moveable,
    register_passive,
)

__all__ = [
    "PositionableArtist",
    "_PathObstacle",
    "_artist_obstacles",
    "_collect_obstacles",
    "_labels",
    "_passive",
    "_pos_to_numeric",
    "draw_composed_debug_overlay",
    "draw_debug_overlay",
    "register_artist_obstacle",
    "register_moveable",
    "register_passive",
    "resolve_collisions",
    "resolve_composed_collisions",
]
