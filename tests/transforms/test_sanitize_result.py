from __future__ import annotations

import numpy as np
import pandas as pd

from chartkit.transforms._validation import sanitize_result


def test_inf_replaced_with_nan() -> None:
    s = pd.Series([1.0, np.inf, 3.0])
    result = sanitize_result(s)
    assert np.isnan(result.iloc[1])
    assert result.iloc[0] == 1.0
    assert result.iloc[2] == 3.0


def test_neg_inf_replaced_with_nan() -> None:
    s = pd.Series([1.0, -np.inf, 3.0])
    result = sanitize_result(s)
    assert np.isnan(result.iloc[1])


def test_normal_values_unchanged() -> None:
    s = pd.Series([1.0, 2.0, 3.0])
    result = sanitize_result(s)
    pd.testing.assert_series_equal(result, s)


def test_nan_stays_nan() -> None:
    s = pd.Series([1.0, np.nan, 3.0])
    result = sanitize_result(s)
    assert np.isnan(result.iloc[1])
    assert result.iloc[0] == 1.0
