"""Public parameter types for the transform API.

These are the same sets the pydantic validators enforce at runtime, exposed as
``Literal`` aliases so editors can complete them and type checkers can reject a
typo before the call is made.
"""

from __future__ import annotations

from typing import Literal

__all__ = [
    "DespikeMethod",
    "Freq",
    "Horizon",
    "ResampleFreq",
    "ResampleMethod",
]

Horizon = Literal["month", "year"]

Freq = Literal[
    "D",
    "B",
    "W",
    "M",
    "Q",
    "Y",
    "BME",
    "BMS",
    "daily",
    "business",
    "weekly",
    "monthly",
    "quarterly",
    "yearly",
    "annual",
]

DespikeMethod = Literal["median", "interpolate"]

ResampleFreq = Literal[
    "day",
    "D",
    "week",
    "W",
    "month",
    "M",
    "quarter",
    "Q",
    "year",
    "Y",
    "annual",
]

ResampleMethod = Literal["last", "first", "mean", "sum"]
