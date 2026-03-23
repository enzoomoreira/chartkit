"""Chart kind classification for feature compatibility."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

__all__ = [
    "KIND_ALIASES",
    "KindCaps",
    "get_kind_caps",
    "resolve_kind_alias",
    "validate_highlight_for_kind",
    "validate_metrics_for_kind",
]

AxisGroup = Literal["series", "distribution", "aggregation", "isolated", "event"]

# Single source of truth for chart kind aliases.
# ChartRenderer._ALIASES references this dict.
KIND_ALIASES: dict[str, str] = {"line": "plot", "area": "fill_between"}


@dataclass(frozen=True)
class KindCaps:
    """Feature capabilities for a chart kind.

    Attributes:
        group: Axis-semantics group this kind belongs to.
        highlight: Whether highlight markers are supported.
        temporal_metrics: Whether time-series metrics (ma, std_band, vband) work.
        all_metrics: Whether any metrics are supported at all.
        composable: Whether the kind can participate in ``compose()``.
    """

    group: AxisGroup
    highlight: bool
    temporal_metrics: bool
    all_metrics: bool
    composable: bool


# fmt: off
_CAPS: dict[str, KindCaps] = {
    # -- series (time-series / sequential) --
    "plot":         KindCaps("series", highlight=True,  temporal_metrics=True,  all_metrics=True,  composable=True),
    "scatter":      KindCaps("series", highlight=True,  temporal_metrics=True,  all_metrics=True,  composable=True),
    "step":         KindCaps("series", highlight=True,  temporal_metrics=True,  all_metrics=True,  composable=True),
    "bar":          KindCaps("series", highlight=True,  temporal_metrics=True,  all_metrics=True,  composable=True),
    "barh":         KindCaps("series", highlight=True,  temporal_metrics=True,  all_metrics=True,  composable=True),
    "stacked_bar":  KindCaps("series", highlight=True,  temporal_metrics=True,  all_metrics=True,  composable=True),
    "fill_between": KindCaps("series", highlight=True,  temporal_metrics=True,  all_metrics=True,  composable=True),
    "stackplot":    KindCaps("series", highlight=False, temporal_metrics=True,  all_metrics=True,  composable=True),
    "stairs":       KindCaps("series", highlight=True,  temporal_metrics=True,  all_metrics=True,  composable=True),
    "stem":         KindCaps("series", highlight=True,  temporal_metrics=True,  all_metrics=True,  composable=True),
    # -- distribution --
    "boxplot":      KindCaps("distribution", highlight=False, temporal_metrics=False, all_metrics=False, composable=False),
    "violinplot":   KindCaps("distribution", highlight=False, temporal_metrics=False, all_metrics=False, composable=False),
    # -- aggregation --
    "hist":         KindCaps("aggregation", highlight=False, temporal_metrics=False, all_metrics=False, composable=False),
    "ecdf":         KindCaps("aggregation", highlight=False, temporal_metrics=False, all_metrics=False, composable=False),
    # -- isolated --
    "pie":          KindCaps("isolated", highlight=False, temporal_metrics=False, all_metrics=False, composable=False),
    # -- event --
    "eventplot":    KindCaps("event", highlight=False, temporal_metrics=False, all_metrics=False, composable=False),
}
# fmt: on

# Metrics that require sequential / temporal x-axis data.
_TEMPORAL_METRICS: frozenset[str] = frozenset({"ma", "std_band", "vband"})


def resolve_kind_alias(kind: str) -> str:
    """Resolve a user-facing kind name to its canonical form."""
    return KIND_ALIASES.get(kind, kind)


def get_kind_caps(kind: str) -> KindCaps | None:
    """Return capabilities for a known kind, or ``None`` for unclassified generic kinds."""
    return _CAPS.get(kind)


def validate_highlight_for_kind(kind: str, resolved: str | None = None) -> None:
    """Raise ``ValidationError`` if *kind* does not support highlight.

    Args:
        kind: User-facing kind name (used in error messages).
        resolved: Pre-resolved canonical kind.  Computed from *kind* when omitted.
    """
    from ..exceptions import ValidationError

    if resolved is None:
        resolved = resolve_kind_alias(kind)
    caps = get_kind_caps(resolved)
    if caps is not None and not caps.highlight:
        raise ValidationError(f"Chart kind '{kind}' does not support highlight.")


def _extract_metric_name(spec: str | object) -> str:
    """Extract the metric name from a spec without importing MetricRegistry.

    Handles string syntax ``name:param1:param2@column|label`` and
    ``MetricSpec`` objects (which expose a ``.name`` attribute).
    """
    if hasattr(spec, "name"):
        return spec.name
    s = str(spec)
    if "|" in s:
        s = s.split("|", 1)[0]
    if "@" in s:
        s = s.rsplit("@", 1)[0]
    return s.split(":")[0]


def validate_metrics_for_kind(
    kind: str,
    specs: str | Sequence[str | object],
    resolved: str | None = None,
) -> None:
    """Raise ``ValidationError`` if any metric is incompatible with *kind*.

    Validates **capabilities** only (does this kind support metrics?).
    Metric existence is validated later by ``MetricRegistry.apply()``.

    Rules:
    - Unclassified generic kinds: allow all (backwards compat).
    - ``all_metrics=False``: block ALL metrics.
    - ``temporal_metrics=False``: block temporal metrics (ma, std_band, vband).

    Args:
        kind: User-facing kind name (used in error messages).
        specs: Metric spec strings or ``MetricSpec`` objects.
        resolved: Pre-resolved canonical kind.  Computed from *kind* when omitted.
    """
    from ..exceptions import ValidationError

    if resolved is None:
        resolved = resolve_kind_alias(kind)
    caps = get_kind_caps(resolved)
    if caps is None:
        return  # unclassified generic kind -- allow all

    if isinstance(specs, str):
        specs = [specs]

    for spec in specs:
        name = _extract_metric_name(spec)

        if not caps.all_metrics:
            raise ValidationError(
                f"Chart kind '{kind}' does not support metrics. Got metric '{name}'."
            )

        if not caps.temporal_metrics and name in _TEMPORAL_METRICS:
            raise ValidationError(
                f"Metric '{name}' requires sequential/temporal data, "
                f"which is not available for chart kind '{kind}'."
            )
