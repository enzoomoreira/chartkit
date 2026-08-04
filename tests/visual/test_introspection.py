"""Tests for the structural chart description.

These cover what the snapshots cannot: that the description reaches every
Axes, survives a change of figure size, and reports label overlap honestly.
"""

from __future__ import annotations

import pandas as pd
import pytest

import chartkit
from chartkit import compose


@pytest.fixture
def dual_axis_result(monthly_rates: pd.DataFrame):
    left = monthly_rates[["cdi"]].chartkit.layer(units="%")
    right = monthly_rates[["ipca"]].chartkit.layer(kind="bar", axis="right")
    return compose(left, right, title="Dual axis", source="BCB")


class TestFigureCoverage:
    """A composed chart draws on two Axes; describing one hides half of it."""

    def test_reports_both_axes(self, dual_axis_result) -> None:
        described = dual_axis_result.describe()

        assert [ax["side"] for ax in described["axes"]] == ["left", "right"]

    def test_right_axis_bars_are_described(self, dual_axis_result) -> None:
        described = dual_axis_result.describe()
        right = described["axes"][1]

        # One bar per observation in the monthly_rates fixture.
        assert len(right["patches"]) == 24
        assert all(patch["type"] == "Rectangle" for patch in right["patches"])

    def test_left_axis_line_is_described(self, dual_axis_result) -> None:
        left = dual_axis_result.describe()["axes"][0]

        assert [line["label"] for line in left["lines"]] == ["cdi"]
        assert left["lines"][0]["points"] == 24


class TestColors:
    """Theme colours are the product; a description blind to them is useless."""

    def test_series_colour_follows_theme(self, monthly_rates: pd.DataFrame) -> None:
        chartkit.configure(colors={"primary": "#FF0000"})

        result = monthly_rates[["cdi"]].chartkit.plot()

        assert result.describe()["axes"][0]["lines"][0]["color"] == "#ff0000"

    def test_series_follow_the_colour_cycle(
        self, multi_series_monthly: pd.DataFrame
    ) -> None:
        chartkit.configure(colors={"primary": "#FF0000", "secondary": "#00FF00"})

        result = multi_series_monthly[["fund_a", "fund_b"]].chartkit.plot()

        colors = [line["color"] for line in result.describe()["axes"][0]["lines"]]
        assert colors == ["#ff0000", "#00ff00"]

    def test_bar_facecolour_is_reported(self, monthly_rates: pd.DataFrame) -> None:
        chartkit.configure(colors={"primary": "#123456"})

        result = monthly_rates[["cdi"]].chartkit.plot(kind="bar")

        patches = result.describe()["axes"][0]["patches"]
        assert {patch["facecolor"] for patch in patches} == {"#123456"}


class TestGeometry:
    """Pixel measurements are opt-in: they are the part that is not portable."""

    def test_absent_by_default(self, monthly_rates: pd.DataFrame) -> None:
        result = monthly_rates.chartkit.plot()

        assert "overlaps" not in result.describe()

    def test_present_when_requested(self, monthly_rates: pd.DataFrame) -> None:
        result = monthly_rates.chartkit.plot()

        assert "overlaps" in result.describe(geometry=True)

    def test_stacked_labels_are_reported(self, monthly_rates: pd.DataFrame) -> None:
        result = monthly_rates.chartkit.plot()
        # Two labels written at the same data point cannot both be readable.
        result.ax.text(0.5, 0.5, "alpha", transform=result.ax.transAxes)
        result.ax.text(0.5, 0.5, "beta", transform=result.ax.transAxes)

        overlaps = result.describe(geometry=True)["overlaps"]

        assert any("alpha" in pair["a"] and "beta" in pair["b"] for pair in overlaps), (
            f"expected alpha/beta to collide, got {overlaps}"
        )

    def test_separated_labels_are_not_reported(
        self, monthly_rates: pd.DataFrame
    ) -> None:
        result = monthly_rates.chartkit.plot()
        result.ax.text(0.02, 0.95, "alpha", transform=result.ax.transAxes)
        result.ax.text(0.98, 0.05, "beta", transform=result.ax.transAxes)

        overlaps = result.describe(geometry=True)["overlaps"]

        assert not any(
            "alpha" in pair["a"] and "beta" in pair["b"] for pair in overlaps
        )


class TestPortability:
    """Data-space fields must not move when the figure is drawn larger."""

    def test_bars_survive_a_figure_resize(self, monthly_rates: pd.DataFrame) -> None:
        chartkit.configure(layout={"figsize": (10.0, 5.0), "dpi": 100})
        small = monthly_rates[["cdi"]].chartkit.plot(kind="bar").describe()

        chartkit.configure(layout={"figsize": (14.0, 7.0), "dpi": 150})
        large = monthly_rates[["cdi"]].chartkit.plot(kind="bar").describe()

        assert small["axes"][0]["patches"] == large["axes"][0]["patches"]


class TestExplain:
    def test_mentions_title_and_series(self, monthly_rates: pd.DataFrame) -> None:
        result = monthly_rates[["cdi"]].chartkit.plot(title="Rates")

        text = result.explain()

        assert "Rates" in text
        assert "cdi" in text

    def test_reports_both_axes(self, dual_axis_result) -> None:
        text = dual_axis_result.explain()

        assert "Axes[0] (left)" in text
        assert "Axes[1] (right)" in text
