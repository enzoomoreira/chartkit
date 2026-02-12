from __future__ import annotations

from datetime import datetime

import pandas as pd

from chartkit._internal.collision import _pos_to_numeric


def test_float_passthrough() -> None:
    x, y = _pos_to_numeric(1.0, 2.0)
    assert x == 1.0
    assert y == 2.0


def test_int_passthrough() -> None:
    x, y = _pos_to_numeric(1, 2)
    assert x == 1.0
    assert y == 2.0


def test_datetime_converted() -> None:
    dt = datetime(2023, 6, 15)
    x, y = _pos_to_numeric(dt, 5.0)
    assert isinstance(x, float)
    assert x > 0  # matplotlib date number
    assert y == 5.0


def test_timestamp_converted() -> None:
    ts = pd.Timestamp("2023-06-15")
    x, y = _pos_to_numeric(ts, 10.0)
    assert isinstance(x, float)
    assert x > 0
    assert y == 10.0
