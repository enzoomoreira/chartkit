"""Structural render snapshots.

Pixel baselines were deliberately avoided: font rasterisation differs between
platforms and matplotlib releases, which would make the comparison fail for
reasons unrelated to chartkit. A structural description is deterministic and,
when it breaks, names the property that changed instead of reporting an RMS
delta over an image.

The description itself lives in ``chartkit._internal.introspection`` and is
public as ``PlotResult.describe()``. These snapshots therefore exercise the
same code a user runs to inspect a chart, rather than a private copy of it.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from matplotlib.figure import Figure

from chartkit._internal.introspection import describe_figure

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

Snapshotter = Callable[[Figure], None]


@pytest.fixture
def assert_snapshot(request: pytest.FixtureRequest) -> Snapshotter:
    """Compare a Figure against its stored structural description.

    Every Axes is covered, so a chart with a second Y axis is compared in
    full. Geometry is left out: it is measured in pixels and would break the
    comparison whenever a font or a figure size changed.

    Run with ``--snapshot-update`` to rewrite the stored snapshots after an
    intentional rendering change; review the resulting diff as evidence.
    """
    updating = request.config.getoption("--snapshot-update")
    name = request.node.name.replace("[", "-").replace("]", "").replace("/", "_")
    path = SNAPSHOT_DIR / f"{name}.json"

    def _assert(fig: Figure) -> None:
        actual = describe_figure(fig)
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
