"""Tests for the structural chart description.

These cover what the snapshots cannot: that the description reaches every
Axes, survives a change of figure size, and reports label overlap honestly.
"""

from __future__ import annotations

import numpy as np
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


class TestContainers:
    """matplotlib marks bar rectangles ``_nolegend_``; the group holds the name."""

    def test_bar_series_is_named(self, monthly_rates: pd.DataFrame) -> None:
        described = monthly_rates[["cdi"]].chartkit.plot(kind="bar").describe()
        axes = described["axes"][0]

        # A single series draws no legend, so nothing else carries the name.
        assert axes["legend"] is None
        assert [group["label"] for group in axes["containers"]] == ["cdi"]

    def test_grouped_bars_name_every_series(self, monthly_rates: pd.DataFrame) -> None:
        described = monthly_rates.chartkit.plot(kind="bar").describe()

        labels = [group["label"] for group in described["axes"][0]["containers"]]
        assert labels == ["cdi", "ipca"]

    def test_line_charts_have_no_containers(self, monthly_rates: pd.DataFrame) -> None:
        described = monthly_rates.chartkit.plot().describe()

        assert described["axes"][0]["containers"] == []


class TestScaleOffset:
    """Ticks reading 8.395 on an axis running in billions are not 8.395."""

    @pytest.fixture
    def billions(self, monthly_index: pd.DatetimeIndex) -> pd.DataFrame:
        n = len(monthly_index)
        return pd.DataFrame(
            {"mktcap": 8.4e9 + np.linspace(0, 8e6, n)}, index=monthly_index
        )

    def test_default_formatter_offset_is_reported(self, billions: pd.DataFrame) -> None:
        described = billions.chartkit.plot().describe()["axes"][0]

        assert described["y_offset"] == "1e9"
        # The ticks alone would read as single digits.
        assert all(len(label) < 8 for label in described["yticklabels"])

    def test_numeric_index_offset_is_reported(self) -> None:
        df = pd.DataFrame(
            {"y": np.linspace(1.0, 2.0, 20)},
            index=np.linspace(5.0e8, 5.0e8 + 1000, 20),
        )

        described = df.chartkit.plot(kind="scatter").describe()["axes"][0]

        assert described["x_offset"] == "+5e8"

    def test_currency_formatter_has_no_offset(self, billions: pd.DataFrame) -> None:
        # A currency formatter writes the magnitude into every tick instead.
        described = billions.chartkit.plot(units="BRL").describe()["axes"][0]

        assert described["y_offset"] == ""

    def test_date_axis_has_no_offset(self, monthly_rates: pd.DataFrame) -> None:
        described = monthly_rates.chartkit.plot().describe()["axes"][0]

        assert described["x_offset"] == ""
        assert described["y_offset"] == ""

    def test_right_axis_offset_is_reported(
        self, monthly_rates: pd.DataFrame, billions: pd.DataFrame
    ) -> None:
        result = compose(
            monthly_rates[["cdi"]].chartkit.layer(units="%"),
            billions.chartkit.layer(kind="bar", axis="right"),
        )

        described = result.describe()

        assert described["axes"][0]["y_offset"] == ""
        assert described["axes"][1]["y_offset"] == "1e9"

    def test_explain_surfaces_the_offset(self, billions: pd.DataFrame) -> None:
        text = billions.chartkit.plot().explain()

        assert "scale offset" in text
        assert "1e9" in text


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

    def test_names_every_layer_of_a_larger_composition(
        self, multi_series_monthly: pd.DataFrame
    ) -> None:
        # Two layers share the left axis and the third is drawn as bars on the
        # right, so no single Axes or artist type holds the whole chart.
        result = compose(
            multi_series_monthly[["fund_a"]].chartkit.layer(units="%"),
            multi_series_monthly[["fund_b"]].chartkit.layer(),
            multi_series_monthly[["fund_c"]].chartkit.layer(kind="bar", axis="right"),
        )

        text = result.explain()

        for series in ("fund_a", "fund_b", "fund_c"):
            assert series in text, f"{series} missing from:\n{text}"

    def test_names_a_bar_series_with_no_legend_to_carry_it(
        self, monthly_rates: pd.DataFrame
    ) -> None:
        result = monthly_rates[["cdi"]].chartkit.plot(kind="bar")

        assert result.describe()["axes"][0]["legend"] is None
        assert "cdi" in result.explain()

    def test_patches_are_summarised_rather_than_listed(
        self, daily_prices: pd.DataFrame
    ) -> None:
        # Hundreds of bars must not become hundreds of lines.
        result = daily_prices.chartkit.plot(kind="bar")

        text = result.explain()

        assert len(result.describe()["axes"][0]["patches"]) > 100
        assert text.count("Rectangle") == 1
