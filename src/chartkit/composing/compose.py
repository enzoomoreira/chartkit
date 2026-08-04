"""Chart composition pipeline for multi-layer charts with dual-axis support."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .._internal import (
    apply_legend,
    create_figure,
    draw_composed_debug_overlay,
    extract_plot_data,
    finalize_chart,
    get_formatter,
    normalize_highlight,
    register_artist_obstacle,
    resolve_composed_collisions,
    save_figure,
    validate_plot_params,
)
from .._internal.collision import clear_axes_state
from .._internal.plot_validation import AxisLimits, TickFreq
from ..charts import ChartRenderer
from ..charts._classification import get_kind_caps, resolve_kind_alias
from ..exceptions import ValidationError
from ..metrics import MetricRegistry
from ..result import PlotResult
from ..styling.theme import theme
from ..warnings import RenderingWarning, warn
from .layer import AxisSide, Layer

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .._internal.plot_validation import UnitFormat

__all__ = ["compose"]


class _ComposePlotter:
    """Minimal plotter that satisfies the Saveable protocol for composed charts."""

    def __init__(self, fig: Figure) -> None:
        self._fig = fig

    def save(self, path: str, dpi: int | None = None) -> None:
        save_figure(self._fig, path, dpi)


def _validate_layers(
    layers: tuple[Layer, ...],
    legend: bool | None,
    tick_freq: TickFreq | None = None,
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
    ax: Axes,
    side: AxisSide,
    units: UnitFormat | None,
    decimals: int | None,
    applied: dict[AxisSide, tuple[UnitFormat, int | None] | None],
) -> None:
    if units is None:
        return
    current = applied[side]
    if current is not None:
        if current != (units, decimals):
            warn(
                f"Conflicting units on {side} axis: '{current[0]}' vs "
                f"'{units}'. Keeping '{current[0]}'.",
                RenderingWarning,
            )
        return
    ax.yaxis.set_major_formatter(get_formatter(units, decimals))
    applied[side] = (units, decimals)


def _render_layer(
    ax: Axes,
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
    tick_freq: TickFreq | None = None,
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

    Note:
        Tick locating and formatting are driven by the **first** layer's X data
        alone. Layers sharing an axis are expected to span a comparable range;
        when they do not, matplotlib still autoscales the axis to fit them all,
        but the tick spacing is chosen for the first layer.
    """
    _validate_layers(layers, legend, tick_freq=tick_freq)

    logger.debug("compose: %s layer(s), title=%s", len(layers), title)

    # The whole chart is built inside the theme context: matplotlib reads
    # rcParams as each artist is created, not at save time.
    with theme.context():
        # 1. Figure
        fig, ax_left = create_figure(figsize=figsize, grid=grid)

        # 2. Right axis (if needed)
        ax_right: Axes | None = None
        if any(layer.axis == "right" for layer in layers):
            ax_right = ax_left.twinx()
            ax_right.spines["right"].set_visible(True)

        all_axes: list[Axes] = [ax_left]
        if ax_right is not None:
            all_axes.append(ax_right)

        try:
            # 3. Apply formatters and render layers
            applied_units: dict[AxisSide, tuple[UnitFormat, int | None] | None] = {
                "left": None,
                "right": None,
            }
            axes_map: dict[AxisSide, Axes] = {"left": ax_left}
            if ax_right is not None:
                axes_map["right"] = ax_right

            first_x_data: pd.Index | pd.Series | None = None
            for layer in layers:
                ax = axes_map[layer.axis]
                _apply_axis_formatter(
                    ax, layer.axis, layer.units, layer.decimals, applied_units
                )

                x_data, y_data = extract_plot_data(layer.df, layer.x, layer.y)
                if first_x_data is None:
                    first_x_data = x_data
                logger.debug(
                    "Rendering layer: kind=%s, axis=%s, shape=%s",
                    layer.kind,
                    layer.axis,
                    layer.df.shape,
                )
                _render_layer(ax, layer, x_data, y_data)

            # 4. Legend (consolidated from both axes)
            apply_legend(ax_left, ax_right, legend=legend)

            # 5. Collision resolution (unified cross-axis)
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
        finally:
            # Collision bookkeeping only matters while this chart is being
            # built; holding it would keep the Axes alive indefinitely.
            for axes in all_axes:
                clear_axes_state(axes)

    return PlotResult(fig=fig, ax=ax_left, plotter=_ComposePlotter(fig))
