"""Y-axis formatter dispatch table."""

from __future__ import annotations

from typing import get_args

from .plot_validation import UnitFormat
from ..styling import (
    compact_currency_formatter,
    currency_formatter,
    human_readable_formatter,
    percent_formatter,
    points_formatter,
)

__all__ = ["FORMATTERS"]

FORMATTERS = {
    "BRL": lambda: currency_formatter("BRL"),
    "USD": lambda: currency_formatter("USD"),
    "BRL_compact": lambda: compact_currency_formatter("BRL"),
    "USD_compact": lambda: compact_currency_formatter("USD"),
    "%": percent_formatter,
    "human": human_readable_formatter,
    "points": points_formatter,
}

assert set(FORMATTERS.keys()) == set(get_args(UnitFormat)), (
    f"FORMATTERS keys {set(FORMATTERS.keys())} != UnitFormat {set(get_args(UnitFormat))}"
)
