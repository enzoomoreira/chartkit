"""Main plotting engine."""

from __future__ import annotations

from typing import Literal

import pandas as pd
from loguru import logger

from ._internal import (
    FORMATTERS,
    apply_legend,
    create_figure,
    draw_debug_overlay,
    extract_plot_data,
    finalize_chart,
    normalize_highlight,
    register_artist_obstacle,
    resolve_collisions,
    save_figure,
    validate_plot_params,
)
from ._internal.plot_validation import AxisLimits, UnitFormat
from .charts import ChartRenderer
from .charts._classification import (
    resolve_kind_alias,
    validate_highlight_for_kind,
    validate_metrics_for_kind,
)
from .exceptions import StateError
from .metrics import MetricRegistry
from .overlays import HighlightMode
from .result import PlotResult

ChartKind = str
HighlightInput = bool | HighlightMode | list[HighlightMode]


class ChartingPlotter:
    """Standardized financial visualization factory."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self._fig = None
        self._ax = None

    def plot(
        self,
        x: str | None = None,
        y: str | list[str] | None = None,
        *,
        kind: ChartKind = "line",
        title: str | None = None,
        units: UnitFormat | None = None,
        source: str | None = None,
        highlight: HighlightInput = False,
        metrics: str | list[str] | None = None,
        legend: bool | None = None,
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
        **kwargs,
    ) -> PlotResult:
        """Generate standardized chart.

        Args:
            x: Column for the X axis. ``None`` uses the DataFrame index.
            y: Column(s) for the Y axis. ``None`` uses all numeric columns.
            kind: Chart type.
            title: Title displayed above the chart.
            units: Y axis formatting.
            source: Data source displayed in the footer. Overrides
                ``branding.default_source`` from config when provided.
            highlight: Data point highlight mode(s). ``True`` or ``'last'``
                highlights the last point; ``'max'``/``'min'`` highlights
                maximum/minimum. Accepts a list to combine modes.
            metrics: Declarative metric(s). Use ``|`` for custom legend label
                (e.g.: ``'ath|Maximum'``, ``'ma:12@col|12M Average'``).
            legend: Legend control. ``None`` = auto (shows when there are
                2+ labeled artists), ``True`` = force, ``False`` = suppress.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            xlim: X-axis limits as ``(min, max)``. Accepts strings
                (``"2024-01-01"``), datetime, pd.Timestamp, or numeric.
            ylim: Y-axis limits as ``(min, max)``. Accepts strings
                (``"100"``), numeric, datetime, or pd.Timestamp.
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
            **kwargs: Chart-specific parameters (e.g.: ``y_origin='auto'`` for bars)
                and matplotlib parameters passed directly to the renderer.
        """
        highlight_modes = normalize_highlight(highlight)
        validate_plot_params(units=units, legend=legend, tick_freq=tick_freq)

        resolved_kind = resolve_kind_alias(kind)
        if highlight_modes:
            validate_highlight_for_kind(kind, resolved=resolved_kind)
        if metrics:
            validate_metrics_for_kind(kind, metrics, resolved=resolved_kind)

        logger.debug(
            "plot: kind={}, shape={}, units={}, metrics={}",
            kind,
            self.df.shape,
            units,
            metrics,
        )

        # 1. Style + figure
        fig, ax = create_figure(grid=grid)
        self._fig = fig
        self._ax = ax

        # 2. Data
        x_data, y_data = extract_plot_data(self.df, x, y)

        # 3. Y formatter
        if units:
            ax.yaxis.set_major_formatter(FORMATTERS[units]())

        # 4. Plot
        ChartRenderer.render(
            ax, kind, x_data, y_data, highlight=highlight_modes, **kwargs
        )

        # 5. Metrics
        if metrics:
            logger.debug("Applying metric(s)")
            MetricRegistry.apply(ax, x_data, y_data, metrics)

        # 6. Legend
        apply_legend(ax, legend=legend)

        # 7. Collision resolution
        if collision:
            legend_artist = ax.get_legend()
            if legend_artist is not None:
                register_artist_obstacle(ax, legend_artist, filled=True)
            resolve_collisions(ax)

        # 8. Finalize (ticks, axis limits, labels, decorations)
        finalize_chart(
            fig,
            ax,
            tick_format=tick_format,
            tick_freq=tick_freq,
            tick_rotation=tick_rotation,
            x_data=x_data,
            xlim=xlim,
            ylim=ylim,
            xlabel=xlabel,
            ylabel=ylabel,
            title=title,
            source=source,
        )

        # 9. Debug overlay (after finalize so geometry is final)
        if debug:
            draw_debug_overlay(ax)

        return PlotResult(fig=self._fig, ax=ax, plotter=self)

    def save(self, path: str, dpi: int | None = None) -> None:
        """Save chart to file.

        Raises:
            StateError: If no chart has been generated yet.
        """
        if self._fig is None:
            raise StateError("No chart generated yet. Call plot() first.")
        save_figure(self._fig, path, dpi)
