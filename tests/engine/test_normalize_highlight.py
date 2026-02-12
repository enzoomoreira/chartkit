from __future__ import annotations

import pytest

from chartkit.engine import _normalize_highlight
from chartkit.exceptions import ValidationError


class TestNormalizeHighlight:
    def test_true_returns_last(self) -> None:
        assert _normalize_highlight(True) == ["last"]

    def test_false_returns_empty(self) -> None:
        assert _normalize_highlight(False) == []

    def test_string_last(self) -> None:
        assert _normalize_highlight("last") == ["last"]

    def test_string_max(self) -> None:
        assert _normalize_highlight("max") == ["max"]

    def test_string_min(self) -> None:
        assert _normalize_highlight("min") == ["min"]

    def test_invalid_string_raises(self) -> None:
        with pytest.raises(ValidationError, match="invalid"):
            _normalize_highlight("invalid_mode")

    def test_list_of_modes(self) -> None:
        result = _normalize_highlight(["last", "max"])
        assert result == ["last", "max"]

    def test_list_with_invalid_raises(self) -> None:
        with pytest.raises(ValidationError, match="invalid"):
            _normalize_highlight(["last", "xyz"])
