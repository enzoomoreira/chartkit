from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# DatetimeIndex helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def daily_index() -> pd.DatetimeIndex:
    """252 business days (~1 year) starting 2023-01-02."""
    return pd.bdate_range("2023-01-02", periods=252, freq="B")


@pytest.fixture
def monthly_index() -> pd.DatetimeIndex:
    """24 months starting 2023-01-31."""
    return pd.date_range("2023-01-31", periods=24, freq="ME")


# ---------------------------------------------------------------------------
# Financial DataFrames (seed fixa para reprodutibilidade)
# ---------------------------------------------------------------------------


@pytest.fixture
def monthly_rates(monthly_index: pd.DatetimeIndex) -> pd.DataFrame:
    """Monthly return rates (cdi ~1%, ipca ~0.5%)."""
    rng = np.random.default_rng(42)
    n = len(monthly_index)
    return pd.DataFrame(
        {"cdi": rng.normal(1.0, 0.15, n), "ipca": rng.normal(0.5, 0.2, n)},
        index=monthly_index,
    )


@pytest.fixture
def daily_prices(daily_index: pd.DatetimeIndex) -> pd.DataFrame:
    """Daily stock prices (geometric random walk from 100)."""
    rng = np.random.default_rng(42)
    n = len(daily_index)
    log_returns = rng.normal(0.0004, 0.015, n)
    prices = 100 * np.exp(np.cumsum(log_returns))
    return pd.DataFrame({"price": prices}, index=daily_index)


@pytest.fixture
def multi_series_monthly(monthly_index: pd.DatetimeIndex) -> pd.DataFrame:
    """3 numeric + 1 string column on monthly index."""
    rng = np.random.default_rng(42)
    n = len(monthly_index)
    return pd.DataFrame(
        {
            "fund_a": rng.normal(1.2, 0.3, n),
            "fund_b": rng.normal(0.8, 0.4, n),
            "fund_c": rng.normal(1.5, 0.5, n),
            "category": ["equity"] * n,
        },
        index=monthly_index,
    )


@pytest.fixture
def single_series(monthly_index: pd.DatetimeIndex) -> pd.Series:
    """Monthly numeric Series."""
    rng = np.random.default_rng(42)
    return pd.Series(
        rng.normal(1.0, 0.2, len(monthly_index)),
        index=monthly_index,
        name="rate",
    )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.fixture
def empty_df() -> pd.DataFrame:
    return pd.DataFrame()


@pytest.fixture
def empty_series() -> pd.Series:
    return pd.Series(dtype=float)


@pytest.fixture
def all_nan_series(monthly_index: pd.DatetimeIndex) -> pd.Series:
    return pd.Series(np.nan, index=monthly_index, name="nan_series")


@pytest.fixture
def constant_series(monthly_index: pd.DatetimeIndex) -> pd.Series:
    """All values are the same (std=0)."""
    return pd.Series(5.0, index=monthly_index, name="const")


@pytest.fixture
def non_datetime_index_df() -> pd.DataFrame:
    """DataFrame with integer index (no DatetimeIndex)."""
    return pd.DataFrame({"val": [1.0, 2.0, 3.0, 4.0, 5.0]})
