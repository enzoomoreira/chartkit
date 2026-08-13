from __future__ import annotations

import inspect
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, ClassVar, NamedTuple

import pandas as pd
from matplotlib.axes import Axes

from .._internal.frequency import infer_freq
from ..exceptions import RegistryError, ValidationError
from ..warnings import RenderingWarning, warn

logger = logging.getLogger(__name__)


@dataclass
class MetricSpec:
    """Parsed metric specification.

    String syntax: ``name:param1:param2@column|label``

    Attributes:
        name: Metric name (e.g. ``'ath'``, ``'ma'``, ``'band'``).
        params: Parsed positional parameters (e.g. ``{'window': 12}``).
        series: Target column when using ``@`` syntax.
        label: Custom legend label when using ``|`` syntax.
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
    uses_freq: bool


class MetricRegistry:
    """Central metrics registry with string spec parsing and batch application."""

    _metrics: ClassVar[dict[str, _MetricEntry]] = {}
    _builtins: ClassVar[dict[str, _MetricEntry]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        param_names: list[str] | None = None,
        uses_series: bool = True,
        uses_freq: bool = False,
        replace: bool = False,
    ) -> Callable[[Callable], Callable]:
        """Decorator to register a metric.

        Args:
            name: Metric name (used in the string spec).
            param_names: Names of positional parameters extracted from the string.
                E.g.: ``['window']`` makes ``'ma:12'`` become ``{'window': 12}``.
            uses_series: Whether the metric uses the ``series`` parameter to
                select a column in multi-series DataFrames.
            uses_freq: Whether the metric receives ``detected_freq`` from
                automatic frequency detection.
            replace: Allow overwriting an existing metric of the same name.
                Without it a collision raises, so two libraries registering
                ``'ma'`` cannot silently shadow one another.

        Raises:
            RegistryError: If *name* is taken and *replace* is False.
        """
        names = param_names or []

        def decorator(func: Callable) -> Callable:
            if name in cls._metrics and not replace:
                existing = cls._metrics[name].func
                raise RegistryError(
                    f"Metric '{name}' is already registered by "
                    f"{getattr(existing, '__qualname__', existing)}. "
                    f"Pass replace=True to override it deliberately."
                )
            sig = inspect.signature(func)
            required = [
                p
                for p in names
                if p in sig.parameters
                and sig.parameters[p].default is inspect.Parameter.empty
            ]
            cls._metrics[name] = _MetricEntry(
                func, names, required, uses_series, uses_freq
            )
            return func

        return decorator

    @classmethod
    def unregister(cls, name: str) -> None:
        """Remove a single metric.

        Raises:
            RegistryError: If *name* is not registered.
        """
        if name not in cls._metrics:
            raise RegistryError(
                f"Metric '{name}' is not registered. Available: {cls.available()}."
            )
        del cls._metrics[name]

    @classmethod
    def snapshot_builtins(cls) -> None:
        """Record the current registry as the built-in set.

        Called once after the built-in metrics register, so
        ``reset_to_builtins()`` has something to restore to.
        """
        cls._builtins = dict(cls._metrics)

    @classmethod
    def reset_to_builtins(cls) -> None:
        """Drop every user-registered metric, keeping the built-in set.

        This is what a test or a notebook wants between runs; clearing the
        registry outright would leave ``'ath'`` and ``'ma'`` undefined.
        """
        cls._metrics = dict(cls._builtins)

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
            warn(
                f"Extra parameters ignored in '{spec}': {extra}",
                RenderingWarning,
            )

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
        specs: str | Sequence[str | MetricSpec],
    ) -> None:
        """Apply metric(s) to the chart.

        Args:
            ax: Target matplotlib Axes.
            x_data: X-axis values (index or column).
            y_data: Y-axis data (Series or DataFrame).
            specs: One or more metric specs as strings or ``MetricSpec``
                objects. Strings are parsed via ``parse()``.
        """
        if isinstance(specs, str):
            specs = [specs]

        parsed_specs = [cls.parse(s) for s in specs]

        detected_freq: str | None = None
        if any(cls._metrics[p.name].uses_freq for p in parsed_specs):
            detected_freq = infer_freq(x_data)

        for parsed in parsed_specs:
            entry = cls._metrics[parsed.name]
            kwargs = parsed.params.copy()
            if parsed.series is not None and entry.uses_series:
                kwargs["series"] = parsed.series
            if parsed.label is not None:
                kwargs["label"] = parsed.label
            if entry.uses_freq:
                kwargs["detected_freq"] = detected_freq
            entry.func(ax, x_data, y_data, **kwargs)

    @classmethod
    def available(cls) -> list[str]:
        """Return sorted list of registered metric names."""
        return sorted(cls._metrics.keys())
