"""Tests for chartkit.transforms.temporal.diff.

Covers: known-value correctness, negative periods (forward diff),
zero periods validation, default periods.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from chartkit.exceptions import TransformError
from chartkit.transforms.temporal import diff


class TestDiffKnownValues:
    def test_basic_diff(self) -> None:
        """[10, 12, 15] periods=1 -> [NaN, 2, 3]."""
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"val": [10.0, 12.0, 15.0]}, index=idx)
        result = diff(df)
        assert np.isnan(result["val"].iloc[0])
        assert result["val"].iloc[1] == pytest.approx(2.0)
        assert result["val"].iloc[2] == pytest.approx(3.0)

    def test_negative_periods_forward_diff(self) -> None:
        """periods=-1 computes forward difference."""
        idx = pd.date_range("2023-01-31", periods=3, freq="ME")
        df = pd.DataFrame({"val": [10.0, 12.0, 15.0]}, index=idx)
        result = diff(df, periods=-1)
        assert result["val"].iloc[0] == pytest.approx(-2.0)
        assert result["val"].iloc[1] == pytest.approx(-3.0)
        assert np.isnan(result["val"].iloc[2])

    def test_default_periods_is_1(self, monthly_rates: pd.DataFrame) -> None:
        """Default periods=1: first row NaN, rest computed."""
        result = diff(monthly_rates)
        assert result.iloc[0].isna().all()
        assert not result.iloc[1].isna().any()


class TestDiffValidation:
    def test_zero_periods_raises(self, monthly_rates: pd.DataFrame) -> None:
        with pytest.raises(TransformError, match="non-zero"):
            diff(monthly_rates, periods=0)
