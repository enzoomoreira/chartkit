"""Synthetic Brazilian macro series used by the gallery examples.

The numbers are ILLUSTRATIVE, not observations. They are drawn from a fixed
seed so every example renders identically on every machine, and their orders
of magnitude follow the real series closely enough that the formatting and
frequency handling on display are the ones a reader would actually hit. Do
not cite them: for real data use the BCB SGS or IBGE SIDRA APIs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "monthly_index",
    "ipca_monthly",
    "selic_target",
    "usd_brl",
    "gdp_quarterly",
]

_SEED = 42


def monthly_index(periods: int = 60) -> pd.DatetimeIndex:
    """Month-end index ending in 2025-12, long enough for a 12-month window."""
    return pd.date_range(end="2025-12-31", periods=periods, freq="ME")


def ipca_monthly() -> pd.DataFrame:
    """Monthly inflation in percent, with the seasonal shape of the real index."""
    idx = monthly_index()
    rng = np.random.default_rng(_SEED)

    # Food and schooling put a bump early in the year; November is usually mild.
    seasonal = 0.18 * np.sin(2 * np.pi * (idx.month - 3) / 12)
    drift = np.linspace(0.62, 0.34, len(idx))
    noise = rng.normal(0, 0.11, len(idx))

    return pd.DataFrame({"IPCA": (drift + seasonal + noise).round(2)}, index=idx)


def selic_target() -> pd.DataFrame:
    """Policy rate in percent per year, moving in the discrete steps Copom uses."""
    idx = monthly_index()
    # A tightening cycle, a plateau, and a partial easing -- the shape of a
    # rate path, held flat between meetings rather than drifting daily.
    path = (
        [2.00, 2.75, 3.50, 4.25, 5.25, 6.25, 7.75, 9.25]
        + [10.75] * 4
        + [12.75] * 6
        + [13.75] * 14
        + [13.25, 12.75, 12.25, 11.75, 11.25, 10.75]
        + [10.50] * 8
        + [11.25, 12.25, 13.25, 14.25]
        + [14.75] * 10
    )
    if len(path) < len(idx):  # pragma: no cover - guards the literal above
        raise ValueError(f"rate path has {len(path)} steps, need {len(idx)}")

    return pd.DataFrame({"Selic": path[: len(idx)]}, index=idx)


def usd_brl() -> pd.DataFrame:
    """Exchange rate, as a random walk anchored to a plausible range."""
    idx = monthly_index()
    rng = np.random.default_rng(_SEED + 1)

    steps = rng.normal(0.004, 0.032, len(idx))
    walk = np.cumsum(steps)
    # Pull the walk back towards its start instead of clipping it: a hard
    # bound flattens the series against the limit, which no exchange rate does.
    series = 5.20 * np.exp(walk - 0.35 * np.linspace(0, 1, len(idx)) * walk)

    return pd.DataFrame({"USD/BRL": series.round(4)}, index=idx)


def gdp_quarterly() -> pd.DataFrame:
    """Quarterly GDP change in percent, quarter over quarter."""
    idx = pd.date_range(end="2025-12-31", periods=20, freq="QE")
    rng = np.random.default_rng(_SEED + 2)

    values = rng.normal(0.55, 0.72, len(idx))
    return pd.DataFrame({"PIB": values.round(2)}, index=idx)
