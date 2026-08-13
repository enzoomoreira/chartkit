"""Path-based obstacle representation, factory functions, and collectors."""

from __future__ import annotations

import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.path import Path as MplPath
from matplotlib.transforms import Affine2D, Bbox

from ._registry import _artist_obstacles, _labels, _passive


class _PathObstacle:
    """Unified path-based collision obstacle for any matplotlib Artist."""

    __slots__ = (
        "_ax",
        "_artist",
        "_display_paths",
        "_path_extents",
        "_extent_array",
        "_hull",
        "_filled",
        "_colocate",
        "_debug_color",
        "_source_id",
    )

    def __init__(
        self,
        ax: Axes,
        artist: Artist,
        display_paths: list[MplPath],
        *,
        filled: bool,
        colocate: bool = False,
        debug_color: str,
    ) -> None:
        self._ax = ax
        self._artist = artist
        self._display_paths = display_paths
        self._filled = filled
        self._colocate = colocate
        self._debug_color = debug_color
        self._source_id = id(artist)

        # The paths are already in display space and never move, so their
        # extents are computed once here. They used to be recomputed on every
        # intersects() call -- once per path, per candidate position, per
        # label, per iteration, which is what made a scatter unusable.
        self._path_extents = [_vertex_extents(p) for p in display_paths]
        if self._path_extents:
            self._extent_array = np.array(
                [[e.x0, e.y0, e.x1, e.y1] for e in self._path_extents], dtype=float
            )
            self._hull: Bbox | None = Bbox.from_extents(
                float(self._extent_array[:, 0].min()),
                float(self._extent_array[:, 1].min()),
                float(self._extent_array[:, 2].max()),
                float(self._extent_array[:, 3].max()),
            )
        else:
            self._extent_array = np.empty((0, 4), dtype=float)
            self._hull = None

    def intersects(
        self, bbox: Bbox, renderer: RendererBase, padding: float = 0.0
    ) -> bool:
        if self._hull is None:
            return False

        test_bbox = _pad_bbox(bbox, padding) if padding > 0 else bbox

        # One comparison against the hull rejects the whole obstacle, which is
        # the common case: a label sits far from most of a scatter cloud.
        if not self._hull.overlaps(test_bbox):
            return False

        # Vectorised overlap test picks out the few candidate paths, so the
        # exact intersects_bbox() runs on those rather than on all of them.
        extents = self._extent_array
        near = (
            (extents[:, 0] < test_bbox.x1)
            & (extents[:, 2] > test_bbox.x0)
            & (extents[:, 1] < test_bbox.y1)
            & (extents[:, 3] > test_bbox.y0)
        )
        for index in np.flatnonzero(near):
            if self._display_paths[index].intersects_bbox(
                test_bbox, filled=self._filled
            ):
                return True
        return False

    def local_bbox(
        self, label_bbox: Bbox, margin: float, renderer: RendererBase
    ) -> Bbox:
        """Bbox of the obstacle near the label, for displacement generation."""
        if self._filled:
            return self._hull if self._hull is not None else label_bbox
        # Unfilled: only vertices near the label (for lines)
        x_lo = label_bbox.x0 - margin
        x_hi = label_bbox.x1 + margin
        x_mins: list[float] = []
        y_mins: list[float] = []
        x_maxes: list[float] = []
        y_maxes: list[float] = []
        for path in self._display_paths:
            verts = path.vertices
            mask = (verts[:, 0] >= x_lo) & (verts[:, 0] <= x_hi)
            local = verts[mask]
            if len(local) > 0:
                x_mins.append(float(local[:, 0].min()))
                y_mins.append(float(local[:, 1].min()))
                x_maxes.append(float(local[:, 0].max()))
                y_maxes.append(float(local[:, 1].max()))
        if not x_mins:
            return label_bbox
        return Bbox.from_extents(min(x_mins), min(y_mins), max(x_maxes), max(y_maxes))


# -- Geometry helpers --


def _vertex_extents(path: MplPath) -> Bbox:
    """Bounding box of a path's control points.

    ``Path.get_extents()`` solves for the exact Bezier extrema, which costs a
    polynomial root-find per segment -- on a scatter, whose markers are curved,
    that dominated everything else the collision engine did. The control-point
    hull always contains the curve, so this is conservative: an obstacle may
    read a pixel or two larger than it draws, which pushes labels away rather
    than letting them overlap.
    """
    verts = path.vertices
    if len(verts) == 0:
        return Bbox.from_extents(0.0, 0.0, 0.0, 0.0)
    return Bbox.from_extents(
        float(verts[:, 0].min()),
        float(verts[:, 1].min()),
        float(verts[:, 0].max()),
        float(verts[:, 1].max()),
    )


def _pad_bbox(bbox: Bbox, padding_px: float) -> Bbox:
    """Expand a raw Bbox by a fixed padding on all sides."""
    return Bbox.from_extents(
        bbox.x0 - padding_px,
        bbox.y0 - padding_px,
        bbox.x1 + padding_px,
        bbox.y1 + padding_px,
    )


def _shift_bbox(bbox: Bbox, dx: float, dy: float) -> Bbox:
    """Translate a Bbox by (dx, dy) pixels."""
    return Bbox.from_extents(bbox.x0 + dx, bbox.y0 + dy, bbox.x1 + dx, bbox.y1 + dy)


# -- Factory functions --


def _bbox_to_path(bbox: Bbox) -> MplPath:
    """Convert a Bbox to a closed rectangular Path in the same coordinates."""
    return MplPath(
        [
            [bbox.x0, bbox.y0],
            [bbox.x1, bbox.y0],
            [bbox.x1, bbox.y1],
            [bbox.x0, bbox.y1],
            [bbox.x0, bbox.y0],
        ]
    )


def _path_from_line(ax: Axes, line: Artist) -> _PathObstacle:
    """Extract display-space path from a Line2D."""
    data_path = line.get_path()
    transform = line.get_transform()
    vertices = transform.transform(data_path.vertices)
    display_path = MplPath(vertices, data_path.codes)
    return _PathObstacle(ax, line, [display_path], filled=False, debug_color="orange")


def _path_from_patch(ax: Axes, patch: Artist) -> _PathObstacle:
    """Extract display-space path from a Patch (Rectangle, Wedge, etc.).

    ``Patch.get_transform()`` already includes ``get_patch_transform()``,
    so using it directly maps unit path -> data -> display in one step.
    """
    path = patch.get_path()
    display_path = path.transformed(patch.get_transform())
    return _PathObstacle(ax, patch, [display_path], filled=True, debug_color="red")


def _path_from_collection(
    ax: Axes, collection: Artist, renderer: RendererBase
) -> _PathObstacle:
    """Extract display-space paths from a Collection (scatter, etc.)."""
    offsets = collection.get_offsets()

    if len(offsets) == 0:
        return _PathObstacle(ax, collection, [], filled=True, debug_color="purple")

    paths = collection.get_paths()
    if not paths:
        return _PathObstacle(ax, collection, [], filled=True, debug_color="purple")

    element_transforms = collection.get_transforms()
    offset_transform = collection.get_offset_transform()
    display_offsets = offset_transform.transform(offsets)

    display_paths: list[MplPath] = []
    for i, doff in enumerate(display_offsets):
        base = paths[i % len(paths)]
        if len(element_transforms) > 0:
            et = element_transforms[i % len(element_transforms)]
            scaled = base.transformed(Affine2D(et))
        else:
            scaled = base
        translated = scaled.transformed(Affine2D().translate(doff[0], doff[1]))
        display_paths.append(translated)

    return _PathObstacle(
        ax, collection, display_paths, filled=True, debug_color="purple"
    )


def _path_from_extent(
    ax: Axes, artist: Artist, renderer: RendererBase
) -> _PathObstacle:
    """Fallback: use the artist's bounding box as a filled rectangle."""
    extent = artist.get_window_extent(renderer)
    return _PathObstacle(
        ax, artist, [_bbox_to_path(extent)], filled=True, debug_color="red"
    )


# -- Unified type dispatch --


def _classify_artist(
    ax: Axes,
    artist: Artist,
    renderer: RendererBase,
    *,
    filled: bool = False,
    colocate: bool = False,
    debug_color: str | None = None,
) -> _PathObstacle:
    """Convert any Artist to a ``_PathObstacle`` via structural type detection.

    Dispatch order (first match wins):
    1. Collection (``get_paths`` + ``get_offsets``) -> path-per-element
    2. Patch (``get_patch_transform``) -> single transformed path
    3. Line (``get_path`` when not filled) -> display-space polyline
    4. Fallback -> bounding-box rectangle
    """
    if hasattr(artist, "get_paths") and hasattr(artist, "get_offsets"):
        obs = _path_from_collection(ax, artist, renderer)
    elif hasattr(artist, "get_patch_transform"):
        obs = _path_from_patch(ax, artist)
    elif not filled and hasattr(artist, "get_path"):
        obs = _path_from_line(ax, artist)
    else:
        obs = _path_from_extent(ax, artist, renderer)

    obs._colocate = colocate
    if debug_color is not None:
        obs._debug_color = debug_color
    return obs


# -- Obstacle collection --


def _collect_obstacles(
    ax: Axes, moveables: list[Artist], renderer: RendererBase
) -> list[_PathObstacle]:
    """Collect obstacles from patches, collections, and registered artists.

    In composed charts with twinx, labels from one axis must also avoid
    patches, collections, labels and line paths on the sibling axis.
    """
    moveable_ids = {id(m) for m in moveables}
    sibling_axes = list(ax.get_shared_x_axes().get_siblings(ax))
    passive_ids = {id(p) for sibling in sibling_axes for p in _passive.get(sibling, [])}
    seen: set[int] = set()
    obstacles: list[_PathObstacle] = []

    def _should_include(artist: Artist) -> bool:
        aid = id(artist)
        if aid in moveable_ids or aid in passive_ids or aid in seen:
            return False
        if not artist.get_visible():
            return False
        seen.add(aid)
        return True

    # 1-3. Auto-detect from sibling axes
    for sibling in sibling_axes:
        for patch in sibling.patches:
            if _should_include(patch):
                obstacles.append(_path_from_patch(sibling, patch))

        for collection in sibling.collections:
            if _should_include(collection):
                obstacles.append(_path_from_collection(sibling, collection, renderer))

        if sibling is not ax:
            for label in _labels.get(sibling, []):
                if _should_include(label):
                    obstacles.append(_path_from_extent(sibling, label, renderer))

    # 4. Explicitly registered artist obstacles -> unified dispatch
    for sibling in sibling_axes:
        for artist, filled, colocate in _artist_obstacles.get(sibling, []):
            if not artist.get_visible():
                continue
            aid = id(artist)
            if aid in seen or aid in passive_ids:
                continue
            seen.add(aid)
            obstacles.append(
                _classify_artist(
                    sibling, artist, renderer, filled=filled, colocate=colocate
                )
            )

    return obstacles


def _collect_passive_obstacles(ax: Axes, renderer: RendererBase) -> list[_PathObstacle]:
    """Collect passive artists as obstacles for debug visualization."""
    sibling_axes = list(ax.get_shared_x_axes().get_siblings(ax))
    obstacles: list[_PathObstacle] = []
    seen: set[int] = set()

    for sibling in sibling_axes:
        for artist in _passive.get(sibling, []):
            aid = id(artist)
            if aid in seen or not artist.get_visible():
                continue
            seen.add(aid)
            obs = _classify_artist(sibling, artist, renderer, debug_color="gray")
            obstacles.append(obs)

    return obstacles
