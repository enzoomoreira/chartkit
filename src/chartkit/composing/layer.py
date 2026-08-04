"""Layer dataclass for chart composition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    import pandas as pd

    from ..engine import ChartKind, HighlightInput, UnitFormat

AxisSide = Literal["left", "right"]

__all__ = ["AxisSide", "Layer", "create_layer"]


@dataclass(frozen=True)
class Layer:
    """Immutable specification for a single layer in a composed chart.

    Captures the plotting intent (data + visual parameters) without rendering.
    Created via ``df.chartkit.layer()`` and consumed by ``compose()``.

    Attributes:
        df: Source DataFrame.
        x: Column for the X axis. ``None`` uses the DataFrame index.
        y: Column(s) for the Y axis. ``None`` uses all numeric columns.
        kind: Chart type (``'line'``, ``'bar'``, ``'area'``, etc.).
        units: Y-axis formatting (``'BRL'``, ``'USD'``, ``'%'``, etc.).
        decimals: Decimal places for this layer's axis tick labels.
        highlight: Data point highlight mode(s).
        metrics: Declarative metric(s).
        axis: Which Y axis to use (``'left'`` or ``'right'``).
        kwargs: Extra matplotlib parameters passed to the renderer.
    """

    df: pd.DataFrame
    x: str | None = None
    y: str | list[str] | None = None
    kind: ChartKind = "line"
    units: UnitFormat | None = None
    decimals: int | None = None
    highlight: HighlightInput = False
    metrics: str | list[str] | None = None
    axis: AxisSide = "left"
    kwargs: dict[str, Any] = field(default_factory=dict)


def create_layer(
    df: pd.DataFrame,
    x: str | None = None,
    y: str | list[str] | None = None,
    *,
    kind: ChartKind = "line",
    units: UnitFormat | None = None,
    decimals: int | None = None,
    highlight: HighlightInput = False,
    metrics: str | list[str] | None = None,
    axis: AxisSide = "left",
    **kwargs: Any,
) -> Layer:
    """Create a Layer for use with ``compose()``.

    Args:
        df: Source DataFrame.
        x: Column for the X axis. ``None`` uses the DataFrame index.
        y: Column(s) for the Y axis. ``None`` uses all numeric columns.
        kind: Chart type (``'line'``, ``'bar'``, ``'area'``, etc.).
        units: Y-axis formatting (``'BRL'``, ``'USD'``, ``'%'``, etc.).
        decimals: Decimal places for this layer's axis tick labels. Has no
            effect when *units* is ``None``.
        highlight: Data point highlight mode(s).
        metrics: Declarative metric(s).
        axis: Which Y axis to use (``'left'`` or ``'right'``).
        **kwargs: Extra matplotlib parameters passed to the renderer.

    Raises:
        ValidationError: Invalid ``units``, ``highlight``, ``axis``, or ``kind``.
    """
    from .._internal import normalize_highlight, validate_plot_params
    from ..charts import ChartRenderer
    from ..charts._classification import (
        resolve_kind_alias,
        validate_highlight_for_kind,
        validate_metrics_for_kind,
    )

    validate_plot_params(units=units, legend=None)
    ChartRenderer.validate_kind(kind)
    if axis not in ("left", "right"):
        from ..exceptions import ValidationError

        raise ValidationError(f"Invalid axis '{axis}'. Expected 'left' or 'right'.")

    # Normalizing here rejects unknown modes at construction; compose() would
    # otherwise only find out once it is halfway through rendering.
    highlight_modes = normalize_highlight(highlight)

    resolved = resolve_kind_alias(kind)
    if highlight_modes:
        validate_highlight_for_kind(kind, resolved=resolved)
    if metrics:
        validate_metrics_for_kind(kind, metrics, resolved=resolved)

    return Layer(
        df=df,
        x=x,
        y=y,
        kind=kind,
        units=units,
        decimals=decimals,
        highlight=highlight,
        metrics=metrics,
        axis=axis,
        kwargs=kwargs,
    )
