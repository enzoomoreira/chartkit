"""Collision state and registration API.

Per-Axes state stored in WeakKeyDictionaries, automatically released by GC.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from weakref import WeakKeyDictionary

from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.transforms import Bbox

_labels: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_passive: WeakKeyDictionary[Axes, list[Artist]] = WeakKeyDictionary()
_artist_obstacles: WeakKeyDictionary[Axes, list[tuple[Artist, bool, bool]]] = (
    WeakKeyDictionary()
)


@runtime_checkable
class PositionableArtist(Protocol):
    """Artist that supports repositioning via get/set_position."""

    def get_position(self) -> tuple[float, float]: ...
    def set_position(self, xy: tuple[float, float]) -> None: ...
    def get_window_extent(self, renderer: RendererBase | None = None) -> Bbox: ...


def register_moveable(ax: Axes, artist: Artist) -> None:
    """Register Artist that can be repositioned by the engine."""
    _labels.setdefault(ax, []).append(artist)


def register_artist_obstacle(
    ax: Axes, artist: Artist, *, filled: bool = False, colocate: bool = False
) -> None:
    """Register an Artist whose geometry should repel moveable labels.

    The artist's actual path is extracted and used for precise collision
    detection via ``Path.intersects_bbox()``.

    Args:
        filled: ``True`` for shapes (bars, wedges), ``False`` for lines.
        colocate: ``True`` for data lines where labels naturally start ON
            the line. The co-location skip allows the label to remain at
            its origin without being repelled by the line it belongs to.
    """
    _artist_obstacles.setdefault(ax, []).append((artist, filled, colocate))


def register_passive(ax: Axes, artist: Artist) -> None:
    """Register Artist that does not participate in collision resolution.

    Auto-detected patches and collections are treated as obstacles by
    default. Use this to exclude background visuals (bands, shaded areas).
    """
    _passive.setdefault(ax, []).append(artist)
