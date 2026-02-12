from __future__ import annotations

import warnings

import pandas as pd

from chartkit.charts._helpers import detect_bar_width, is_categorical_index
from chartkit.settings.schema import BarsConfig


def test_detect_bar_width_object_datetime_index_uses_monthly_width() -> None:
    idx = pd.Index(
        [
            pd.Timestamp("2025-01-31"),
            pd.Timestamp("2025-02-28"),
            pd.Timestamp("2025-03-31"),
        ],
        dtype="object",
    )
    bars = BarsConfig()
    width = detect_bar_width(idx, bars)
    assert width == float(bars.width_monthly)


def test_detect_bar_width_non_datetime_keeps_default() -> None:
    idx = pd.Index(["a", "b", "c"], dtype="object")
    bars = BarsConfig()
    width = detect_bar_width(idx, bars)
    assert width == bars.width_default


class TestIsCategoricalIndex:
    def test_string_index(self) -> None:
        idx = pd.Index(["B3", "NYSE", "LSE"])
        assert is_categorical_index(idx) is True

    def test_datetime_index(self) -> None:
        idx = pd.date_range("2023-01-01", periods=3, freq="ME")
        assert is_categorical_index(idx) is False

    def test_numeric_index(self) -> None:
        idx = pd.Index([1, 2, 3])
        assert is_categorical_index(idx) is False

    def test_pd_categorical(self) -> None:
        idx = pd.CategoricalIndex(["A", "B", "C"])
        assert is_categorical_index(idx) is True

    def test_pd_string_dtype(self) -> None:
        idx = pd.Index(["X", "Y", "Z"], dtype="string")
        assert is_categorical_index(idx) is True


def test_coerce_datetime_no_warning_for_strings() -> None:
    idx = pd.Index(["B3", "NYSE", "LSE"])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        width = detect_bar_width(idx, BarsConfig())
    assert width == BarsConfig().width_default
