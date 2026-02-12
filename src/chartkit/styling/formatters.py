"""Axis formatters for matplotlib."""

import math

from babel.numbers import format_compact_currency as babel_format_compact_currency
from babel.numbers import format_currency as babel_format_currency
from matplotlib.ticker import FuncFormatter

from ..settings import get_config


def currency_formatter(currency: str = "BRL") -> FuncFormatter:
    """Full currency formatter (e.g. ``R$ 1.234,56``)."""
    config = get_config()
    locale = config.formatters.locale.babel_locale

    def _format(x: float, pos: int | None) -> str:
        if not math.isfinite(x):
            return ""
        return babel_format_currency(
            x,
            currency,
            locale=locale,
            currency_digits=True,
            group_separator=True,
        )

    return FuncFormatter(_format)


def compact_currency_formatter(
    currency: str = "BRL", fraction_digits: int = 1
) -> FuncFormatter:
    """Compact currency formatter (e.g. ``R$ 1,2 mi``).

    Values below 1000 automatically use the full format.
    """
    config = get_config()
    locale = config.formatters.locale.babel_locale

    def _format(x: float, pos: int | None) -> str:
        if not math.isfinite(x):
            return ""
        if abs(x) < 1000:
            return babel_format_currency(x, currency, locale=locale)

        return babel_format_compact_currency(
            x,
            currency,
            locale=locale,
            fraction_digits=fraction_digits,
        )

    return FuncFormatter(_format)


def percent_formatter(decimals: int = 1) -> FuncFormatter:
    """Percent formatter with thousands separator (e.g. ``10.234,5%``)."""
    config = get_config()
    locale = config.formatters.locale

    def _format(x: float, pos: int | None) -> str:
        if not math.isfinite(x):
            return ""
        formatted = f"{x:,.{decimals}f}%"
        formatted = (
            formatted.replace(",", "X")
            .replace(".", locale.decimal)
            .replace("X", locale.thousands)
        )
        return formatted

    return FuncFormatter(_format)


def human_readable_formatter(decimals: int = 1) -> FuncFormatter:
    """Magnitude suffix formatter (e.g. ``1,5M``, ``300k``)."""
    config = get_config()
    suffixes = config.formatters.magnitude.suffixes
    locale = config.formatters.locale

    def _format(x: float, pos: int | None) -> str:
        if not math.isfinite(x):
            return ""
        if x == 0:
            return "0"

        magnitude = 0
        while abs(x) >= 1000 and magnitude < len(suffixes) - 1:
            magnitude += 1
            x /= 1000.0

        suffix = suffixes[magnitude]
        if x == int(x):
            return f"{int(x)}{suffix}"

        formatted = f"{x:.{decimals}f}{suffix}"
        return formatted.replace(".", locale.decimal)

    return FuncFormatter(_format)


def points_formatter(decimals: int = 0) -> FuncFormatter:
    """Numeric formatter with thousands separator (e.g. ``1.234.567``)."""
    config = get_config()
    locale = config.formatters.locale

    def _format(x: float, pos: int | None) -> str:
        if not math.isfinite(x):
            return ""
        if x == 0:
            return "0"

        if decimals == 0 or x == int(x):
            formatted = f"{int(x):,}"
            return formatted.replace(",", locale.thousands)
        else:
            formatted = f"{x:,.{decimals}f}"
            formatted = (
                formatted.replace(",", "X")
                .replace(".", locale.decimal)
                .replace("X", locale.thousands)
            )
            return formatted

    return FuncFormatter(_format)
