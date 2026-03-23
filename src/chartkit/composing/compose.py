"""Chart composition pipeline for multi-layer charts with dual-axis support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger

from .._internal import (
    FORMATTERS,
    apply_legend,
    create_figure,
    draw_composed_debug_overlay,
    extract_plot_data,
    finalize_chart,
    normalize_highlight,
    register_artist_obstacle,
    resolve_composed_collisions,
    save_figure,
    validate_plot_params,
)
from .._internal.plot_validation import AxisLimits
from ..charts import ChartRenderer
from ..charts._classification import get_kind_caps, resolve_kind_alias
from ..exceptions import ValidationError
from ..metrics import MetricRegistry
from ..result import PlotResult
from .layer import AxisSide, Layer

if TYPE_CHECKING:
    from .._internal.plot_validation import UnitFormat

__all__ = ["compose"]


class _ComposePlotter:
    """Minimal plotter that satisfies the Saveable protocol for composed charts."""

    def __init__(self, fig: plt.Figure) -> None:
        self._fig = fig

    def save(self, path: str, dpi: int | None = None) -> None:
        save_figure(self._fig, path, dpi)


def _validate_layers(
    layers: tuple[Layer, ...],
    legend: bool | None,
    tick_freq: str | None = None,
) -> None:
    validate_plot_params(units=None, legend=legend, tick_freq=tick_freq)

    if not layers:
        raise ValidationError("compose() requires at least one layer.")

    if all(layer.axis == "right" for layer in layers):
        raise ValidationError(
            "All layers are on axis='right'. At least one layer must use axis='left'."
        )

    # Validate composability of each layer kind
    for layer in layers:
        resolved = resolve_kind_alias(layer.kind)
        caps = get_kind_caps(resolved)
        if caps is not None and not caps.composable:
            raise ValidationError(
                f"Chart kind '{layer.kind}' cannot be used in compose(). "
                f"It has incompatible axis semantics for multi-layer charts."
            )


def _apply_axis_formatter(
    ax: plt.Axes,
    side: AxisSide,
    units: UnitFormat | None,
    applied: dict[AxisSide, UnitFormat | None],
) -> None:
    if units is None:
        return
    if applied[side] is not None:
        if applied[side] != units:
            logger.warning(
                "Conflicting units on {} axis: '{}' vs '{}'. Keeping '{}'.",
                side,
                applied[side],
                units,
                applied[side],
            )
        return
    ax.yaxis.set_major_formatter(FORMATTERS[units]())
    applied[side] = units


def _render_layer(
    ax: plt.Axes,
    layer: Layer,
    x_data: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
) -> None:
    highlight_modes = normalize_highlight(layer.highlight)
    ChartRenderer.render(
        ax, layer.kind, x_data, y_data, highlight=highlight_modes, **layer.kwargs
    )

    if layer.metrics:
        MetricRegistry.apply(ax, x_data, y_data, layer.metrics)


def compose(
    *layers: Layer,
    title: str | None = None,
    source: str | None = None,
    legend: bool | None = None,
    figsize: tuple[float, float] | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    xlim: AxisLimits | None = None,
    ylim: AxisLimits | None = None,
    grid: bool | None = None,
    tick_rotation: int | Literal["auto"] | None = None,
    tick_format: str | None = None,
    tick_freq: str | None = None,
    collision: bool = True,
    debug: bool = False,
) -> PlotResult:
    """Compose multiple layers into a single chart with optional dual axes.

    Args:
        *layers: One or more ``Layer`` objects created via ``df.chartkit.layer()``.
        title: Chart title.
        source: Data source for the footer.
        legend: Legend control. ``None`` = auto, ``True`` = force, ``False`` = suppress.
        figsize: Override figure size ``(width, height)`` in inches.
        xlabel: X-axis label.
        ylabel: Y-axis label (applied to the left axis).
        xlim: X-axis limits as ``(min, max)``. Accepts strings
            (``"2024-01-01"``), datetime, pd.Timestamp, or numeric.
        ylim: Y-axis limits as ``(min, max)`` (applied to the left axis).
            Accepts strings (``"100"``), numeric, datetime, or pd.Timestamp.
        grid: Grid override. ``None`` uses config, ``True``/``False``
            enables/disables grid for this chart.
        tick_rotation: X-axis tick label rotation. ``"auto"`` detects
            overlap; ``int`` forces a fixed angle. ``None`` uses config.
        tick_format: Date format string for X-axis ticks (e.g. ``"%b/%Y"``).
        tick_freq: Tick frequency (``"day"``, ``"week"``, ``"month"``,
            ``"quarter"``, ``"semester"``, ``"year"``).
        collision: Enable collision resolution engine. ``False`` skips
            all label collision processing.
        debug: Show collision debug overlay.

    Raises:
        ValidationError: No layers provided or all layers on right axis.
    """
    _validate_layers(layers, legend, tick_freq=tick_freq)

    logger.debug("compose: {} layer(s), title={}", len(layers), title)

    # 1. Style + figure
    fig, ax_left = create_figure(figsize=figsize, grid=grid)

    # 2. Right axis (if needed)
    ax_right: plt.Axes | None = None
    if any(layer.axis == "right" for layer in layers):
        ax_right = ax_left.twinx()
        ax_right.spines["right"].set_visible(True)

    # 3. Apply formatters and render layers
    applied_units: dict[AxisSide, UnitFormat | None] = {"left": None, "right": None}
    axes_map: dict[AxisSide, plt.Axes] = {"left": ax_left}
    if ax_right is not None:
        axes_map["right"] = ax_right

    first_x_data: pd.Index | pd.Series | None = None
    for layer in layers:
        ax = axes_map[layer.axis]
        _apply_axis_formatter(ax, layer.axis, layer.units, applied_units)

        x_data, y_data = extract_plot_data(layer.df, layer.x, layer.y)
        if first_x_data is None:
            first_x_data = x_data
        logger.debug(
            "Rendering layer: kind={}, axis={}, shape={}",
            layer.kind,
            layer.axis,
            layer.df.shape,
        )
        _render_layer(ax, layer, x_data, y_data)

    # 4. Legend (consolidated from both axes)
    apply_legend(ax_left, ax_right, legend=legend)

    # 5. Collision resolution (unified cross-axis)
    all_axes: list[plt.Axes] = [ax_left]
    if ax_right is not None:
        all_axes.append(ax_right)

    if collision:
        legend_artist = ax_left.get_legend()
        if legend_artist is not None:
            register_artist_obstacle(ax_left, legend_artist, filled=True)
        resolve_composed_collisions(all_axes)

    # 6. Finalize (ticks, axis limits, labels, decorations)
    finalize_chart(
        fig,
        ax_left,
        tick_format=tick_format,
        tick_freq=tick_freq,
        tick_rotation=tick_rotation,
        x_data=first_x_data,
        xlim=xlim,
        ylim=ylim,
        xlabel=xlabel,
        ylabel=ylabel,
        title=title,
        source=source,
    )

    # 7. Debug overlay (after finalize so geometry is final)
    if debug:
        draw_composed_debug_overlay(all_axes)

    return PlotResult(fig=fig, ax=ax_left, plotter=_ComposePlotter(fig))
