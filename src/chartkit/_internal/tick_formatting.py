"""Temporal tick formatting and frequency control for X-axis."""

from __future__ import annotations

from typing import Literal

import matplotlib.dates as mdates
from matplotlib.axes import Axes

from ..settings import get_config

TickFreq = Literal["day", "week", "month", "quarter", "semester", "year"]

_FREQ_LOCATORS: dict[TickFreq, type[mdates.DateLocator] | tuple] = {
    "day": (mdates.DayLocator, {}),
    "week": (mdates.WeekdayLocator, {"byweekday": mdates.MO}),
    "month": (mdates.MonthLocator, {}),
    "quarter": (mdates.MonthLocator, {"bymonth": [1, 4, 7, 10]}),
    "semester": (mdates.MonthLocator, {"bymonth": [1, 7]}),
    "year": (mdates.YearLocator, {}),
}

__all__ = ["apply_tick_formatting"]


def apply_tick_formatting(
    ax: Axes,
    *,
    tick_format: str | None = None,
    tick_freq: str | None = None,
) -> None:
    """Apply date locator and formatter to the X-axis.

    Precedence: parameter > config > None (matplotlib auto).

    Args:
        ax: Target axes.
        tick_format: Date format string (e.g. ``"%b/%Y"``).
        tick_freq: Tick frequency (``"day"``, ``"week"``, ``"month"``,
            ``"quarter"``, ``"semester"``, ``"year"``).
    """
    config = get_config()

    effective_freq = tick_freq or config.ticks.date_freq
    effective_format = tick_format or config.ticks.date_format

    if effective_freq is not None:
        entry = _FREQ_LOCATORS.get(effective_freq)
        if entry is None:
            valid = ", ".join(f"'{k}'" for k in _FREQ_LOCATORS)
            raise ValueError(
                f"Invalid tick_freq '{effective_freq}'. Valid options: {valid}"
            )
        locator_cls, locator_kwargs = entry
        ax.xaxis.set_major_locator(locator_cls(**locator_kwargs))

    if effective_format is not None:
        ax.xaxis.set_major_formatter(mdates.DateFormatter(effective_format))
