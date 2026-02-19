from __future__ import annotations

import warnings

import pandas as pd
import pytest

from chartkit.charts._helpers import detect_bar_width, is_categorical_index
from chartkit.settings.schema import BarsConfig


# ---------------------------------------------------------------------------
# detect_bar_width
# ---------------------------------------------------------------------------


class TestDetectBarWidth:
    def test_annual_frequency(self) -> None:
        idx = pd.date_range("2020-12-31", periods=4, freq="YE")
        bars = BarsConfig()
        width = detect_bar_width(idx, bars)
        assert width == float(bars.width_annual)

    def test_monthly_frequency(self) -> None:
        idx = pd.date_range("2023-01-31", periods=12, freq="ME")
        bars = BarsConfig()
        width = detect_bar_width(idx, bars)
        assert width == float(bars.width_monthly)

    def test_object_datetime_index_uses_monthly(self) -> None:
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

    def test_non_datetime_keeps_default(self) -> None:
        idx = pd.Index(["a", "b", "c"], dtype="object")
        bars = BarsConfig()
        width = detect_bar_width(idx, bars)
        assert width == bars.width_default

    def test_no_warning_for_string_index(self) -> None:
        idx = pd.Index(["B3", "NYSE", "LSE"])
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            width = detect_bar_width(idx, BarsConfig())
        assert width == BarsConfig().width_default


# ---------------------------------------------------------------------------
# is_categorical_index
# ---------------------------------------------------------------------------


class TestIsCategoricalIndex:
    @pytest.mark.parametrize(
        "idx, expected",
        [
            (pd.Index(["B3", "NYSE", "LSE"]), True),
            (pd.CategoricalIndex(["A", "B", "C"]), True),
            (pd.Index(["X", "Y", "Z"], dtype="string"), True),
            (pd.date_range("2023-01-01", periods=3, freq="ME"), False),
            (pd.Index([1, 2, 3]), False),
        ],
        ids=["string", "categorical", "string_dtype", "datetime", "numeric"],
    )
    def test_detection(self, idx: pd.Index, expected: bool) -> None:
        assert is_categorical_index(idx) is expected
