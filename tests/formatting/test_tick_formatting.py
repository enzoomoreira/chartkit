"""Tick formatting tests: auto-detection, frequency alignment, and tick clipping.

Tests the _infer_locator auto-detection that aligns X-axis ticks with actual
data points, and the _clip_ticks_to_data that removes phantom ticks outside
the data range.
"""

from __future__ import annotations

import matplotlib
import matplotlib.dates as mdates

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.ticker import FixedLocator

from chartkit._internal.tick_formatting import (
    _clip_ticks_to_data,
    _infer_locator,
    _is_sparse,
    _period_key,
    _strip_multiplier,
    _ticks_from_data,
    _to_datetime_index,
    apply_tick_formatting,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def quarterly_end_index() -> pd.DatetimeIndex:
    """Quarterly end-of-period: Mar, Jun, Sep, Dec (Brazilian GDP style)."""
    return pd.date_range("2014-03-31", periods=20, freq="QE-DEC")


@pytest.fixture
def quarterly_jan_index() -> pd.DatetimeIndex:
    """Quarterly end-of-period anchored in January: Jan, Apr, Jul, Oct."""
    return pd.date_range("2020-01-31", periods=12, freq="QE-JAN")


@pytest.fixture
def annual_index() -> pd.DatetimeIndex:
    """Annual data (year-end)."""
    return pd.date_range("2015-12-31", periods=10, freq="YE")


@pytest.fixture
def semiannual_index() -> pd.DatetimeIndex:
    """Semi-annual data (Jun and Dec)."""
    return pd.date_range("2018-06-30", periods=10, freq="6ME")


@pytest.fixture
def monthly_index() -> pd.DatetimeIndex:
    """Monthly data (24 months)."""
    return pd.date_range("2022-01-31", periods=24, freq="ME")


@pytest.fixture
def daily_index() -> pd.DatetimeIndex:
    """Daily business data (~1 year)."""
    return pd.bdate_range("2023-01-02", periods=252, freq="B")


@pytest.fixture
def weekly_index() -> pd.DatetimeIndex:
    """Weekly data (52 weeks)."""
    return pd.date_range("2023-01-02", periods=52, freq="W-MON")


@pytest.fixture
def ax() -> plt.Axes:
    """Fresh axes for each test."""
    _, ax = plt.subplots()
    yield ax
    plt.close("all")


def _tick_months(locator: FixedLocator) -> list[int]:
    """Extract unique months from a FixedLocator's tick positions."""
    dates = [mdates.num2date(t) for t in locator.locs]
    return sorted(set(d.month for d in dates))


# ---------------------------------------------------------------------------
# _strip_multiplier
# ---------------------------------------------------------------------------


class TestStripMultiplier:
    def test_no_prefix(self) -> None:
        assert _strip_multiplier("QE-DEC") == "QE-DEC"

    def test_single_digit(self) -> None:
        assert _strip_multiplier("2QE-DEC") == "QE-DEC"

    def test_multi_digit(self) -> None:
        assert _strip_multiplier("12ME") == "ME"

    def test_no_alpha(self) -> None:
        assert _strip_multiplier("123") == ""

    def test_pure_alpha(self) -> None:
        assert _strip_multiplier("YE") == "YE"


# ---------------------------------------------------------------------------
# _is_sparse
# ---------------------------------------------------------------------------


class TestIsSparse:
    @pytest.mark.parametrize(
        "base",
        ["YE", "YE-DEC", "YS", "YS-JAN", "BYE", "BYE-DEC", "BYS"],
    )
    def test_annual_is_sparse(self, base: str) -> None:
        assert _is_sparse(base) is True

    @pytest.mark.parametrize(
        "base",
        ["QE", "QE-DEC", "QE-JAN", "QS", "QS-DEC", "BQE", "BQS"],
    )
    def test_quarterly_is_sparse(self, base: str) -> None:
        assert _is_sparse(base) is True

    @pytest.mark.parametrize("base", ["ME", "MS", "BME", "W", "D", "B"])
    def test_dense_is_not_sparse(self, base: str) -> None:
        assert _is_sparse(base) is False


# ---------------------------------------------------------------------------
# _to_datetime_index
# ---------------------------------------------------------------------------


class TestToDatetimeIndex:
    def test_datetime_index_passthrough(
        self, quarterly_end_index: pd.DatetimeIndex
    ) -> None:
        result = _to_datetime_index(quarterly_end_index)
        assert isinstance(result, pd.DatetimeIndex)
        assert len(result) == len(quarterly_end_index)

    def test_datetime_series(self, quarterly_end_index: pd.DatetimeIndex) -> None:
        series = pd.Series(quarterly_end_index)
        result = _to_datetime_index(series)
        assert isinstance(result, pd.DatetimeIndex)

    def test_non_datetime_returns_none(self) -> None:
        assert _to_datetime_index(pd.RangeIndex(10)) is None

    def test_none_returns_none(self) -> None:
        assert _to_datetime_index(None) is None

    def test_string_index_returns_none(self) -> None:
        assert _to_datetime_index(pd.Index(["a", "b", "c"])) is None


# ---------------------------------------------------------------------------
# _period_key
# ---------------------------------------------------------------------------


class TestPeriodKey:
    def test_year_groups_by_year(self) -> None:
        dt = pd.Timestamp("2024-06-30")
        assert _period_key(dt, "year") == (2024,)

    def test_semester_h1(self) -> None:
        dt = pd.Timestamp("2024-03-31")
        assert _period_key(dt, "semester") == (2024, 1)

    def test_semester_h2(self) -> None:
        dt = pd.Timestamp("2024-09-30")
        assert _period_key(dt, "semester") == (2024, 2)

    def test_semester_boundary_june(self) -> None:
        dt = pd.Timestamp("2024-06-30")
        assert _period_key(dt, "semester") == (2024, 1)

    def test_semester_boundary_july(self) -> None:
        dt = pd.Timestamp("2024-07-31")
        assert _period_key(dt, "semester") == (2024, 2)

    def test_quarter_q1(self) -> None:
        dt = pd.Timestamp("2024-03-31")
        assert _period_key(dt, "quarter") == (2024, 0)

    def test_quarter_q2(self) -> None:
        dt = pd.Timestamp("2024-06-30")
        assert _period_key(dt, "quarter") == (2024, 1)

    def test_quarter_q3(self) -> None:
        dt = pd.Timestamp("2024-09-30")
        assert _period_key(dt, "quarter") == (2024, 2)

    def test_quarter_q4(self) -> None:
        dt = pd.Timestamp("2024-12-31")
        assert _period_key(dt, "quarter") == (2024, 3)

    def test_month(self) -> None:
        dt = pd.Timestamp("2024-07-15")
        assert _period_key(dt, "month") == (2024, 7)


# ---------------------------------------------------------------------------
# _ticks_from_data
# ---------------------------------------------------------------------------


class TestTicksFromData:
    def test_year_from_quarterly_data(self) -> None:
        """tick_freq='year' with quarterly data: picks December dates."""
        idx = pd.date_range("2020-03-31", periods=20, freq="QE-DEC")
        locator = _ticks_from_data(idx, "year")
        assert isinstance(locator, FixedLocator)

        tick_dates = [mdates.num2date(t) for t in locator.locs]
        for d in tick_dates:
            assert d.month == 12

    def test_year_from_monthly_data(self) -> None:
        """tick_freq='year' with monthly data: picks last date per year."""
        idx = pd.date_range("2020-01-31", periods=36, freq="ME")
        locator = _ticks_from_data(idx, "year")
        assert isinstance(locator, FixedLocator)

        tick_dates = [mdates.num2date(t) for t in locator.locs]
        for d in tick_dates:
            assert d.month == 12

    def test_semester_from_quarterly_data(self) -> None:
        """tick_freq='semester' with quarterly data: one per half-year."""
        idx = pd.date_range("2020-03-31", periods=12, freq="QE-DEC")
        locator = _ticks_from_data(idx, "semester")
        assert isinstance(locator, FixedLocator)

        tick_dates = [mdates.num2date(t) for t in locator.locs]
        tick_months = {d.month for d in tick_dates}
        assert tick_months == {6, 12}

    def test_quarter_from_monthly_data(self) -> None:
        """tick_freq='quarter' with monthly data: last date per quarter."""
        idx = pd.date_range("2022-01-31", periods=24, freq="ME")
        locator = _ticks_from_data(idx, "quarter")
        assert isinstance(locator, FixedLocator)

        tick_dates = [mdates.num2date(t) for t in locator.locs]
        tick_months = {d.month for d in tick_dates}
        assert tick_months == {3, 6, 9, 12}

    def test_month_from_daily_data(self) -> None:
        """tick_freq='month' with daily data: last business day per month."""
        idx = pd.bdate_range("2023-01-02", periods=252, freq="B")
        locator = _ticks_from_data(idx, "month")
        assert isinstance(locator, FixedLocator)
        assert len(locator.locs) >= 12

    def test_fiscal_calendar_preserved(self) -> None:
        """Fiscal quarters (Jan/Apr/Jul/Oct anchoring) are preserved."""
        idx = pd.date_range("2020-01-31", periods=12, freq="QE-JAN")
        locator = _ticks_from_data(idx, "year")
        assert isinstance(locator, FixedLocator)

        tick_dates = [mdates.num2date(t) for t in locator.locs]
        # Last date per year should be in October (QE-JAN: Jan, Apr, Jul, Oct)
        for d in tick_dates:
            assert d.month in {1, 10}

    def test_incomplete_period_shows_last_available(self) -> None:
        """Incomplete final period still shows its last available date."""
        # 2020 full year + 2021 only until September
        dates = list(pd.date_range("2020-03-31", "2020-12-31", freq="QE-DEC"))
        dates += list(pd.date_range("2021-03-31", "2021-09-30", freq="QE-DEC"))
        idx = pd.DatetimeIndex(dates)

        locator = _ticks_from_data(idx, "year")
        assert isinstance(locator, FixedLocator)

        tick_dates = [mdates.num2date(t) for t in locator.locs]
        # 2020 -> Dec 31, 2021 -> Sep 30 (incomplete year)
        assert tick_dates[0].month == 12
        assert tick_dates[0].year == 2020
        assert tick_dates[1].month == 9
        assert tick_dates[1].year == 2021

    def test_single_point_returns_none(self) -> None:
        idx = pd.DatetimeIndex(["2024-03-31"])
        assert _ticks_from_data(idx, "year") is None

    def test_empty_returns_none(self) -> None:
        idx = pd.DatetimeIndex([])
        assert _ticks_from_data(idx, "year") is None

    def test_all_same_period_returns_none(self) -> None:
        """All dates in same year -> only 1 group -> returns None."""
        idx = pd.date_range("2024-01-31", periods=6, freq="ME")
        assert _ticks_from_data(idx, "year") is None


# ---------------------------------------------------------------------------
# _infer_locator - frequency auto-detection
# ---------------------------------------------------------------------------


class TestInferLocator:
    """Verify that _infer_locator returns FixedLocator with ticks at
    the exact data dates for sparse frequencies."""

    def test_quarterly_end_dec_uses_actual_dates(
        self, quarterly_end_index: pd.DatetimeIndex
    ) -> None:
        """Ticks should fall on actual data dates (31-Mar, 30-Jun, etc.),
        NOT on 1st-of-month as MonthLocator would produce."""
        locator = _infer_locator(quarterly_end_index)
        assert isinstance(locator, FixedLocator)
        assert len(locator.locs) == len(quarterly_end_index)

        expected = [mdates.date2num(d) for d in quarterly_end_index]
        assert list(locator.locs) == expected

    def test_quarterly_end_dec_months(
        self, quarterly_end_index: pd.DatetimeIndex
    ) -> None:
        locator = _infer_locator(quarterly_end_index)
        assert _tick_months(locator) == [3, 6, 9, 12]

    def test_quarterly_end_jan_months(
        self, quarterly_jan_index: pd.DatetimeIndex
    ) -> None:
        locator = _infer_locator(quarterly_jan_index)
        assert isinstance(locator, FixedLocator)
        assert _tick_months(locator) == [1, 4, 7, 10]

    def test_annual(self, annual_index: pd.DatetimeIndex) -> None:
        locator = _infer_locator(annual_index)
        assert isinstance(locator, FixedLocator)

        expected = [mdates.date2num(d) for d in annual_index]
        assert list(locator.locs) == expected

    def test_semiannual(self, semiannual_index: pd.DatetimeIndex) -> None:
        """Semi-annual (6ME, detected as 2QE-DEC by pandas)."""
        locator = _infer_locator(semiannual_index)
        assert isinstance(locator, FixedLocator)
        assert _tick_months(locator) == [6, 12]

    def test_monthly_returns_none(self, monthly_index: pd.DatetimeIndex) -> None:
        """Monthly data should NOT trigger auto-detection."""
        assert _infer_locator(monthly_index) is None

    def test_daily_returns_none(self, daily_index: pd.DatetimeIndex) -> None:
        assert _infer_locator(daily_index) is None

    def test_weekly_returns_none(self, weekly_index: pd.DatetimeIndex) -> None:
        assert _infer_locator(weekly_index) is None

    def test_too_few_points_returns_none(self) -> None:
        idx = pd.date_range("2024-03-31", periods=2, freq="QE")
        assert _infer_locator(idx) is None

    def test_irregular_dates_returns_none(self) -> None:
        idx = pd.DatetimeIndex(["2023-01-05", "2023-03-18", "2023-07-22", "2024-01-10"])
        assert _infer_locator(idx) is None

    def test_non_datetime_returns_none(self) -> None:
        assert _infer_locator(pd.RangeIndex(10)) is None

    def test_quarterly_fiscal_feb(self) -> None:
        """Fiscal quarters ending in Feb/May/Aug/Nov."""
        idx = pd.date_range("2020-02-29", periods=8, freq="QE-FEB")
        locator = _infer_locator(idx)
        assert isinstance(locator, FixedLocator)
        assert _tick_months(locator) == [2, 5, 8, 11]

    def test_biannual(self) -> None:
        """Bi-annual data (2YE) is still sparse."""
        idx = pd.date_range("2010-12-31", periods=6, freq="2YE")
        locator = _infer_locator(idx)
        assert isinstance(locator, FixedLocator)
        assert len(locator.locs) == 6

    def test_tick_dates_match_index_exactly(
        self, quarterly_end_index: pd.DatetimeIndex
    ) -> None:
        """Core guarantee: every tick date == corresponding index date."""
        locator = _infer_locator(quarterly_end_index)
        tick_dates = [mdates.num2date(t).date() for t in locator.locs]
        index_dates = [d.date() for d in quarterly_end_index]
        assert tick_dates == index_dates


# ---------------------------------------------------------------------------
# _clip_ticks_to_data
# ---------------------------------------------------------------------------


class TestClipTicksToData:
    def test_removes_phantom_ticks(
        self, ax: plt.Axes, quarterly_end_index: pd.DatetimeIndex
    ) -> None:
        """Ticks outside data range should be removed."""
        rng = np.random.default_rng(42)
        ax.bar(quarterly_end_index, rng.normal(0, 1, len(quarterly_end_index)))

        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[3, 6, 9, 12]))

        _clip_ticks_to_data(ax, quarterly_end_index)

        locator = ax.xaxis.get_major_locator()
        assert isinstance(locator, FixedLocator)

        tick_dates = [mdates.num2date(t) for t in locator.locs]
        first_data = quarterly_end_index.min()
        last_data = quarterly_end_index.max()

        for d in tick_dates:
            assert d.month >= first_data.month or d.year > first_data.year
            assert d.year <= last_data.year

    def test_keeps_first_month_tick(
        self, ax: plt.Axes, quarterly_end_index: pd.DatetimeIndex
    ) -> None:
        """A tick on day-1 of the first data month should NOT be filtered.

        MonthLocator produces 2014-03-01 while data starts 2014-03-31.
        The clipping should keep it because they share the same month.
        """
        rng = np.random.default_rng(42)
        ax.bar(quarterly_end_index, rng.normal(0, 1, len(quarterly_end_index)))

        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[3, 6, 9, 12]))

        _clip_ticks_to_data(ax, quarterly_end_index)

        locator = ax.xaxis.get_major_locator()
        tick_dates = [mdates.num2date(t) for t in locator.locs]

        first_tick_month = (tick_dates[0].year, tick_dates[0].month)
        first_data_month = (quarterly_end_index[0].year, quarterly_end_index[0].month)
        assert first_tick_month == first_data_month

    def test_non_datetime_is_noop(self, ax: plt.Axes) -> None:
        int_index = pd.RangeIndex(10)
        ax.plot(range(10), range(10))
        _clip_ticks_to_data(ax, int_index)

    def test_short_data_is_noop(self, ax: plt.Axes) -> None:
        idx = pd.date_range("2024-01-01", periods=1)
        ax.plot(idx, [1.0])
        _clip_ticks_to_data(ax, idx)


# ---------------------------------------------------------------------------
# apply_tick_formatting (integration)
# ---------------------------------------------------------------------------


class TestApplyTickFormatting:
    def test_explicit_freq_overrides_auto(
        self, ax: plt.Axes, quarterly_end_index: pd.DatetimeIndex
    ) -> None:
        """Explicit tick_freq should use data-aligned ticks (not day-1)."""
        rng = np.random.default_rng(42)
        ax.plot(quarterly_end_index, rng.normal(0, 1, len(quarterly_end_index)))

        apply_tick_formatting(ax, tick_freq="year", x_data=quarterly_end_index)

        locator = ax.xaxis.get_major_locator()
        assert isinstance(locator, FixedLocator)

        # Ticks must fall on actual December dates from the index
        tick_dates = [mdates.num2date(t) for t in locator.locs]
        index_dates = {d.date() for d in quarterly_end_index}
        for d in tick_dates:
            assert d.date() in index_dates

    def test_auto_detect_quarterly(
        self, ax: plt.Axes, quarterly_end_index: pd.DatetimeIndex
    ) -> None:
        """Without tick_freq, quarterly data should auto-detect."""
        rng = np.random.default_rng(42)
        ax.plot(quarterly_end_index, rng.normal(0, 1, len(quarterly_end_index)))

        apply_tick_formatting(ax, x_data=quarterly_end_index)

        locator = ax.xaxis.get_major_locator()
        assert isinstance(locator, FixedLocator)
        assert len(locator.locs) == len(quarterly_end_index)

    def test_auto_detect_monthly_no_override(
        self, ax: plt.Axes, monthly_index: pd.DatetimeIndex
    ) -> None:
        """Monthly data should NOT override matplotlib's auto-detection."""
        rng = np.random.default_rng(42)
        ax.plot(monthly_index, rng.normal(0, 1, len(monthly_index)))

        apply_tick_formatting(ax, x_data=monthly_index)

        locator = ax.xaxis.get_major_locator()
        assert not isinstance(locator, FixedLocator)

    def test_tick_format_applied(
        self, ax: plt.Axes, monthly_index: pd.DatetimeIndex
    ) -> None:
        rng = np.random.default_rng(42)
        ax.plot(monthly_index, rng.normal(0, 1, len(monthly_index)))

        apply_tick_formatting(ax, tick_format="%b/%Y", x_data=monthly_index)

        formatter = ax.xaxis.get_major_formatter()
        assert isinstance(formatter, mdates.DateFormatter)

    def test_invalid_tick_freq_raises(self, ax: plt.Axes) -> None:
        from chartkit.exceptions import ValidationError

        with pytest.raises(ValidationError, match="Invalid tick_freq"):
            apply_tick_formatting(ax, tick_freq="biweekly")

    def test_no_x_data_no_auto_detect(self, ax: plt.Axes) -> None:
        """Without x_data, auto-detection should not run."""
        ax.plot(range(10), range(10))
        apply_tick_formatting(ax)
        assert not isinstance(ax.xaxis.get_major_locator(), FixedLocator)

    def test_explicit_quarter_aligns_to_data(
        self, ax: plt.Axes, quarterly_end_index: pd.DatetimeIndex
    ) -> None:
        """tick_freq='quarter' with end-of-month data should produce
        ticks exactly at the data dates, not at day-1 of each month."""
        rng = np.random.default_rng(42)
        ax.bar(
            quarterly_end_index,
            rng.normal(0, 1, len(quarterly_end_index)),
            width=20,
        )

        apply_tick_formatting(ax, tick_freq="quarter", x_data=quarterly_end_index)

        locator = ax.xaxis.get_major_locator()
        assert isinstance(locator, FixedLocator)

        tick_dates = {mdates.num2date(t).date() for t in locator.locs}
        index_dates = {d.date() for d in quarterly_end_index}
        assert tick_dates == index_dates

    def test_no_phantom_ticks_after_data(
        self, ax: plt.Axes, quarterly_end_index: pd.DatetimeIndex
    ) -> None:
        """All ticks must be actual data dates (no phantoms possible)."""
        rng = np.random.default_rng(42)
        ax.bar(
            quarterly_end_index,
            rng.normal(0, 1, len(quarterly_end_index)),
            width=20,
        )

        apply_tick_formatting(ax, tick_freq="quarter", x_data=quarterly_end_index)

        locator = ax.xaxis.get_major_locator()
        assert isinstance(locator, FixedLocator)

        tick_dates = {mdates.num2date(t).date() for t in locator.locs}
        index_dates = {d.date() for d in quarterly_end_index}
        # Data-aligned ticks are always a subset of (or equal to) index dates
        assert tick_dates <= index_dates

    def test_explicit_day_bypasses_data_alignment(
        self, ax: plt.Axes, daily_index: pd.DatetimeIndex
    ) -> None:
        """tick_freq='day' should use matplotlib DayLocator (not _ticks_from_data)."""
        rng = np.random.default_rng(42)
        ax.plot(daily_index, rng.normal(0, 1, len(daily_index)))

        # Should not raise, day is a valid freq but not in _ALIGNABLE_FREQS
        apply_tick_formatting(ax, tick_freq="day", x_data=daily_index)

    def test_explicit_week_bypasses_data_alignment(
        self, ax: plt.Axes, weekly_index: pd.DatetimeIndex
    ) -> None:
        """tick_freq='week' should use matplotlib WeekdayLocator (not _ticks_from_data)."""
        rng = np.random.default_rng(42)
        ax.plot(weekly_index, rng.normal(0, 1, len(weekly_index)))

        # Should not raise, week is a valid freq but not in _ALIGNABLE_FREQS
        apply_tick_formatting(ax, tick_freq="week", x_data=weekly_index)

    def test_explicit_freq_without_x_data_uses_matplotlib(self, ax: plt.Axes) -> None:
        """tick_freq without x_data should fallback to matplotlib locators."""
        ax.plot(range(10), range(10))
        apply_tick_formatting(ax, tick_freq="year")

        locator = ax.xaxis.get_major_locator()
        assert not isinstance(locator, FixedLocator)

    def test_explicit_semester_aligns_to_data(
        self, ax: plt.Axes, quarterly_end_index: pd.DatetimeIndex
    ) -> None:
        """tick_freq='semester' with quarterly data picks Jun/Dec dates."""
        rng = np.random.default_rng(42)
        ax.plot(quarterly_end_index, rng.normal(0, 1, len(quarterly_end_index)))

        apply_tick_formatting(ax, tick_freq="semester", x_data=quarterly_end_index)

        locator = ax.xaxis.get_major_locator()
        assert isinstance(locator, FixedLocator)

        tick_dates = [mdates.num2date(t) for t in locator.locs]
        tick_months = {d.month for d in tick_dates}
        assert tick_months == {6, 12}

        # All ticks are actual data dates
        index_dates = {d.date() for d in quarterly_end_index}
        for d in tick_dates:
            assert d.date() in index_dates

    def test_auto_detect_semiannual(
        self, ax: plt.Axes, semiannual_index: pd.DatetimeIndex
    ) -> None:
        """Semi-annual data should auto-detect with ticks at data dates."""
        rng = np.random.default_rng(42)
        ax.plot(semiannual_index, rng.normal(0, 1, len(semiannual_index)))

        apply_tick_formatting(ax, x_data=semiannual_index)

        locator = ax.xaxis.get_major_locator()
        assert isinstance(locator, FixedLocator)

        tick_months = {mdates.num2date(t).month for t in locator.locs}
        assert tick_months == {6, 12}
