from __future__ import annotations

import warnings

import pandas as pd
import pytest

from chartkit.charts._helpers import detect_bar_width, is_categorical_index
from chartkit.settings.schema import BarsConfig

# ---------------------------------------------------------------------------
# detect_bar_width
# ---------------------------------------------------------------------------


class TestDetectBarWidth:
    @pytest.mark.parametrize(
        "freq, periods, spacing_days",
        [
            ("B", 60, 1.0),
            ("W-MON", 52, 7.0),
            ("ME", 24, 31.0),
            ("QE", 16, 92.0),
            ("YE", 10, 365.0),
        ],
        ids=["business_daily", "weekly", "monthly", "quarterly", "annual"],
    )
    def test_width_is_a_fixed_share_of_the_spacing(
        self, freq: str, periods: int, spacing_days: float
    ) -> None:
        """Every frequency gets the same share of the room it has.

        The frequency tiers this replaced left weekly at 11% of its slot and
        quarterly at 22%, while daily and annual sat near 80%.
        """
        bars = BarsConfig()
        idx = pd.date_range("2020-01-31", periods=periods, freq=freq)

        width = detect_bar_width(idx, bars)

        assert width == pytest.approx(spacing_days * bars.width_fraction)

    def test_object_datetime_index_is_measured(self) -> None:
        idx = pd.Index(
            [
                pd.Timestamp("2025-01-31"),
                pd.Timestamp("2025-02-28"),
                pd.Timestamp("2025-03-31"),
            ],
            dtype="object",
        )
        bars = BarsConfig()

        # Gaps of 28 and 31 days; the median of the two is 29.5.
        assert detect_bar_width(idx, bars) == pytest.approx(29.5 * bars.width_fraction)

    def test_a_hole_in_the_series_does_not_widen_the_bars(self) -> None:
        """The median ignores the gap; the mean would have stretched every bar."""
        bars = BarsConfig()
        regular = pd.date_range("2024-01-31", periods=12, freq="ME")
        gapped = regular.delete([4, 5, 6])

        assert detect_bar_width(gapped, bars) == pytest.approx(
            detect_bar_width(regular, bars), rel=0.05
        )

    def test_non_datetime_keeps_the_unit_slot(self) -> None:
        idx = pd.Index(["a", "b", "c"], dtype="object")
        bars = BarsConfig()
        assert detect_bar_width(idx, bars) == bars.width_fraction

    def test_repeated_dates_fall_back(self) -> None:
        """A median spacing of zero would render bars with no width at all."""
        idx = pd.DatetimeIndex(["2024-01-01"] * 3 + ["2024-01-02"])
        bars = BarsConfig()
        assert detect_bar_width(idx, bars) == bars.width_fraction

    def test_single_point_keeps_the_unit_slot(self) -> None:
        bars = BarsConfig()
        assert detect_bar_width(pd.DatetimeIndex(["2024-01-31"]), bars) == (
            bars.width_fraction
        )

    def test_no_warning_for_string_index(self) -> None:
        idx = pd.Index(["B3", "NYSE", "LSE"])
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            width = detect_bar_width(idx, BarsConfig())
        assert width == BarsConfig().width_fraction


class TestWidthOverride:
    """``width=`` used to reach ax.bar() twice and raise TypeError."""

    @pytest.mark.parametrize("kind", ["bar", "stacked_bar"])
    def test_width_overrides_the_measurement(self, kind: str) -> None:
        idx = pd.date_range("2024-03-31", periods=8, freq="QE")
        df = pd.DataFrame({"pib": range(8)}, index=idx)

        result = df.chartkit.plot(kind=kind, title="t", width=45)

        assert result.axes.containers[0][0].get_width() == pytest.approx(45)

    def test_grouped_width_is_split_across_columns(self) -> None:
        idx = pd.date_range("2024-03-31", periods=8, freq="QE")
        df = pd.DataFrame({"a": range(8), "b": range(8)}, index=idx)

        result = df.chartkit.plot(kind="bar", title="t", width=60)

        assert result.axes.containers[0][0].get_width() == pytest.approx(30)

    def test_barh_height_overrides_the_default(self) -> None:
        df = pd.DataFrame({"v": [3.0, 1.0, 2.0]}, index=pd.Index(["B3", "NYSE", "LSE"]))

        result = df.chartkit.plot(kind="barh", title="t", height=0.4)

        assert result.axes.containers[0][0].get_height() == pytest.approx(0.4)


# ---------------------------------------------------------------------------
# is_categorical_index
# ---------------------------------------------------------------------------


class TestIsCategoricalIndex:
    @pytest.mark.parametrize(
        "idx, expected",
        [
            (pd.Index(["B3", "NYSE", "LSE"]), True),
            (pd.CategoricalIndex(["A", "B", "C"]), True),
            (pd.Index(["X", "Y", "Z"], dtype="string"), True),
            (pd.date_range("2023-01-01", periods=3, freq="ME"), False),
            (pd.Index([1, 2, 3]), False),
        ],
        ids=["string", "categorical", "string_dtype", "datetime", "numeric"],
    )
    def test_detection(self, idx: pd.Index, expected: bool) -> None:
        assert is_categorical_index(idx) is expected
