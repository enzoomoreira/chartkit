from __future__ import annotations

import pytest

from chartkit.metrics.registry import MetricRegistry


@pytest.fixture(autouse=True)
def _preserve_registry():
    """Snapshot and restore MetricRegistry around each test."""
    snapshot = dict(MetricRegistry._metrics)
    yield
    MetricRegistry._metrics = snapshot
