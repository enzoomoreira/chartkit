"""Structural snapshots of the main rendering paths.

Captured before the rendering bug fixes so that each subsequent fix produces a
reviewable diff of exactly what changed on screen.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd
import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

Snapshotter = Callable[[Figure, Axes], None]


@pytest.mark.parametrize(
    "kind",
    ["line", "bar", "area", "scatter", "step", "stackplot", "barh"],
)
def test_kind_snapshot(
    monthly_rates: pd.DataFrame, assert_snapshot: Snapshotter, kind: str
) -> None:
    result = monthly_rates.chartkit.plot(kind=kind, title=f"{kind} chart")
    assert_snapshot(result.figure, result.axes)


def test_line_with_metrics_snapshot(
    daily_prices: pd.DataFrame, assert_snapshot: Snapshotter
) -> None:
    result = daily_prices.chartkit.plot(
        title="Price with metrics",
        metrics=["ath|Peak", "atl|Trough", "ma:21|21d average"],
        units="BRL",
    )
    assert_snapshot(result.figure, result.axes)


def test_highlight_modes_snapshot(
    daily_prices: pd.DataFrame, assert_snapshot: Snapshotter
) -> None:
    result = daily_prices.chartkit.plot(
        title="Highlighted extremes",
        highlight=["last", "max", "min"],
        units="points",
    )
    assert_snapshot(result.figure, result.axes)


def test_transform_chain_snapshot(
    monthly_rates: pd.DataFrame, assert_snapshot: Snapshotter
) -> None:
    result = monthly_rates.chartkit.variation(horizon="year").plot(
        kind="bar", title="YoY variation", units="%", highlight="last"
    )
    assert_snapshot(result.figure, result.axes)


def test_axis_controls_snapshot(
    monthly_rates: pd.DataFrame, assert_snapshot: Snapshotter
) -> None:
    result = monthly_rates.chartkit.plot(
        title="Axis controls",
        xlabel="Date",
        ylabel="Rate",
        grid=False,
        tick_freq="quarter",
        tick_format="%b/%y",
    )
    assert_snapshot(result.figure, result.axes)


def test_compose_dual_axis_snapshot(
    monthly_rates: pd.DataFrame, assert_snapshot: Snapshotter
) -> None:
    from chartkit import compose

    left = monthly_rates[["cdi"]].chartkit.layer(units="%")
    right = monthly_rates[["ipca"]].chartkit.layer(kind="bar", axis="right")
    result = compose(left, right, title="Dual axis", source="BCB")
    assert_snapshot(result.figure, result.axes)
