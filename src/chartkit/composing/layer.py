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
    """

    df: pd.DataFrame
    kind: ChartKind = "line"
    x: str | None = None
    y: str | list[str] | None = None
    units: UnitFormat | None = None
    highlight: HighlightInput = False
    metrics: str | list[str] | None = None
    fill_between: tuple[str, str] | None = None
    axis: AxisSide = "left"
    kwargs: dict[str, Any] = field(default_factory=dict)


def create_layer(
    df: pd.DataFrame,
    kind: ChartKind = "line",
    x: str | None = None,
    y: str | list[str] | None = None,
    *,
    units: UnitFormat | None = None,
    highlight: HighlightInput = False,
    metrics: str | list[str] | None = None,
    fill_between: tuple[str, str] | None = None,
    axis: AxisSide = "left",
    **kwargs: Any,
) -> Layer:
    """Create a Layer for use with ``compose()``.

    Same parameters as ``plot()`` but without chart-level options
    (title, source, legend). Those are passed to ``compose()`` instead.

    Raises:
        ValidationError: Invalid ``units``, ``highlight``, or ``axis``.
        RegistryError: Unknown ``kind``.
    """
    from .._internal import validate_plot_params
    from ..charts import ChartRegistry

    validate_plot_params(units=units, legend=None)
    ChartRegistry.get(kind)
    if axis not in ("left", "right"):
        from ..exceptions import ValidationError

        raise ValidationError(f"Invalid axis '{axis}'. Expected 'left' or 'right'.")

    return Layer(
        df=df,
        kind=kind,
        x=x,
        y=y,
        units=units,
        highlight=highlight,
        metrics=metrics,
        fill_between=fill_between,
        axis=axis,
        kwargs=kwargs,
    )
