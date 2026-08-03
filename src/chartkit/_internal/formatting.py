"""Y-axis formatter dispatch table."""

from __future__ import annotations

from typing import get_args

from ..styling import (
    compact_currency_formatter,
    currency_formatter,
    human_readable_formatter,
    multiplier_formatter,
    percent_formatter,
    points_formatter,
)
from .plot_validation import UnitFormat

__all__ = ["FORMATTERS", "get_formatter"]

FORMATTERS = {
    "BRL": lambda: currency_formatter("BRL"),
    "USD": lambda: currency_formatter("USD"),
    "BRL_compact": lambda: compact_currency_formatter("BRL"),
    "USD_compact": lambda: compact_currency_formatter("USD"),
    "%": percent_formatter,
    "human": human_readable_formatter,
    "points": points_formatter,
    "x": multiplier_formatter,
}

assert set(FORMATTERS.keys()) == set(get_args(UnitFormat)), (
    f"FORMATTERS keys {set(FORMATTERS.keys())} != UnitFormat {set(get_args(UnitFormat))}"
)


def get_formatter(units: UnitFormat, decimals: int | None = None):
    """Return the formatter for *units*, optionally overriding decimal places.

    For ``units`` that support a ``decimals`` argument (``"%"``, ``"human"``,
    ``"points"``, ``"x"``), *decimals* overrides the default when provided.
    For compact-currency units (``"BRL_compact"``, ``"USD_compact"``), *decimals*
    maps to ``fraction_digits``.  For full-currency units the argument is ignored.
    """
    if decimals is None:
        return FORMATTERS[units]()

    if units == "%":
        return percent_formatter(decimals=decimals)
    if units == "human":
        return human_readable_formatter(decimals=decimals)
    if units == "points":
        return points_formatter(decimals=decimals)
    if units == "x":
        return multiplier_formatter(decimals=decimals)
    if units == "BRL_compact":
        return compact_currency_formatter("BRL", fraction_digits=decimals)
    if units == "USD_compact":
        return compact_currency_formatter("USD", fraction_digits=decimals)

    # BRL / USD: decimal places controlled by Babel; ignore decimals
    return FORMATTERS[units]()
