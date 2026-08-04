"""Process-level guarantees a published library must honour.

These assert that importing and using chartkit leaves no trace on the host
process: no retained figures, no mutated matplotlib defaults, no dependency
on the active backend. They are the acceptance criteria for the library
citizenship work.
"""

from __future__ import annotations

import gc
import os
import subprocess
import sys
import weakref
from pathlib import Path

import matplotlib
import pandas as pd
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"

_PDF_BACKEND_SCRIPT = """
import matplotlib
matplotlib.use("pdf")

import pandas as pd
import chartkit

df = pd.DataFrame(
    {"v": [1.0, 3.0, 2.0, 5.0]},
    index=pd.date_range("2024-01-31", periods=4, freq="ME"),
)
df.chartkit.plot(highlight=True, metrics=["ath"], tick_rotation="auto")
"""


def test_plot_does_not_retain_figures(monthly_rates: pd.DataFrame) -> None:
    """Every figure must be collectable once the caller drops its result."""
    refs: list[weakref.ref] = []

    for _ in range(5):
        result = monthly_rates.chartkit.plot(highlight=True)
        refs.append(weakref.ref(result.figure))
        del result

    gc.collect()

    alive = [ref for ref in refs if ref() is not None]
    assert not alive, f"{len(alive)} of {len(refs)} figures still reachable"


def test_plot_does_not_mutate_global_rcparams(monthly_rates: pd.DataFrame) -> None:
    """Plotting must not change matplotlib defaults for the whole process."""
    before = dict(matplotlib.rcParams)

    monthly_rates.chartkit.plot(title="Isolation")

    after = dict(matplotlib.rcParams)
    changed = sorted(key for key in before if before[key] != after[key])
    assert not changed, f"rcParams leaked: {changed}"


def test_plot_works_on_non_agg_backend() -> None:
    """Headless PDF/SVG rendering must not depend on the Agg renderer."""
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    proc = subprocess.run(
        [sys.executable, "-c", _PDF_BACKEND_SCRIPT],
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("kind", ["plot", "bar", "area", "scatter"])
def test_repeated_plots_do_not_accumulate_collision_state(
    monthly_rates: pd.DataFrame, kind: str
) -> None:
    """Collision bookkeeping must not outlive the Axes it describes."""
    from chartkit._internal.collision._registry import (
        _artist_obstacles,
        _labels,
        _passive,
    )

    for _ in range(3):
        result = monthly_rates.chartkit.plot(kind=kind)
        del result

    gc.collect()

    retained = len(_labels) + len(_passive) + len(_artist_obstacles)
    assert retained == 0, f"{retained} Axes entries retained after collection"
