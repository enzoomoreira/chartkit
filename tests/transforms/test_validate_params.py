from __future__ import annotations

import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms._validation import (
    _DiffParams,
    _FreqResolvedParams,
    _NormalizeParams,
    _RollingParams,
    _ZScoreParams,
    validate_params,
)


class TestFreqResolvedParams:
    def test_both_none_valid(self) -> None:
        p = validate_params(_FreqResolvedParams)
        assert p.periods is None
        assert p.freq is None

    def test_periods_only_valid(self) -> None:
        p = validate_params(_FreqResolvedParams, periods=12)
        assert p.periods == 12

    def test_freq_only_valid(self) -> None:
        p = validate_params(_FreqResolvedParams, freq="M")
        assert p.freq == "M"

    def test_both_specified_raises(self) -> None:
        with pytest.raises(TransformError, match="Cannot specify both"):
            validate_params(_FreqResolvedParams, periods=12, freq="M")

    def test_negative_periods_raises(self) -> None:
        with pytest.raises(TransformError):
            validate_params(_FreqResolvedParams, periods=-1)

    def test_zero_periods_raises(self) -> None:
        with pytest.raises(TransformError):
            validate_params(_FreqResolvedParams, periods=0)


class TestRollingParams:
    def test_both_none_valid(self) -> None:
        p = validate_params(_RollingParams)
        assert p.window is None

    def test_window_only_valid(self) -> None:
        p = validate_params(_RollingParams, window=6)
        assert p.window == 6

    def test_freq_only_valid(self) -> None:
        p = validate_params(_RollingParams, freq="M")
        assert p.freq == "M"

    def test_both_specified_raises(self) -> None:
        with pytest.raises(TransformError, match="Cannot specify both"):
            validate_params(_RollingParams, window=6, freq="M")

    def test_negative_window_raises(self) -> None:
        with pytest.raises(TransformError):
            validate_params(_RollingParams, window=-1)


class TestDiffParams:
    def test_positive_periods_valid(self) -> None:
        p = validate_params(_DiffParams, periods=1)
        assert p.periods == 1

    def test_negative_periods_valid(self) -> None:
        p = validate_params(_DiffParams, periods=-1)
        assert p.periods == -1

    def test_zero_periods_raises(self) -> None:
        with pytest.raises(TransformError, match="non-zero"):
            validate_params(_DiffParams, periods=0)


class TestZScoreParams:
    def test_none_window_valid(self) -> None:
        p = validate_params(_ZScoreParams)
        assert p.window is None

    def test_window_2_valid(self) -> None:
        p = validate_params(_ZScoreParams, window=2)
        assert p.window == 2

    def test_window_1_raises(self) -> None:
        with pytest.raises(TransformError, match=">= 2"):
            validate_params(_ZScoreParams, window=1)

    def test_large_window_valid(self) -> None:
        p = validate_params(_ZScoreParams, window=100)
        assert p.window == 100


class TestNormalizeParams:
    def test_defaults_valid(self) -> None:
        p = validate_params(_NormalizeParams)
        assert p.base is None
        assert p.base_date is None

    def test_base_positive_valid(self) -> None:
        p = validate_params(_NormalizeParams, base=100)
        assert p.base == 100
