"""Axis formatter tests: currency, compact, percent, human, points, multiplier.

Consolidates: tests/test_formatters.py + tests/internal/test_formatting.py.
"""

from __future__ import annotations

import math

import pytest

from chartkit._internal.formatting import FORMATTERS
from chartkit.styling.formatters import (
    compact_currency_formatter,
    currency_formatter,
    human_readable_formatter,
    multiplier_formatter,
    percent_formatter,
    points_formatter,
)


class TestCurrencyFormatter:
    def test_brl_contains_thousands(self) -> None:
        fmt = currency_formatter("BRL")
        result = fmt(1234.56, None)
        assert "1.234" in result or "1,234" in result

    def test_usd_contains_dollar_sign(self) -> None:
        fmt = currency_formatter("USD")
        result = fmt(1234.56, None)
        assert "$" in result

    @pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
    def test_non_finite_returns_empty(self, value: float) -> None:
        fmt = currency_formatter("BRL")
        assert fmt(value, None) == ""

    def test_negative_value_formatted(self) -> None:
        fmt = currency_formatter("BRL")
        result = fmt(-500.0, None)
        assert result != ""
        assert "-" in result or "(" in result


class TestCompactCurrencyFormatter:
    def test_below_1000_uses_full_format(self) -> None:
        fmt = compact_currency_formatter("BRL")
        result = fmt(500.0, None)
        assert result != ""

    def test_millions_compacted(self) -> None:
        fmt = compact_currency_formatter("BRL")
        result = fmt(1_500_000.0, None)
        assert result != ""

    def test_inf_returns_empty(self) -> None:
        fmt = compact_currency_formatter("BRL")
        assert fmt(math.inf, None) == ""


class TestPercentFormatter:
    def test_basic_percent(self) -> None:
        fmt = percent_formatter()
        result = fmt(10.5, None)
        assert "10" in result
        assert "%" in result

    def test_inf_returns_empty(self) -> None:
        fmt = percent_formatter()
        assert fmt(math.inf, None) == ""


class TestHumanReadableFormatter:
    def test_zero_returns_zero(self) -> None:
        fmt = human_readable_formatter()
        assert fmt(0, None) == "0"

    def test_thousands_suffix(self) -> None:
        fmt = human_readable_formatter()
        assert "k" in fmt(1500.0, None)

    def test_millions_suffix(self) -> None:
        fmt = human_readable_formatter()
        assert "M" in fmt(1_500_000.0, None)

    def test_inf_returns_empty(self) -> None:
        fmt = human_readable_formatter()
        assert fmt(math.inf, None) == ""


class TestPointsFormatter:
    def test_thousands_separated(self) -> None:
        fmt = points_formatter()
        result = fmt(1234567.0, None)
        assert "1.234.567" in result or "1,234,567" in result

    def test_zero_returns_zero(self) -> None:
        fmt = points_formatter()
        assert fmt(0, None) == "0"

    def test_inf_returns_empty(self) -> None:
        fmt = points_formatter()
        assert fmt(math.inf, None) == ""


class TestMultiplierFormatter:
    def test_decimal_value(self) -> None:
        fmt = multiplier_formatter()
        result = fmt(12.3, None)
        assert "x" in result
        assert "12" in result

    def test_integer_value(self) -> None:
        fmt = multiplier_formatter()
        result = fmt(5.0, None)
        assert result == "5x"

    def test_zero_returns_zero_x(self) -> None:
        fmt = multiplier_formatter()
        assert fmt(0, None) == "0x"

    def test_negative_value(self) -> None:
        fmt = multiplier_formatter()
        result = fmt(-2.5, None)
        assert "x" in result
        assert "-" in result

    def test_inf_returns_empty(self) -> None:
        fmt = multiplier_formatter()
        assert fmt(math.inf, None) == ""


class TestFormatterDispatchTable:
    EXPECTED_KEYS = {
        "BRL",
        "USD",
        "BRL_compact",
        "USD_compact",
        "%",
        "human",
        "points",
        "x",
    }

    def test_all_keys_present(self) -> None:
        assert set(FORMATTERS.keys()) == self.EXPECTED_KEYS

    @pytest.mark.parametrize("key", sorted(EXPECTED_KEYS))
    def test_factory_returns_callable(self, key: str) -> None:
        assert callable(FORMATTERS[key]())
