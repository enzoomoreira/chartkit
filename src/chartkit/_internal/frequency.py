"""Frequency detection and display utilities.

Shared by transforms and metrics for frequency-aware behavior.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

__all__ = [
    "FREQ_ALIASES",
    "FREQ_DISPLAY_MAP",
    "estimate_freq",
    "freq_display_label",
    "infer_freq",
    "normalize_freq_code",
]

# Friendly aliases the user can pass in the freq= parameter
FREQ_ALIASES: dict[str, str] = {
    "D": "D",
    "daily": "D",
    "B": "B",
    "business": "B",
    "W": "W",
    "weekly": "W",
    "M": "ME",
    "monthly": "ME",
    "Q": "QE",
    "quarterly": "QE",
    "Y": "YE",
    "yearly": "YE",
    "annual": "YE",
    "BME": "BME",
    "BMS": "BMS",
}

# Prefixes of anchored freq codes that pd.infer_freq() may return.
# E.g.: "W-SUN" -> "W", "QE-DEC" -> "QE", "BYE-DEC" -> "BYE"
_ANCHORED_PREFIXES = (
    "W-",
    "QE-",
    "QS-",
    "BQE-",
    "BQS-",
    "YE-",
    "YS-",
    "BYE-",
    "BYS-",
)

# Short display labels for frequency codes (pt-BR friendly)
FREQ_DISPLAY_MAP: dict[str, str] = {
    "D": "D",
    "B": "DU",
    "W": "S",
    "ME": "M",
    "MS": "M",
    "BME": "M",
    "BMS": "M",
    "QE": "T",
    "QS": "T",
    "BQE": "T",
    "BQS": "T",
    "YE": "A",
    "YS": "A",
    "BYE": "A",
    "BYS": "A",
}


def normalize_freq_code(raw: str) -> str:
    """Normalize freq code to canonical form.

    Handles friendly aliases (``'M'`` -> ``'ME'``) and anchored freq codes
    (``'W-SUN'`` -> ``'W'``, ``'BQE-DEC'`` -> ``'BQE'``).
    """
    if raw in FREQ_ALIASES:
        return FREQ_ALIASES[raw]

    for prefix in _ANCHORED_PREFIXES:
        if raw.startswith(prefix):
            return prefix.rstrip("-")

    return raw


def infer_freq(data: pd.DataFrame | pd.Series | pd.Index) -> str | None:
    """Try to infer frequency via pandas.

    Accepts DataFrame, Series, or Index directly.
    Returns normalized freq code or None if unable to determine.
    """
    index = data if isinstance(data, pd.Index) else data.index

    if not isinstance(index, pd.DatetimeIndex):
        return None

    if len(index) < 3:
        return None

    try:
        raw = pd.infer_freq(index)
    except (TypeError, ValueError):
        return None

    if raw is None:
        return None

    result = normalize_freq_code(raw)
    logger.debug("Inferred frequency: '%s' (raw: '%s')", result, raw)
    return result


# Upper bound on the median spacing, in days, for each frequency. Daily and
# business-daily both sit at a one-day median, so they are told apart by
# whether the index ever lands on a weekend, not by spacing.
_SPACING_BOUNDS: tuple[tuple[float, str], ...] = (
    (1.05, "D"),
    (2.5, "B"),
    (10.0, "W"),
    (45.0, "ME"),
    (135.0, "QE"),
    (400.0, "YE"),
)


def estimate_freq(data: pd.DataFrame | pd.Series | pd.Index) -> str | None:
    """Estimate frequency from the median spacing between observations.

    ``pd.infer_freq`` needs a perfectly regular index, so it returns ``None``
    for any real market series: one public holiday is enough. This falls back
    to the typical gap, which still tells daily from monthly.

    Returns ``None`` when there is no datetime index or too few points.
    """
    index = data if isinstance(data, pd.Index) else data.index

    if not isinstance(index, pd.DatetimeIndex) or len(index) < 3:
        return None

    deltas = index.to_series().diff().dropna()
    if deltas.empty:
        return None

    median_days = float(deltas.median().total_seconds()) / 86400.0
    if median_days <= 0:
        return None

    for upper, code in _SPACING_BOUNDS:
        if median_days > upper:
            continue
        # 'D' and 'B' are 365 versus 252 periods a year -- a 45% difference, so
        # guessing is not good enough. A series that never lands on a weekend
        # is a trading calendar.
        if code == "D" and not (index.dayofweek >= 5).any():
            code = "B"
        logger.debug(
            "Estimated frequency '%s' from median spacing of %.2f day(s)",
            code,
            median_days,
        )
        return code
    return None


def freq_display_label(freq_code: str | None) -> str:
    """Convert frequency code to short display label.

    Returns empty string if freq_code is None or unknown.
    """
    if freq_code is None:
        return ""
    return FREQ_DISPLAY_MAP.get(freq_code, freq_code)
