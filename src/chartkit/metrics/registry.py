from __future__ import annotations

import inspect
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Callable, NamedTuple

import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from ..exceptions import RegistryError, ValidationError


@dataclass
class MetricSpec:
    """Parsed metric specification.

    String syntax: ``name:param1:param2@column|label``
    """

    name: str
    params: dict[str, Any] = field(default_factory=dict)
    series: str | None = None
    label: str | None = None


class _MetricEntry(NamedTuple):
    func: Callable
    param_names: list[str]
    required_params: list[str]
    uses_series: bool


class MetricRegistry:
    """Central metrics registry with string spec parsing and batch application."""

    _metrics: dict[str, _MetricEntry] = {}

    @classmethod
    def register(
        cls,
        name: str,
        param_names: list[str] | None = None,
        uses_series: bool = True,
    ) -> Callable[[Callable], Callable]:
        """Decorator to register a metric.

        Args:
            name: Metric name (used in the string spec).
            param_names: Names of positional parameters extracted from the string.
                E.g.: ``['window']`` makes ``'ma:12'`` become ``{'window': 12}``.
            uses_series: Whether the metric uses the ``series`` parameter to
                select a column in multi-series DataFrames.
        """
        names = param_names or []

        def decorator(func: Callable) -> Callable:
            sig = inspect.signature(func)
            required = [
                p
                for p in names
                if p in sig.parameters
                and sig.parameters[p].default is inspect.Parameter.empty
            ]
            cls._metrics[name] = _MetricEntry(func, names, required, uses_series)
            return func

        return decorator

    @classmethod
    def parse(cls, spec: str | MetricSpec) -> MetricSpec:
        """Convert string spec into MetricSpec.

        Formats: ``'ath'``, ``'ma:12'``, ``'band:1.5:4.5'``, ``'ath@revenue'``,
        ``'ath|Maximum'``, ``'ma:12@revenue|12M Average'``.
        ``|`` separates custom label; ``@`` selects column; ``:`` separates params.

        Raises:
            RegistryError: Metric not registered.
            ValidationError: Required params missing or empty series after ``@``.
        """
        if isinstance(spec, MetricSpec):
            return spec

        label: str | None = None
        if "|" in spec:
            spec, label = spec.split("|", 1)
            label = label.strip() or None

        series: str | None = None
        if "@" in spec:
            metric_part, series = spec.rsplit("@", 1)
            if not series:
                raise ValidationError(
                    f"Empty series in '{spec}'. Use 'metric@column' or "
                    f"MetricSpec(name, series=column) for columns with '@'."
                )
        else:
            metric_part = spec

        parts = metric_part.split(":")
        name = parts[0]

        if name not in cls._metrics:
            available = ", ".join(sorted(cls._metrics.keys()))
            raise RegistryError(f"Unknown metric: '{name}'. Available: {available}")

        entry = cls._metrics[name]
        params: dict[str, Any] = {}

        raw_params = parts[1:]
        extra = raw_params[len(entry.param_names) :]
        if extra:
            logger.warning("Extra parameters ignored in '{}': {}", spec, extra)

        for i, value in enumerate(raw_params):
            if i < len(entry.param_names):
                try:
                    parsed_value: Any = float(value)
                    if parsed_value.is_integer():
                        parsed_value = int(parsed_value)
                    params[entry.param_names[i]] = parsed_value
                except ValueError:
                    params[entry.param_names[i]] = value

        missing = [p for p in entry.required_params if p not in params]
        if missing:
            raise ValidationError(
                f"Metric '{name}' requires parameter(s): {', '.join(missing)}. "
                f"Use '{name}:{':'.join('<' + p + '>' for p in entry.param_names)}'."
            )

        return MetricSpec(name, params, series, label)

    @classmethod
    def apply(
        cls,
        ax: Axes,
        x_data: pd.Index | pd.Series,
        y_data: pd.Series | pd.DataFrame,
        specs: Sequence[str | MetricSpec],
    ) -> None:
        """Apply list of metrics to the chart."""
        for spec in specs:
            parsed = cls.parse(spec)
            entry = cls._metrics[parsed.name]
            kwargs = parsed.params.copy()
            if parsed.series is not None and entry.uses_series:
                kwargs["series"] = parsed.series
            if parsed.label is not None:
                kwargs["label"] = parsed.label
            entry.func(ax, x_data, y_data, **kwargs)

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._metrics.keys())

    @classmethod
    def clear(cls) -> None:
        """Remove all registered metrics."""
        cls._metrics.clear()
