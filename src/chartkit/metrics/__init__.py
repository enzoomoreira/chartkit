"""Declarative metrics system for charts.

Syntax: ``metrics=['ath', 'ma:12', 'band:1.5:4.5', 'ath@revenue']``

Use ``|`` for custom legend label: ``'ath|Maximum'``, ``'ma:12@col|12M Average'``.
Use ``@column`` to select target column in multi-series DataFrames.
"""

from .builtin import register_builtin_metrics
from .registry import MetricRegistry, MetricSpec

register_builtin_metrics()

__all__ = ["MetricRegistry", "MetricSpec"]
