"""Structural render snapshots.

Pixel baselines were deliberately avoided: font rasterisation differs between
platforms and matplotlib releases, which would make the comparison fail for
reasons unrelated to chartkit. A structural description is deterministic and,
when it breaks, names the property that changed instead of reporting an RMS
delta over an image.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

# Coordinates are rounded before comparison: date2num values carry far more
# precision than any rendering decision depends on.
_PRECISION = 4


def _round(value: Any) -> Any:
    if isinstance(value, float):
        # NaN never compares equal to itself, so empty geometry (a bar for a
        # NaN observation) would make every comparison fail.
        return None if not math.isfinite(value) else round(float(value), _PRECISION)
    if isinstance(value, (list, tuple)):
        return [_round(item) for item in value]
    return value


def _describe_line(line: Any) -> dict[str, Any]:
    xdata, ydata = line.get_xdata(orig=False), line.get_ydata(orig=False)
    return {
        "label": line.get_label(),
        "points": len(xdata),
        "first": _round([float(xdata[0]), float(ydata[0])]) if len(xdata) else None,
        "last": _round([float(xdata[-1]), float(ydata[-1])]) if len(xdata) else None,
        "linestyle": line.get_linestyle(),
        "marker": line.get_marker(),
        "zorder": _round(float(line.get_zorder())),
    }


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


def _describe_text(text: Any) -> dict[str, Any]:
    return {
        "text": text.get_text(),
        "position": [_coord(coord) for coord in text.get_position()],
        "ha": text.get_ha(),
        "va": text.get_va(),
    }


def describe_axes(fig: Figure, ax: Axes) -> dict[str, Any]:
    """Serialise everything about an Axes that a rendering change would alter."""
    legend = ax.get_legend()
    return {
        "title": ax.get_title(),
        "xlabel": ax.get_xlabel(),
        "ylabel": ax.get_ylabel(),
        "xlim": _round([float(v) for v in ax.get_xlim()]),
        "ylim": _round([float(v) for v in ax.get_ylim()]),
        "lines": [_describe_line(line) for line in ax.lines],
        "patches": [
            {
                "type": type(patch).__name__,
                "bbox": _round(list(patch.get_extents().bounds)),
            }
            for patch in ax.patches
        ],
        "collections": [type(coll).__name__ for coll in ax.collections],
        "texts": [_describe_text(text) for text in ax.texts],
        "legend": sorted(t.get_text() for t in legend.get_texts()) if legend else None,
        "xticklabels": [label.get_text() for label in ax.get_xticklabels()],
        "yticklabels": [label.get_text() for label in ax.get_yticklabels()],
        "xtick_rotation": _round(
            [float(label.get_rotation()) for label in ax.get_xticklabels()][:1]
        ),
        "y_formatter": type(ax.yaxis.get_major_formatter()).__name__,
        "figure_texts": sorted(text.get_text() for text in fig.texts),
    }


@pytest.fixture
def assert_snapshot(request: pytest.FixtureRequest) -> Callable[[Figure, Axes], None]:
    """Compare an Axes against its stored structural description.

    Run with ``--snapshot-update`` to rewrite the stored snapshots after an
    intentional rendering change; review the resulting diff as evidence.
    """
    updating = request.config.getoption("--snapshot-update")
    name = request.node.name.replace("[", "-").replace("]", "").replace("/", "_")
    path = SNAPSHOT_DIR / f"{name}.json"

    def _assert(fig: Figure, ax: Axes) -> None:
        actual = describe_axes(fig, ax)
        serialised = json.dumps(actual, indent=2, sort_keys=True, ensure_ascii=False)

        if updating or not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(serialised + "\n", encoding="utf-8")
            if not updating:
                pytest.skip(f"snapshot created: {path.name}")
            return

        expected = json.loads(path.read_text(encoding="utf-8"))
        assert actual == expected, (
            f"render snapshot changed for {name}.\n"
            "Re-run with --snapshot-update if the change is intentional."
        )

    return _assert
