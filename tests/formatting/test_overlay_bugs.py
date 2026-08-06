"""Regressions for the overlay, formatter and decoration defects (F3C pass).

Four of these turn a configuration mistake into a raw KeyError or IndexError
raised halfway through ``plot()``, where the traceback points at matplotlib
internals rather than at the TOML line that caused it.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError as PydanticValidationError

from chartkit import configure
from chartkit.exceptions import ValidationError


@pytest.fixture(autouse=True)
def _close_figs():
    yield
    plt.close("all")


@pytest.fixture
def frame() -> pd.DataFrame:
    idx = pd.date_range("2023-01-31", periods=24, freq="ME")
    return pd.DataFrame({"v": np.linspace(0.0, 1.0, 24)}, index=idx)


class TestFooterTemplate:
    def test_unknown_placeholder_names_the_key(self, frame: pd.DataFrame) -> None:
        """str.format raised a bare KeyError from inside plot()."""
        configure(branding={"footer_format": "Fonte: {source} | {unknown_key}"})

        with pytest.raises(ValidationError, match="unknown_key"):
            frame.chartkit.plot(source="BCB")

    def test_the_error_points_at_the_setting(self, frame: pd.DataFrame) -> None:
        configure(branding={"footer_format": "{nope}"})

        with pytest.raises(ValidationError, match="footer_format"):
            frame.chartkit.plot(source="BCB")

    def test_valid_placeholders_still_render(self, frame: pd.DataFrame) -> None:
        configure(branding={"footer_format": "Fonte: {source}"})
        result = frame.chartkit.plot(source="BCB")
        assert any("BCB" in t.get_text() for t in result.figure.texts)


class TestMagnitudeSuffixes:
    def test_empty_suffix_list_is_rejected(self, frame: pd.DataFrame) -> None:
        """An empty list reached the formatter and indexed out of range.

        The schema rejects it now, naming the setting, rather than surfacing as
        an IndexError once a number large enough to need a suffix comes along.
        The check fires on first use because ``configure()`` only records the
        override -- the config is built lazily.
        """
        configure(formatters={"magnitude": {"suffixes": []}})

        with pytest.raises(PydanticValidationError, match="at least 1 item"):
            frame.chartkit.plot(units="human")

    def test_a_populated_list_is_accepted(self, frame: pd.DataFrame) -> None:
        configure(formatters={"magnitude": {"suffixes": ["", "mil", "mi"]}})
        result = frame.chartkit.plot(units="human")
        assert result.axes.yaxis.get_major_formatter()(1_500_000) == "1,5mi"


class TestPointsFormatter:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(0.9, "1"), (1.6, "2"), (-0.9, "-1"), (2.4, "2")],
    )
    def test_fractions_round_rather_than_truncate(
        self, value: float, expected: str, frame: pd.DataFrame
    ) -> None:
        """int(x) floored towards zero, so 0.9 was labelled '0'."""
        result = frame.chartkit.plot(units="points")
        assert result.axes.yaxis.get_major_formatter()(value) == expected

    def test_large_integers_still_use_thousands_separators(self) -> None:
        idx = pd.date_range("2023-01-31", periods=6, freq="ME")
        df = pd.DataFrame({"v": np.linspace(1e6, 2e6, 6)}, index=idx)

        result = df.chartkit.plot(units="points")
        assert result.axes.yaxis.get_major_formatter()(1_234_567) == "1.234.567"

    def test_explicit_decimals_are_honoured(self, frame: pd.DataFrame) -> None:
        result = frame.chartkit.plot(units="points", decimals=2)
        assert result.axes.yaxis.get_major_formatter()(1234.5) == "1.234,50"


class TestVBandDates:
    def test_unparseable_date_raises_validation_error(
        self, frame: pd.DataFrame
    ) -> None:
        """pandas raised DateParseError, which is not a ChartKitError."""
        with pytest.raises(ValidationError, match="vband"):
            frame.chartkit.plot(metrics=["vband:nao-e-data:2023-06-30"])

    def test_the_error_names_the_offending_value(self, frame: pd.DataFrame) -> None:
        with pytest.raises(ValidationError, match="nao-e-data"):
            frame.chartkit.plot(metrics=["vband:nao-e-data:2023-06-30"])

    def test_valid_dates_still_draw(self, frame: pd.DataFrame) -> None:
        result = frame.chartkit.plot(metrics=["vband:2023-03-31:2023-06-30"])
        assert len(result.axes.patches) >= 1


class TestStdBandLabel:
    def test_window_placeholder_in_the_full_series_template(
        self, frame: pd.DataFrame
    ) -> None:
        """The full-series branch passed only deviations, so {window} exploded."""
        configure(labels={"std_band_full_format": "DP({window}, {deviations})"})

        result = frame.chartkit.plot(metrics=["std_band"])
        labels = [t.get_text() for t in result.axes.get_legend().get_texts()]
        assert any("DP(0" in label for label in labels), labels

    def test_default_template_still_renders(self, frame: pd.DataFrame) -> None:
        configure(labels={"std_band_full_format": "DP({deviations})"})
        result = frame.chartkit.plot(metrics=["std_band"])
        labels = [t.get_text() for t in result.axes.get_legend().get_texts()]
        assert any("DP(" in label for label in labels), labels
