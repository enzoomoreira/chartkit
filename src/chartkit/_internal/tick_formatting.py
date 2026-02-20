"""Temporal tick formatting and frequency control for X-axis."""

from __future__ import annotations

from typing import Literal

import matplotlib.dates as mdates
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.ticker import FixedLocator

from ..settings import get_config

TickFreq = Literal["day", "week", "month", "quarter", "semester", "year"]

_FREQ_LOCATORS: dict[TickFreq, type[mdates.DateLocator] | tuple] = {
    "day": (mdates.DayLocator, {}),
    "week": (mdates.WeekdayLocator, {"byweekday": mdates.MO}),
    "month": (mdates.MonthLocator, {}),
    "quarter": (mdates.MonthLocator, {"bymonth": [3, 6, 9, 12]}),
    "semester": (mdates.MonthLocator, {"bymonth": [6, 12]}),
    "year": (mdates.YearLocator, {}),
}

_ALIGNABLE_FREQS: set[TickFreq] = {"month", "quarter", "semester", "year"}

__all__ = ["apply_tick_formatting"]


def _to_datetime_index(
    x_data: pd.Index | pd.Series | None,
) -> pd.DatetimeIndex | None:
    """Convert x_data to DatetimeIndex if possible, else return None."""
    if x_data is None:
        return None
    if isinstance(x_data, pd.DatetimeIndex):
        return x_data
    if isinstance(x_data, pd.Series) and pd.api.types.is_datetime64_any_dtype(x_data):
        return pd.DatetimeIndex(x_data)
    if isinstance(x_data, pd.Index) and pd.api.types.is_datetime64_any_dtype(x_data):
        return pd.DatetimeIndex(x_data)
    return None


def _period_key(dt: pd.Timestamp, freq: TickFreq) -> tuple[int, ...]:
    """Return a grouping key for *dt* based on the requested frequency.

    The key determines which period a date belongs to, enabling
    selection of the last real data point in each period.
    """
    year, month = dt.year, dt.month
    if freq == "year":
        return (year,)
    if freq == "semester":
        return (year, 1 if month <= 6 else 2)
    if freq == "quarter":
        return (year, (month - 1) // 3)
    # month
    return (year, month)


def _ticks_from_data(index: pd.DatetimeIndex, freq: TickFreq) -> FixedLocator | None:
    """Select ticks from real data points, grouped by *freq*.

    Iterates the index and keeps the **last** date per period
    (natural dict overwrite preserves insertion order).
    Returns ``None`` when fewer than 2 ticks would result.
    """
    if len(index) < 2:
        return None

    groups: dict[tuple[int, ...], pd.Timestamp] = {}
    for dt in index:
        groups[_period_key(dt, freq)] = dt

    if len(groups) < 2:
        return None

    tick_nums = [mdates.date2num(d) for d in groups.values()]
    return FixedLocator(tick_nums)


def _strip_multiplier(freq: str) -> str:
    """Strip leading numeric multiplier from a pandas freq code.

    ``"2QE-DEC"`` -> ``"QE-DEC"``, ``"6ME"`` -> ``"ME"``,
    ``"QE-DEC"`` -> ``"QE-DEC"`` (no change).
    """
    i = 0
    while i < len(freq) and freq[i].isdigit():
        i += 1
    return freq[i:]


def _is_sparse(freq_base: str) -> bool:
    """Return True for sparse frequencies that benefit from data-aligned ticks."""
    return freq_base.startswith(("YE", "YS", "BY", "QE", "QS", "BQ"))


def _infer_locator(x_data: pd.Index | pd.Series) -> FixedLocator | None:
    """Infer a tick locator aligned to actual data points.

    Uses ``pd.infer_freq()`` to detect the data frequency (same approach
    as the transforms module).  For sparse frequencies (quarterly,
    semi-annual, annual) returns a ``FixedLocator`` whose ticks fall
    exactly on the real index dates -- avoiding the day-1 misalignment
    inherent in ``MonthLocator`` / ``YearLocator``.

    For dense data (daily, weekly, monthly) returns ``None`` to let
    matplotlib auto-detect.
    """
    index = _to_datetime_index(x_data)
    if index is None or len(index) < 3:
        return None

    try:
        freq = pd.infer_freq(index)
    except (TypeError, ValueError):
        return None

    if freq is None:
        return None

    base = _strip_multiplier(freq)

    if _is_sparse(base):
        tick_nums = [mdates.date2num(d) for d in index]
        return FixedLocator(tick_nums)

    return None


def _clip_ticks_to_data(ax: Axes, x_data: pd.Index | pd.Series) -> None:
    """Constrain major ticks to the actual data range.

    Removes phantom ticks that fall outside the data boundaries.  These
    appear when the view limits (xlim) extend beyond the data, e.g. due
    to bar chart padding.

    Uses month-level boundaries (first day of first month, last day of
    last month) so that ``MonthLocator`` ticks on day-1 are not
    accidentally filtered out when data uses end-of-month dates.
    """
    index = _to_datetime_index(x_data)
    if index is None or len(index) < 2:
        return

    # Month-level boundaries: include any tick in the same month as
    # the first/last data point.
    first = index.min()
    last = index.max()
    month_start = first.replace(day=1)
    month_end = (last + pd.offsets.MonthEnd(0)).normalize() + pd.Timedelta(days=1)

    bound_lo = mdates.date2num(month_start)
    bound_hi = mdates.date2num(month_end)

    xlim = ax.get_xlim()
    locator = ax.xaxis.get_major_locator()

    # DateLocator.tick_values expects datetime objects, not raw floats
    vmin = mdates.num2date(xlim[0])
    vmax = mdates.num2date(xlim[1])
    tick_values = locator.tick_values(vmin, vmax)

    filtered = [t for t in tick_values if bound_lo <= t <= bound_hi]
    if filtered:
        ax.xaxis.set_major_locator(FixedLocator(filtered))


def apply_tick_formatting(
    ax: Axes,
    *,
    tick_format: str | None = None,
    tick_freq: str | None = None,
    x_data: pd.Index | pd.Series | None = None,
) -> None:
    """Apply date locator and formatter to the X-axis.

    Precedence: ``tick_freq`` parameter > config > auto-detection from
    ``x_data`` > None (matplotlib default).

    When no explicit frequency is set, inspects ``x_data`` to infer the
    data's temporal pattern and aligns ticks to the actual data points.
    This prevents the common misalignment where, e.g., quarterly data at
    end-of-quarter dates (Mar, Jun, Sep, Dec) gets ticks placed at
    start-of-quarter months (Jan, Apr, Jul, Oct).

    After setting the locator, ticks outside the data range are removed
    to prevent phantom periods caused by xlim padding.
    """
    config = get_config()

    effective_freq = tick_freq or config.ticks.date_freq
    effective_format = tick_format or config.ticks.date_format

    locator_was_set = False

    if effective_freq is not None:
        # Validate freq before anything else
        if effective_freq not in _FREQ_LOCATORS:
            valid = ", ".join(f"'{k}'" for k in _FREQ_LOCATORS)
            raise ValueError(
                f"Invalid tick_freq '{effective_freq}'. Valid options: {valid}"
            )

        # Try data-aligned ticks for sparse frequencies with datetime x_data
        index = _to_datetime_index(x_data)
        aligned = None
        if index is not None and effective_freq in _ALIGNABLE_FREQS:
            aligned = _ticks_from_data(index, effective_freq)

        if aligned is not None:
            ax.xaxis.set_major_locator(aligned)
        else:
            locator_cls, locator_kwargs = _FREQ_LOCATORS[effective_freq]
            ax.xaxis.set_major_locator(locator_cls(**locator_kwargs))

        locator_was_set = True
    elif x_data is not None:
        locator = _infer_locator(x_data)
        if locator is not None:
            ax.xaxis.set_major_locator(locator)
            locator_was_set = True

    if locator_was_set and x_data is not None:
        _clip_ticks_to_data(ax, x_data)

    if effective_format is not None:
        ax.xaxis.set_major_formatter(mdates.DateFormatter(effective_format))
