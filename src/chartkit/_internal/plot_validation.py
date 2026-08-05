"""Shared runtime validation for plot-related parameters."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, StrictBool
from pydantic import ValidationError as PydanticValidationError

from ..exceptions import ValidationError

logger = logging.getLogger(__name__)

UnitFormat = Literal[
    "BRL", "USD", "BRL_compact", "USD_compact", "%", "human", "points", "x"
]

TickFreq = Literal["day", "week", "month", "quarter", "semester", "year"]

AxisValue = str | int | float | datetime | date | pd.Timestamp | None
AxisLimits = tuple[AxisValue, AxisValue]


class PlotParamsModel(BaseModel):
    units: UnitFormat | None = None
    legend: StrictBool | None = None
    tick_freq: TickFreq | None = None


def validate_plot_params(
    units: UnitFormat | None,
    legend: bool | None,
    tick_freq: str | None = None,
) -> None:
    """Validate generic plot params and normalize pydantic errors."""
    try:
        PlotParamsModel(units=units, legend=legend, tick_freq=tick_freq)
    except PydanticValidationError as exc:
        errors = exc.errors()
        msgs = [
            f"  {e['loc'][0]}: {e['msg']}" if e.get("loc") else f"  {e['msg']}"
            for e in errors
        ]
        raise ValidationError("Invalid plot parameters:\n" + "\n".join(msgs)) from exc


def _coerce_limit_value(value: AxisValue, prefer_dates: bool) -> Any:
    """Coerce a single axis limit value.

    Strings are tried as float first (so ``"100"`` stays numeric), then as date
    via ``pd.to_datetime``.  On a date axis the order is reversed: ``"2024"``
    is a year there, and reading it as ``2024.0`` would put the limit two
    millennia away from the data.
    """
    if value is None or not isinstance(value, str):
        return value

    attempts = (
        (pd.to_datetime, "datetime") if prefer_dates else (float, "float"),
        (float, "float") if prefer_dates else (pd.to_datetime, "datetime"),
    )

    for convert, label in attempts:
        try:
            result = convert(value)
        except (ValueError, TypeError):
            continue
        logger.debug("Coerced axis limit '%s' -> %s(%s)", value, label, result)
        return result

    raise ValidationError(
        f"Cannot interpret '{value}' as a number or date for axis limit."
    )


def coerce_axis_limits(
    limits: tuple[Any, Any], *, prefer_dates: bool = False
) -> tuple[Any, Any]:
    """Coerce axis limit values, converting strings to dates or numbers.

    Accepts ``(min, max)`` where each element can be a string
    (``"2024-01-01"`` or ``"100"``), numeric, datetime, or ``None``.

    Args:
        prefer_dates: Resolve ambiguous strings such as ``"2024"`` as dates
            rather than numbers.  Set when the target axis carries dates.
    """
    if len(limits) != 2:
        raise ValidationError(
            f"Axis limits must be a 2-tuple (min, max), got {len(limits)} elements."
        )
    return (
        _coerce_limit_value(limits[0], prefer_dates),
        _coerce_limit_value(limits[1], prefer_dates),
    )


__all__ = [
    "AxisLimits",
    "TickFreq",
    "UnitFormat",
    "coerce_axis_limits",
    "validate_plot_params",
]
