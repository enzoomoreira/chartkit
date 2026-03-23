"""Highlight input normalization tests.

Consolidates: tests/engine/test_normalize_highlight.py.
"""

from __future__ import annotations

import pytest

from chartkit._internal.highlight import normalize_highlight
from chartkit.exceptions import ValidationError


class TestNormalizeHighlight:
    def test_true_returns_last(self) -> None:
        assert normalize_highlight(True) == ["last"]

    def test_false_returns_empty(self) -> None:
        assert normalize_highlight(False) == []

    @pytest.mark.parametrize("mode", ["last", "max", "min", "all"])
    def test_valid_string_wrapped_in_list(self, mode: str) -> None:
        assert normalize_highlight(mode) == [mode]

    def test_invalid_string_raises(self) -> None:
        with pytest.raises(ValidationError, match="invalid"):
            normalize_highlight("invalid_mode")

    def test_list_of_valid_modes(self) -> None:
        assert normalize_highlight(["last", "max"]) == ["last", "max"]

    def test_list_with_invalid_mode_raises(self) -> None:
        with pytest.raises(ValidationError, match="invalid"):
            normalize_highlight(["last", "xyz"])
