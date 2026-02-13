"""Main plotting engine."""

from __future__ import annotations

from typing import Literal

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from ._internal import (
    FORMATTERS,
    extract_plot_data,
    normalize_highlight,
    register_fixed,
    resolve_collisions,
    save_figure,
    should_show_legend,
    validate_plot_params,
)
from ._internal.plot_validation import UnitFormat
from .charts import ChartRegistry
from .decorations import add_footer, add_title
from .exceptions import StateError
from .metrics import MetricRegistry
from .overlays import HighlightMode, add_fill_between
from .result import PlotResult
from .settings import get_config
from .styling import theme

ChartKind = Literal["line", "bar", "stacked_bar"]
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
        fill_between: tuple[str, str] | None = None,
        legend: bool | None = None,
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
            fill_between: Tuple ``(col1, col2)`` to shade the area between
                two DataFrame columns.
            legend: Legend control. ``None`` = auto (shows when there are
                2+ labeled artists), ``True`` = force, ``False`` = suppress.
            **kwargs: Chart-specific parameters (e.g.: ``y_origin='auto'`` for bars)
                and matplotlib parameters passed directly to the renderer.
        """
        highlight_modes = normalize_highlight(highlight)
        self._validate_params(units=units, legend=legend)
        config = get_config()

        logger.debug(
            "plot: kind={}, shape={}, units={}, metrics={}",
            kind,
            self.df.shape,
            units,
            metrics,
        )

        # 1. Style
        theme.apply()
        fig, ax = plt.subplots(figsize=config.layout.figsize)
        self._fig = fig
        self._ax = ax

        # 2. Data
        x_data, y_data = extract_plot_data(self.df, x, y)

        y_cols = (
            list(y_data.columns) if isinstance(y_data, pd.DataFrame) else [y_data.name]
        )
        logger.debug(
            "Data: x={}, y_columns={}, y_shape={}",
            "index" if x is None else x,
            y_cols,
            y_data.shape,
        )

        # 3. Y formatter
        if units:
            ax.yaxis.set_major_formatter(FORMATTERS[units]())

        # 4. Plot
        chart_fn = ChartRegistry.get(kind)
        logger.debug("Dispatch: kind='{}'", kind)
        chart_fn(ax, x_data, y_data, highlight=highlight_modes, **kwargs)

        # 5. Metrics
        if metrics:
            if isinstance(metrics, str):
                metrics = [metrics]
            logger.debug("Applying {} metric(s)", len(metrics))
            MetricRegistry.apply(ax, x_data, y_data, metrics)

        # 5b. Fill between
        if fill_between is not None:
            col1, col2 = fill_between
            add_fill_between(ax, x_data, self.df[col1], self.df[col2])

        # 6. Legend
        self._apply_legend(ax, legend)

        legend_artist = ax.get_legend()
        if legend_artist is not None:
            register_fixed(ax, legend_artist)

        # 7. Collision resolution
        resolve_collisions(ax, debug=debug)

        # 8. Decorations
        add_title(ax, title)
        add_footer(fig, source)

        return PlotResult(fig=self._fig, ax=ax, plotter=self)

    @staticmethod
    def _validate_params(units: UnitFormat | None, legend: bool | None) -> None:
        validate_plot_params(units=units, legend=legend)

    def _apply_legend(self, ax: Axes, legend: bool | None) -> None:
        _, labels = ax.get_legend_handles_labels()

        if not should_show_legend(labels, legend) or not labels:
            return

        config = get_config()
        ax.legend(
            loc=config.legend.loc,
            frameon=config.legend.frameon,
            framealpha=config.legend.alpha,
        )

    def save(self, path: str, dpi: int | None = None) -> None:
        """Save chart to file.

        Raises:
            StateError: If no chart has been generated yet.
        """
        if self._fig is None:
            raise StateError("No chart generated yet. Call plot() first.")
        save_figure(self._fig, path, dpi)
