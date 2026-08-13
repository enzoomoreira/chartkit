"""Performance guard for the collision engine.

A scatter of 100 points took 45 seconds to resolve, against 0.37 without
collision -- the engine solved the exact Bezier extrema of every marker, on
every candidate position, for every label, on every iteration. These tests
express the ceiling as a multiple of the same chart drawn with the engine
off, so they stay meaningful on a slower machine than the one that wrote them.
"""

from __future__ import annotations

import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


def _frame(n: int) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    idx = pd.date_range("2000-01-01", periods=n, freq="B")
    return pd.DataFrame({"a": np.cumsum(rng.normal(0, 1, n)) + 100}, index=idx)


def _fastest(frame: pd.DataFrame, *, collision: bool, repeats: int = 3) -> float:
    """Best of *repeats*, which is the least noisy summary of a timing."""
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        frame.chartkit.plot(
            kind="scatter", highlight=["last", "max", "min"], collision=collision
        )
        timings.append(time.perf_counter() - start)
        plt.close("all")
    return min(timings)


@pytest.mark.parametrize(("points", "budget"), [(100, 6.0), (1000, 8.0)])
def test_collision_overhead_stays_bounded(points: int, budget: float) -> None:
    """Overhead is measured against the same chart with the engine disabled.

    At 100 points the ratio used to be roughly 120x.
    """
    frame = _frame(points)

    baseline = _fastest(frame, collision=False)
    resolved = _fastest(frame, collision=True)

    assert resolved <= baseline * budget, (
        f"{points}-point scatter: {resolved:.3f}s with collision against "
        f"{baseline:.3f}s without ({resolved / baseline:.1f}x, budget {budget}x)"
    )


def test_a_dense_scatter_still_completes() -> None:
    """10k points did not finish in 70 seconds before the extents fix."""
    frame = _frame(10_000)

    start = time.perf_counter()
    frame.chartkit.plot(kind="scatter", highlight=["last", "max", "min"])
    elapsed = time.perf_counter() - start

    assert elapsed < 30.0, f"10k-point scatter took {elapsed:.1f}s"


def test_line_charts_are_not_penalised() -> None:
    """The line path was always fast; this catches a fix that trades it away."""
    frame = _frame(1000)

    baseline = _fastest(frame, collision=False)
    start = time.perf_counter()
    frame.chartkit.plot(kind="line", highlight=["last", "max", "min"])
    elapsed = time.perf_counter() - start

    assert elapsed <= baseline * 8.0, f"line chart took {elapsed:.3f}s"
