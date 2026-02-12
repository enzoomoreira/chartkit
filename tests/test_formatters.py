from __future__ import annotations

import math

from chartkit.styling.formatters import (
    compact_currency_formatter,
    currency_formatter,
    human_readable_formatter,
    percent_formatter,
    points_formatter,
)


class TestCurrencyFormatter:
    def test_brl_format(self) -> None:
        fmt = currency_formatter("BRL")
        result = fmt(1234.56, None)
        assert "1.234" in result or "1,234" in result  # locale-dependent
        assert result != ""

    def test_usd_format(self) -> None:
        fmt = currency_formatter("USD")
        result = fmt(1234.56, None)
        assert result != ""
        assert "$" in result

    def test_inf_returns_empty(self) -> None:
        fmt = currency_formatter("BRL")
        assert fmt(math.inf, None) == ""
        assert fmt(-math.inf, None) == ""
        assert fmt(math.nan, None) == ""


class TestCompactCurrencyFormatter:
    def test_below_1000_full_format(self) -> None:
        fmt = compact_currency_formatter("BRL")
        result = fmt(500.0, None)
        assert result != ""

    def test_large_value(self) -> None:
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
        # Default locale pt_BR: "10,5%"
        assert "10" in result
        assert "%" in result

    def test_inf_returns_empty(self) -> None:
        fmt = percent_formatter()
        assert fmt(math.inf, None) == ""


class TestHumanReadableFormatter:
    def test_zero(self) -> None:
        fmt = human_readable_formatter()
        assert fmt(0, None) == "0"

    def test_thousands(self) -> None:
        fmt = human_readable_formatter()
        result = fmt(1500.0, None)
        assert "k" in result

    def test_millions(self) -> None:
        fmt = human_readable_formatter()
        result = fmt(1_500_000.0, None)
        assert "M" in result

    def test_inf_returns_empty(self) -> None:
        fmt = human_readable_formatter()
        assert fmt(math.inf, None) == ""


class TestPointsFormatter:
    def test_basic_format(self) -> None:
        fmt = points_formatter()
        result = fmt(1234567.0, None)
        # pt_BR uses "." as thousands separator
        assert "1.234.567" in result or "1,234,567" in result

    def test_zero(self) -> None:
        fmt = points_formatter()
        assert fmt(0, None) == "0"

    def test_inf_returns_empty(self) -> None:
        fmt = points_formatter()
        assert fmt(math.inf, None) == ""
