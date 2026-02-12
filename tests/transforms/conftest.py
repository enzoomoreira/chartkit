from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def known_variation_data() -> pd.DataFrame:
    """[100, 110, 99, 108] -> month variation: [NaN, 10.0, -10.0, 9.0909...]"""
    idx = pd.date_range("2023-01-31", periods=4, freq="ME")
    return pd.DataFrame({"price": [100.0, 110.0, 99.0, 108.0]}, index=idx)


@pytest.fixture
def known_accum_data() -> pd.DataFrame:
    """[1%, 2%, 3%] window=3 -> (1.01*1.02*1.03 - 1)*100 = 6.1106%"""
    idx = pd.date_range("2023-01-31", periods=3, freq="ME")
    return pd.DataFrame({"rate": [1.0, 2.0, 3.0]}, index=idx)


@pytest.fixture
def known_normalize_data() -> pd.DataFrame:
    """[50, 100, 150, 200] base=100 -> [100, 200, 300, 400]"""
    idx = pd.date_range("2023-01-31", periods=4, freq="ME")
    return pd.DataFrame({"val": [50.0, 100.0, 150.0, 200.0]}, index=idx)


@pytest.fixture
def known_drawdown_data() -> pd.DataFrame:
    """[100, 120, 90, 110] -> [0%, 0%, -25%, -8.333...]"""
    idx = pd.date_range("2023-01-31", periods=4, freq="ME")
    return pd.DataFrame({"price": [100.0, 120.0, 90.0, 110.0]}, index=idx)


@pytest.fixture
def known_zscore_data() -> pd.Series:
    """[10, 20, 30] mean=20 std=10 -> zscore: [-1, 0, 1]"""
    idx = pd.date_range("2023-01-31", periods=3, freq="ME")
    return pd.Series([10.0, 20.0, 30.0], index=idx, name="val")
