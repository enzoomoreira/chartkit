"""Debug overlay for collision visualization."""

from __future__ import annotations

from collections.abc import Sequence

import matplotlib.patches as mpatches
from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure
from matplotlib.path import Path as MplPath
from matplotlib.transforms import Bbox

from ._obstacles import _PathObstacle, _pad_bbox
from ._registry import PositionableArtist
from ...settings.schema import CollisionConfig

# Named constants for debug visuals
_DEBUG_ZORDER = 100
_BOUNDS_ZORDER = 101
_PASSIVE_FACE_ALPHA = 0.15
_PASSIVE_EDGE_ALPHA = 0.15
_FILLED_FACE_ALPHA = 0.25
_FILLED_EDGE_ALPHA = 0.25
_LINE_FACE_ALPHA = 0.0
_LINE_EDGE_ALPHA = 0.5
_LINE_LW = 4
_SHAPE_LW = 1
_LABEL_ALPHA = 0.3
_BOUNDS_ALPHA = 0.8
_BOUNDS_LW = 2


def _draw_debug_overlay(
    fig: Figure,
    moveables: Sequence[PositionableArtist],
    obstacles: list[_PathObstacle],
    renderer: RendererBase,
    axes_bbox: Bbox,
    collision: CollisionConfig,
    *,
    passive: list[_PathObstacle] | None = None,
) -> None:
    """Draw translucent collision visuals for debugging."""
    label_pad = collision.label_padding_px
    inv = fig.transFigure.inverted()

    def _add_rect(bbox_raw: Bbox, color: str, alpha: float) -> None:
        bbox = Bbox.from_extents(
            max(bbox_raw.x0, axes_bbox.x0),
            max(bbox_raw.y0, axes_bbox.y0),
            min(bbox_raw.x1, axes_bbox.x1),
            min(bbox_raw.y1, axes_bbox.y1),
        )
        if bbox.width <= 0 or bbox.height <= 0:
            return
        p0 = inv.transform((bbox.x0, bbox.y0))
        p1 = inv.transform((bbox.x1, bbox.y1))
        fig.patches.append(
            mpatches.FancyBboxPatch(
                (p0[0], p0[1]),
                p1[0] - p0[0],
                p1[1] - p0[1],
                boxstyle="square,pad=0",
                transform=fig.transFigure,
                facecolor=color,
                edgecolor=color,
                alpha=alpha,
                clip_on=False,
                zorder=_DEBUG_ZORDER,
            )
        )

    def _draw_obstacles(
        obs_list: list[_PathObstacle],
        *,
        linestyle: str = "solid",
    ) -> None:
        for obs in obs_list:
            is_passive = linestyle == "dashed"
            for path in obs._display_paths:
                if obs._filled:
                    draw_path = path.clip_to_bbox(axes_bbox)
                    if len(draw_path.vertices) < 2:
                        continue
                else:
                    draw_path = path
                fig_verts = inv.transform(draw_path.vertices)
                if is_passive:
                    face_alpha = _PASSIVE_FACE_ALPHA
                    edge_alpha = _PASSIVE_EDGE_ALPHA
                    lw = _SHAPE_LW
                elif obs._filled:
                    face_alpha = _FILLED_FACE_ALPHA
                    edge_alpha = _FILLED_EDGE_ALPHA
                    lw = _SHAPE_LW
                else:
                    face_alpha = _LINE_FACE_ALPHA
                    edge_alpha = _LINE_EDGE_ALPHA
                    lw = _LINE_LW
                fig.patches.append(
                    mpatches.PathPatch(
                        MplPath(fig_verts, draw_path.codes),
                        facecolor=obs._debug_color
                        if (obs._filled or is_passive)
                        else "none",
                        edgecolor=obs._debug_color,
                        linewidth=lw,
                        alpha=max(face_alpha, edge_alpha),
                        linestyle=linestyle,
                        joinstyle="round",
                        capstyle="round",
                        transform=fig.transFigure,
                        clip_on=True,
                        zorder=_DEBUG_ZORDER,
                    )
                )

    # Active obstacles
    _draw_obstacles(obstacles)

    # Passive obstacles (gray, dashed)
    if passive:
        _draw_obstacles(passive, linestyle="dashed")

    # Moveable labels (blue)
    for label in moveables:
        ext = label.get_window_extent(renderer)
        _add_rect(_pad_bbox(ext, label_pad), "dodgerblue", _LABEL_ALPHA)

    # Axes bounds (green border)
    p0 = inv.transform((axes_bbox.x0, axes_bbox.y0))
    p1 = inv.transform((axes_bbox.x1, axes_bbox.y1))
    fig.patches.append(
        mpatches.FancyBboxPatch(
            (p0[0], p0[1]),
            p1[0] - p0[0],
            p1[1] - p0[1],
            boxstyle="square,pad=0",
            transform=fig.transFigure,
            facecolor="none",
            edgecolor="green",
            linewidth=_BOUNDS_LW,
            alpha=_BOUNDS_ALPHA,
            clip_on=False,
            zorder=_BOUNDS_ZORDER,
        )
    )
