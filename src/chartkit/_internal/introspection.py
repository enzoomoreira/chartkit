"""Structural description of a rendered chart.

Charts are images, which makes them awkward to verify programmatically: the
usual way to check a result is to look at it. Every rendering decision is
still present in the matplotlib Artists that produced the image, though, so
this module serialises that state into plain data. A chart can then be
asserted on, diffed and read from a terminal without rasterising anything.

Two levels of detail are available. The default reports the chart in data
terms -- series, colours, styles, labels, limits -- which stays the same
whatever size the figure is drawn at, and is what the render snapshots
compare against. ``geometry=True`` adds measured extents and the pairs of
labels that overlap; those are pixel measurements and must never be baselined.

One caveat on the default level: labels the collision engine repositions end
up where they fit, and what fits is decided from text measured in pixels. Their
``position`` therefore tracks font rasterisation, which differs between
platforms and matplotlib releases, even though every other field does not.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from matplotlib.colors import to_hex
from matplotlib.transforms import Bbox

from .rendering import get_renderer

if TYPE_CHECKING:
    from matplotlib.artist import Artist
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

__all__ = ["describe_figure", "explain_figure"]

# Coordinates are rounded before comparison: date2num values carry far more
# precision than any rendering decision depends on.
_PRECISION = 4


def _round(value: Any) -> Any:
    if isinstance(value, float):
        # NaN never compares equal to itself, so empty geometry (a bar for a
        # NaN observation) would make every comparison fail.
        if not math.isfinite(value):
            return None
        # Adding zero collapses -0.0, which a bar sitting exactly on the
        # baseline produces and which only adds noise to a diff.
        return round(float(value), _PRECISION) + 0.0
    if isinstance(value, (list, tuple)):
        return [_round(item) for item in value]
    return value


def _coord(value: Any) -> Any:
    """Normalise a coordinate that may not be numeric.

    Highlight labels can carry a raw index label (a Timestamp) instead of a
    numeric position, so the serialiser records what is actually there rather
    than forcing a conversion that would hide it.
    """
    try:
        return _round(float(value))
    except (TypeError, ValueError):
        return f"{type(value).__name__}:{value}"


def _color(value: Any) -> str | None:
    """Normalise a single colour spec to hex.

    Artists report colour as a name, an RGB(A) tuple or a hex string depending
    on how it was set, so comparing raw values would flag differences that do
    not exist on screen.
    """
    try:
        return to_hex(value)
    except (TypeError, ValueError):
        return None


def _colors(value: Any) -> list[str]:
    """Normalise a colour array, dropping duplicates but keeping order.

    Collections store one colour per element; a scatter with a single colour
    still reports an Nx4 array, and listing it in full would bury the signal.
    """
    single = _color(value)
    if single is not None:
        return [single]

    seen: list[str] = []
    for item in value:
        hex_color = _color(item)
        if hex_color is not None and hex_color not in seen:
            seen.append(hex_color)
    return seen


def _describe_line(line: Any) -> dict[str, Any]:
    xdata, ydata = line.get_xdata(orig=False), line.get_ydata(orig=False)
    return {
        "label": line.get_label(),
        "points": len(xdata),
        "first": _round([float(xdata[0]), float(ydata[0])]) if len(xdata) else None,
        "last": _round([float(xdata[-1]), float(ydata[-1])]) if len(xdata) else None,
        "color": _color(line.get_color()),
        "linestyle": line.get_linestyle(),
        "linewidth": _round(float(line.get_linewidth())),
        "marker": line.get_marker(),
        "alpha": _round(line.get_alpha()),
        "zorder": _round(float(line.get_zorder())),
    }


def _describe_patch(patch: Any, ax: Axes) -> dict[str, Any]:
    # get_extents() reports display pixels, so the same bar measures
    # differently at another figsize or dpi. Data coordinates describe the
    # rectangle the reader sees, independently of how large it is drawn.
    extents = patch.get_extents().transformed(ax.transData.inverted())
    return {
        "type": type(patch).__name__,
        "label": patch.get_label(),
        "bbox": _round(list(extents.bounds)),
        "facecolor": _color(patch.get_facecolor()),
        "edgecolor": _color(patch.get_edgecolor()),
        "alpha": _round(patch.get_alpha()),
        "zorder": _round(float(patch.get_zorder())),
    }


def _describe_collection(collection: Any) -> dict[str, Any]:
    return {
        "type": type(collection).__name__,
        "label": collection.get_label(),
        "elements": len(collection.get_paths()),
        "facecolors": _colors(collection.get_facecolor()),
        "edgecolors": _colors(collection.get_edgecolor()),
        "alpha": _round(collection.get_alpha()),
        "zorder": _round(float(collection.get_zorder())),
    }


def _describe_text(text: Any) -> dict[str, Any]:
    return {
        "text": text.get_text(),
        "position": [_coord(coord) for coord in text.get_position()],
        "color": _color(text.get_color()),
        "ha": text.get_ha(),
        "va": text.get_va(),
    }


def _axis_side(ax: Axes) -> str:
    """Report which side the Y axis is drawn on.

    ``compose()`` builds its second axis with ``twinx()``, which moves the
    ticks to the right. That is the only thing distinguishing the two axes
    once rendering is done.
    """
    position = ax.yaxis.get_ticks_position()
    return "right" if position == "right" else "left"


def _describe_axes(ax: Axes) -> dict[str, Any]:
    legend = ax.get_legend()
    return {
        "side": _axis_side(ax),
        "title": ax.get_title(),
        "xlabel": ax.get_xlabel(),
        "ylabel": ax.get_ylabel(),
        "xlim": _round([float(v) for v in ax.get_xlim()]),
        "ylim": _round([float(v) for v in ax.get_ylim()]),
        "lines": [_describe_line(line) for line in ax.lines],
        "patches": [_describe_patch(patch, ax) for patch in ax.patches],
        "collections": [_describe_collection(coll) for coll in ax.collections],
        "texts": [_describe_text(text) for text in ax.texts],
        "legend": sorted(t.get_text() for t in legend.get_texts()) if legend else None,
        "xticklabels": [label.get_text() for label in ax.get_xticklabels()],
        "yticklabels": [label.get_text() for label in ax.get_yticklabels()],
        "xtick_rotation": _round(
            [float(label.get_rotation()) for label in ax.get_xticklabels()][:1]
        ),
        "y_formatter": type(ax.yaxis.get_major_formatter()).__name__,
    }


def _labelled_artists(fig: Figure) -> list[tuple[str, Artist]]:
    """Collect the artists whose placement the collision engine arbitrates.

    Legends are included because the engine registers them as obstacles: a
    label sitting under the legend box is just as unreadable as one sitting
    under another label.
    """
    artists: list[tuple[str, Artist]] = []
    for index, ax in enumerate(fig.axes):
        for text in ax.texts:
            if text.get_visible() and text.get_text().strip():
                artists.append((f"axes[{index}]:{text.get_text().strip()}", text))
        legend = ax.get_legend()
        if legend is not None and legend.get_visible():
            artists.append((f"axes[{index}]:<legend>", legend))
    return artists


def _find_overlaps(fig: Figure) -> list[dict[str, Any]]:
    """Report every pair of labels whose drawn extents intersect.

    This measures the outcome rather than the intent: the collision registry
    is cleared once the chart is built, so what remains is the geometry the
    reader actually sees.
    """
    fig.canvas.draw()
    renderer = get_renderer(fig)

    artists = _labelled_artists(fig)
    boxes: list[tuple[str, Bbox]] = []
    for name, artist in artists:
        boxes.append((name, artist.get_window_extent(renderer)))

    overlaps: list[dict[str, Any]] = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            name_a, box_a = boxes[i]
            name_b, box_b = boxes[j]
            intersection = Bbox.intersection(box_a, box_b)
            # Boxes that merely touch share an edge but no area.
            if intersection is None or intersection.width <= 0:
                continue
            if intersection.height <= 0:
                continue
            overlaps.append(
                {
                    "a": name_a,
                    "b": name_b,
                    "overlap": _round([intersection.width, intersection.height]),
                }
            )
    return overlaps


def describe_figure(fig: Figure, *, geometry: bool = False) -> dict[str, Any]:
    """Serialise everything about *fig* that a rendering change would alter.

    Args:
        geometry: Add measured bounding boxes and label overlaps. These depend
            on font rasterisation, so they are meant for live inspection and
            must not be compared against a stored baseline.
    """
    described: dict[str, Any] = {
        "axes": [_describe_axes(ax) for ax in fig.axes],
        "figure_texts": sorted(text.get_text() for text in fig.texts),
    }

    if geometry:
        described["overlaps"] = _find_overlaps(fig)

    return described


def _format_line(line: dict[str, Any]) -> str:
    span = ""
    if line["first"] is not None and line["last"] is not None:
        span = f"  {tuple(line['first'])} -> {tuple(line['last'])}"
    return (
        f"    - {line['label']!r}  {line['points']} pts  {line['color']}  "
        f"{line['linestyle']}  lw={line['linewidth']}  z={line['zorder']}{span}"
    )


def _format_axes(index: int, axes: dict[str, Any]) -> list[str]:
    out = [f"Axes[{index}] ({axes['side']})"]
    if axes["title"]:
        out.append(f"  title: {axes['title']!r}")
    out.append(f"  xlim: {axes['xlim']}   ylim: {axes['ylim']}")
    out.append(
        f"  xlabel: {axes['xlabel'] or '-'}   ylabel: {axes['ylabel'] or '-'}"
        f"   y_formatter: {axes['y_formatter']}"
    )

    for key, formatter in (
        ("lines", _format_line),
        ("patches", lambda p: f"    - {p['type']} {p['facecolor']} bbox={p['bbox']}"),
        (
            "collections",
            lambda c: f"    - {c['type']} {c['elements']} el {c['facecolors']}",
        ),
        (
            "texts",
            lambda t: f"    - {t['text']!r} @ {t['position']} {t['ha']}/{t['va']}",
        ),
    ):
        items = axes[key]
        if items:
            out.append(f"  {key} ({len(items)}):")
            out.extend(formatter(item) for item in items)

    if axes["legend"]:
        out.append(f"  legend: {', '.join(axes['legend'])}")

    ticks = ", ".join(axes["xticklabels"])
    rotation = axes["xtick_rotation"][0] if axes["xtick_rotation"] else 0
    out.append(f"  xticks (rot {rotation}): {ticks}")
    return out


def explain_figure(fig: Figure) -> str:
    """Render the structural description as text meant to be read in a terminal."""
    described = describe_figure(fig, geometry=True)

    out: list[str] = []
    for index, axes in enumerate(described["axes"]):
        out.extend(_format_axes(index, axes))
        out.append("")

    if described["figure_texts"]:
        out.append(f"Figure texts: {' | '.join(described['figure_texts'])}")

    overlaps = described["overlaps"]
    if overlaps:
        out.append(f"Overlaps ({len(overlaps)}):")
        out.extend(
            f"  - {item['a']} <-> {item['b']}  {item['overlap']}" for item in overlaps
        )
    else:
        out.append("Overlaps: none")

    return "\n".join(out)
