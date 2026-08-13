"""Auto-rotation of X tick labels: when it fires and how far it goes.

The trigger used to be strict intersection, which twenty quarterly labels
sitting 0.96px apart never met -- they read as one long word and stayed
horizontal. These tests pin the crowding threshold and the escalation to 90
degrees at either end of it.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit import configure
from chartkit._internal.tick_rotation import _is_crowded

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def quarter_labels() -> pd.DataFrame:
    """20 quarters as "1T24" labels -- adjacent, not overlapping."""
    idx = pd.date_range("2020-03-31", periods=20, freq="QE")
    return pd.DataFrame(
        {"pib": range(20)},
        index=pd.Index([f"{d.quarter}T{d.year % 100:02d}" for d in idx]),
    )


def _rotations(result) -> set[float]:
    labels = [t for t in result.axes.get_xticklabels() if t.get_text()]
    return {t.get_rotation() for t in labels}


# ---------------------------------------------------------------------------
# Crowding trigger
# ---------------------------------------------------------------------------


class TestCrowdingTrigger:
    def test_touching_labels_rotate(self, quarter_labels: pd.DataFrame) -> None:
        result = quarter_labels.chartkit.plot(kind="bar", title="t", y_origin="auto")
        assert _rotations(result) == {45.0}

    def test_zero_gap_restores_strict_intersection(
        self, quarter_labels: pd.DataFrame
    ) -> None:
        """The old behaviour, and the reason the defect went unnoticed."""
        configure(ticks={"min_gap_px": 0.0})

        result = quarter_labels.chartkit.plot(kind="bar", title="t", y_origin="auto")

        assert _rotations(result) == {0.0}

    def test_sparse_labels_stay_horizontal(self) -> None:
        idx = pd.date_range("2024-01-31", periods=6, freq="ME")
        df = pd.DataFrame({"v": range(6)}, index=idx)

        assert _rotations(df.chartkit.plot(title="t")) == {0.0}

    def test_configured_gap_is_honoured(self) -> None:
        """Twelve monthly labels sit ~18px apart: clear of 4px, inside 24px."""
        idx = pd.date_range("2024-01-31", periods=12, freq="ME")
        df = pd.DataFrame({"v": range(12)}, index=idx)
        kwargs = {"title": "t", "tick_format": "%b/%y", "tick_freq": "month"}

        assert _rotations(df.chartkit.plot(**kwargs)) == {0.0}

        configure(ticks={"min_gap_px": 24.0})
        assert _rotations(df.chartkit.plot(**kwargs)) == {45.0}

    def test_fewer_than_two_labels_is_never_crowded(self) -> None:
        fig, ax = plt.subplots()
        ax.plot([1], [1])
        ax.set_xticks([1])
        ax.set_xticklabels(["only"])
        fig.canvas.draw()

        assert _is_crowded(fig, ax, 1000.0) is False


# ---------------------------------------------------------------------------
# Escalation to 90 degrees
# ---------------------------------------------------------------------------


class TestEscalation:
    def test_dense_labels_escalate(self) -> None:
        idx = pd.date_range("2020-01-31", periods=60, freq="ME")
        df = pd.DataFrame({"v": range(60)}, index=idx)

        result = df.chartkit.plot(title="t", tick_format="%b/%Y", tick_freq="month")

        assert _rotations(result) == {90.0}

    def test_rotated_labels_are_not_judged_by_their_envelope(
        self, quarter_labels: pd.DataFrame
    ) -> None:
        """45 degrees is enough here, and the escalation must not overrule it.

        The bounding box of a rotated label is its diagonal envelope: these
        labels measure 1.2px apart at 45 degrees while reading perfectly clear.
        Applying the crowding gap to that number sent every chart to 90.
        """
        result = quarter_labels.chartkit.plot(kind="bar", title="t", y_origin="auto")

        assert _rotations(result) == {45.0}
