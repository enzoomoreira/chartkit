"""Shared runtime validation for plot-related parameters."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

import pandas as pd
from loguru import logger
from pydantic import BaseModel, StrictBool
from pydantic import ValidationError as PydanticValidationError

from ..exceptions import ValidationError

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


def _coerce_limit_value(value: AxisValue) -> Any:
    """Coerce a single axis limit value.

    Strings are tried as float first (so ``"100"`` stays numeric),
    then as date via ``pd.to_datetime``.
    """
    if value is None or not isinstance(value, str):
        return value

    try:
        result = float(value)
        logger.debug("Coerced axis limit '{}' -> float({})", value, result)
        return result
    except ValueError:
        pass

    try:
        result = pd.to_datetime(value)
        logger.debug("Coerced axis limit '{}' -> datetime({})", value, result)
        return result
    except (ValueError, TypeError):
        raise ValidationError(
            f"Cannot interpret '{value}' as a number or date for axis limit."
        ) from None


def coerce_axis_limits(limits: tuple[Any, Any]) -> tuple[Any, Any]:
    """Coerce axis limit values, converting strings to dates or numbers.

    Accepts ``(min, max)`` where each element can be a string
    (``"2024-01-01"`` or ``"100"``), numeric, datetime, or ``None``.
    """
    if len(limits) != 2:
        raise ValidationError(
            f"Axis limits must be a 2-tuple (min, max), got {len(limits)} elements."
        )
    return (_coerce_limit_value(limits[0]), _coerce_limit_value(limits[1]))


__all__ = [
    "AxisLimits",
    "TickFreq",
    "UnitFormat",
    "coerce_axis_limits",
    "validate_plot_params",
]
