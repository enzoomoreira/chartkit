"""Chart composition pipeline for multi-layer charts with dual-axis support."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger

from .._internal import (
    FORMATTERS,
    extract_plot_data,
    normalize_highlight,
    register_fixed,
    resolve_composed_collisions,
    save_figure,
    should_show_legend,
    validate_plot_params,
)
from ..charts import ChartRegistry
from ..decorations import add_footer, add_title
from ..exceptions import ValidationError
from ..metrics import MetricRegistry
from ..overlays import add_fill_between
from ..result import PlotResult
from ..settings import get_config
from ..styling.theme import theme
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


def _validate_layers(layers: tuple[Layer, ...], legend: bool | None) -> None:
    validate_plot_params(units=None, legend=legend)

    if not layers:
        raise ValidationError("compose() requires at least one layer.")

    invalid_axes = {
        layer.axis for layer in layers if layer.axis not in {"left", "right"}
    }
    if invalid_axes:
        invalid = ", ".join(sorted(invalid_axes))
        raise ValidationError(
            f"Invalid axis value(s): {invalid}. Expected 'left' or 'right'."
        )

    if all(layer.axis == "right" for layer in layers):
        raise ValidationError(
            "All layers are on axis='right'. At least one layer must use axis='left'."
        )

    for layer in layers:
        validate_plot_params(units=layer.units, legend=None)


def _needs_right_axis(layers: tuple[Layer, ...]) -> bool:
    return any(layer.axis == "right" for layer in layers)


def _add_right_margin(
    ax_left: plt.Axes, ax_right: plt.Axes | None, fraction: float = 0.06
) -> None:
    """Expand X limits to give room for highlight labels at the right edge."""
    x0, x1 = ax_left.get_xlim()
    pad = (x1 - x0) * fraction
    ax_left.set_xlim(x0, x1 + pad)
    if ax_right is not None:
        ax_right.set_xlim(x0, x1 + pad)


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
    chart_fn = ChartRegistry.get(layer.kind)
    chart_fn(ax, x_data, y_data, highlight=highlight_modes, **layer.kwargs)

    if layer.metrics:
        metrics = [layer.metrics] if isinstance(layer.metrics, str) else layer.metrics
        MetricRegistry.apply(ax, x_data, y_data, metrics)

    if layer.fill_between is not None:
        col1, col2 = layer.fill_between
        add_fill_between(ax, x_data, layer.df[col1], layer.df[col2])


def _apply_composed_legend(
    ax_left: plt.Axes,
    ax_right: plt.Axes | None,
    legend: bool | None,
) -> None:
    handles, labels = ax_left.get_legend_handles_labels()
    if ax_right is not None:
        h_right, l_right = ax_right.get_legend_handles_labels()
        handles += h_right
        labels += l_right
        existing = ax_right.get_legend()
        if existing is not None:
            existing.remove()

    if not should_show_legend(labels, legend) or not labels:
        return

    config = get_config()
    ax_left.legend(
        handles,
        labels,
        loc=config.legend.loc,
        frameon=config.legend.frameon,
        framealpha=config.legend.alpha,
    )


def compose(
    *layers: Layer,
    title: str | None = None,
    source: str | None = None,
    legend: bool | None = None,
    figsize: tuple[float, float] | None = None,
) -> PlotResult:
    """Compose multiple layers into a single chart with optional dual axes.

    Args:
        *layers: One or more ``Layer`` objects created via ``df.chartkit.layer()``.
        title: Chart title.
        source: Data source for the footer.
        legend: Legend control. ``None`` = auto, ``True`` = force, ``False`` = suppress.
        figsize: Override figure size ``(width, height)`` in inches.

    Raises:
        ValidationError: No layers provided or all layers on right axis.
    """
    _validate_layers(layers, legend)

    config = get_config()
    logger.debug("compose: {} layer(s), title={}", len(layers), title)

    # 1. Style + figure
    theme.apply()
    effective_figsize = figsize or config.layout.figsize
    fig, ax_left = plt.subplots(figsize=effective_figsize)

    # 2. Right axis (if needed)
    ax_right: plt.Axes | None = None
    if _needs_right_axis(layers):
        ax_right = ax_left.twinx()
        ax_right.spines["right"].set_visible(True)

    # 3. Apply formatters and render layers
    applied_units: dict[AxisSide, UnitFormat | None] = {"left": None, "right": None}
    axes_map: dict[AxisSide, plt.Axes] = {"left": ax_left}
    if ax_right is not None:
        axes_map["right"] = ax_right

    for layer in layers:
        ax = axes_map[layer.axis]
        _apply_axis_formatter(ax, layer.axis, layer.units, applied_units)

        x_data, y_data = extract_plot_data(layer.df, layer.x, layer.y)
        logger.debug(
            "Rendering layer: kind={}, axis={}, shape={}",
            layer.kind,
            layer.axis,
            layer.df.shape,
        )
        _render_layer(ax, layer, x_data, y_data)

    # 4. Right margin for highlight labels
    has_highlights = any(layer.highlight for layer in layers)
    if has_highlights:
        _add_right_margin(ax_left, ax_right)

    # 5. Legend (consolidated from both axes)
    _apply_composed_legend(ax_left, ax_right, legend)

    legend_artist = ax_left.get_legend()
    if legend_artist is not None:
        register_fixed(ax_left, legend_artist)

    # 6. Collision resolution (unified cross-axis)
    all_axes: list[plt.Axes] = [ax_left]
    if ax_right is not None:
        all_axes.append(ax_right)
    resolve_composed_collisions(all_axes)

    # 7. Decorations
    add_title(ax_left, title)
    add_footer(fig, source)

    return PlotResult(fig=fig, ax=ax_left, plotter=_ComposePlotter(fig))
