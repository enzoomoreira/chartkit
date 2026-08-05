"""Colour cycling across composed layers.

A composed chart renders one layer per call, so the palette has to be carried
between calls. When it was not, every layer restarted at the primary colour
and same-axis series came out indistinguishable.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from chartkit.composing.compose import compose
from chartkit.composing.layer import Layer
from chartkit.styling.theme import theme


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def frame() -> pd.DataFrame:
    idx = pd.date_range("2023-01-31", periods=6, freq="ME")
    return pd.DataFrame(
        {name: range(i + 1, i + 7) for i, name in enumerate("abcdefghij")},
        index=idx,
    )


_LAYER_FIELDS = {"x", "y", "kind", "units", "decimals", "highlight", "metrics", "axis"}


def _layer(frame: pd.DataFrame, *cols: str, **kwargs) -> Layer:
    """Build a Layer, routing renderer options into ``Layer.kwargs``."""
    fields = {k: v for k, v in kwargs.items() if k in _LAYER_FIELDS}
    render = {k: v for k, v in kwargs.items() if k not in _LAYER_FIELDS}
    return Layer(df=frame[list(cols)], kwargs=render, **fields)  # type: ignore[arg-type]


def _palette() -> list[str]:
    return [colour.lower() for colour in theme.colors.cycle()]


def _series_colors(result) -> list[str]:
    """Colours in draw order, across every Axes and artist type."""
    colors: list[str] = []
    for axes in result.describe()["axes"]:
        colors += [line["color"] for line in axes["lines"]]
        colors += [c["facecolors"][0] for c in axes["collections"] if c["facecolors"]]
    return colors


class TestSameAxis:
    def test_layers_get_distinct_colors(self, frame: pd.DataFrame) -> None:
        result = compose(_layer(frame, "a"), _layer(frame, "b"), _layer(frame, "c"))

        colors = _series_colors(result)
        assert len(set(colors)) == 3, f"expected three distinct colours, got {colors}"

    def test_matches_a_plain_multi_series_plot(self, frame: pd.DataFrame) -> None:
        # The same three series drawn one way or the other should look the same.
        plotted = frame[["a", "b", "c"]].chartkit.plot()
        composed = compose(_layer(frame, "a"), _layer(frame, "b"), _layer(frame, "c"))

        assert _series_colors(composed) == _series_colors(plotted)

    def test_a_multi_column_layer_consumes_one_slot_per_column(
        self, frame: pd.DataFrame
    ) -> None:
        result = compose(_layer(frame, "a", "b"), _layer(frame, "c"))

        assert _series_colors(result) == _palette()[:3]

    def test_the_palette_wraps_when_layers_outnumber_it(
        self, frame: pd.DataFrame
    ) -> None:
        palette = _palette()
        names = "abcdefghij"[: len(palette) + 2]

        result = compose(*[_layer(frame, name) for name in names])

        expected = [palette[i % len(palette)] for i in range(len(names))]
        assert _series_colors(result) == expected


class TestAcrossAxes:
    """One palette for the whole chart: the legend consolidates both axes, so
    two series sharing a colour would be ambiguous in a single legend."""

    def test_the_cycle_continues_onto_the_right_axis(self, frame: pd.DataFrame) -> None:
        result = compose(
            _layer(frame, "a"),
            _layer(frame, "b", axis="right"),
            _layer(frame, "c"),
        )

        described = result.describe()
        left = [line["color"] for line in described["axes"][0]["lines"]]
        right = [line["color"] for line in described["axes"][1]["lines"]]

        palette = _palette()
        assert left == [palette[0], palette[2]]
        assert right == [palette[1]]


class TestExplicitColor:
    def test_an_explicit_color_wins_over_the_cycle(self, frame: pd.DataFrame) -> None:
        result = compose(_layer(frame, "a", color="#ff0000"), _layer(frame, "b"))

        assert _series_colors(result)[0] == "#ff0000"

    def test_an_explicit_color_consumes_no_slot(self, frame: pd.DataFrame) -> None:
        # Charging it a slot would push the rest into wraparound sooner.
        result = compose(_layer(frame, "a", color="#ff0000"), _layer(frame, "b"))

        assert _series_colors(result)[1] == _palette()[0]


class TestEnhancers:
    """Enhancers resolve colour through the same context, not the generic path."""

    @pytest.mark.parametrize("kind", ["bar", "area", "step", "scatter", "stairs"])
    def test_the_cycle_advances_for_every_kind(
        self, frame: pd.DataFrame, kind: str
    ) -> None:
        result = compose(_layer(frame, "a", kind=kind), _layer(frame, "b", kind=kind))

        described = result.describe()["axes"][0]
        # Which attribute carries the visible colour depends on the artist:
        # bars fill, stairs draw an outline over a transparent face.
        colors = (
            [line["color"] for line in described["lines"]]
            + [c["facecolors"][0] for c in described["collections"] if c["facecolors"]]
            + [patch["facecolor"] for patch in described["patches"]]
            + [patch["edgecolor"] for patch in described["patches"]]
        )
        assert set(_palette()[:2]) <= set(colors), f"{kind} gave {colors}"

    def test_grouped_bars_then_a_line(self, frame: pd.DataFrame) -> None:
        result = compose(_layer(frame, "a", "b", kind="bar"), _layer(frame, "c"))

        described = result.describe()["axes"][0]
        palette = _palette()
        assert {patch["facecolor"] for patch in described["patches"]} == set(
            palette[:2]
        )
        assert [line["color"] for line in described["lines"]] == [palette[2]]
