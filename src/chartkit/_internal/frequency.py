"""Frequency detection and display utilities.

Shared by transforms and metrics for frequency-aware behavior.
"""

from __future__ import annotations

import pandas as pd
from loguru import logger

__all__ = [
    "FREQ_ALIASES",
    "FREQ_DISPLAY_MAP",
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
    if isinstance(data, pd.Index):
        index = data
    else:
        index = data.index

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
    logger.debug("Inferred frequency: '{}' (raw: '{}')", result, raw)
    return result


def freq_display_label(freq_code: str | None) -> str:
    """Convert frequency code to short display label.

    Returns empty string if freq_code is None or unknown.
    """
    if freq_code is None:
        return ""
    return FREQ_DISPLAY_MAP.get(freq_code, freq_code)
