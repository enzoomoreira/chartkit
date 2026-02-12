"""Main plotting engine."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast, get_args

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger
from pydantic import BaseModel, StrictBool
from pydantic import ValidationError as PydanticValidationError

from ._internal import resolve_collisions
from .charts import ChartRegistry
from .decorations import add_footer
from .exceptions import StateError, ValidationError
from .metrics import MetricRegistry
from .overlays import HighlightMode, add_fill_between
from .result import PlotResult
from .settings import get_charts_path, get_config
from .styling import (
    compact_currency_formatter,
    currency_formatter,
    human_readable_formatter,
    percent_formatter,
    points_formatter,
    theme,
)

ChartKind = Literal["line", "bar", "stacked_bar"]
UnitFormat = Literal["BRL", "USD", "BRL_compact", "USD_compact", "%", "human", "points"]
HighlightInput = bool | HighlightMode | list[HighlightMode]

_FORMATTERS = {
    "BRL": lambda: currency_formatter("BRL"),
    "USD": lambda: currency_formatter("USD"),
    "BRL_compact": lambda: compact_currency_formatter("BRL"),
    "USD_compact": lambda: compact_currency_formatter("USD"),
    "%": percent_formatter,
    "human": human_readable_formatter,
    "points": points_formatter,
}

_VALID_HIGHLIGHT_MODES: set[str] = set(get_args(HighlightMode))


def _normalize_highlight(highlight: HighlightInput) -> list[HighlightMode]:
    if highlight is True:
        return ["last"]
    if highlight is False:
        return []
    if isinstance(highlight, str):
        if highlight not in _VALID_HIGHLIGHT_MODES:
            available = ", ".join(sorted(_VALID_HIGHLIGHT_MODES))
            raise ValidationError(
                f"Highlight mode '{highlight}' invalid. Available: {available}"
            )
        return [cast(HighlightMode, highlight)]
    modes: list[HighlightMode] = []
    for m in highlight:
        if m not in _VALID_HIGHLIGHT_MODES:
            available = ", ".join(sorted(_VALID_HIGHLIGHT_MODES))
            raise ValidationError(
                f"Highlight mode '{m}' invalid. Available: {available}"
            )
        modes.append(cast(HighlightMode, m))
    return modes


class _PlotParams(BaseModel):
    units: UnitFormat | None = None
    legend: StrictBool | None = None


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
        highlight_modes = _normalize_highlight(highlight)
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
        x_data: pd.Index | pd.Series = (
            self.df.index if x is None else cast(pd.Series, self.df[x])
        )

        if y is None:
            y_data = self.df.select_dtypes(include=["number"])
        else:
            y_data = self.df[y]

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
        self._apply_y_formatter(ax, units)

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

        # 7. Collision resolution
        resolve_collisions(ax)

        # 8. Decorations
        self._apply_title(ax, title)
        self._apply_decorations(fig, source)

        return PlotResult(fig=self._fig, ax=ax, plotter=self)

    @staticmethod
    def _validate_params(units: UnitFormat | None, legend: bool | None) -> None:
        try:
            _PlotParams(units=units, legend=legend)
        except PydanticValidationError as exc:
            errors = exc.errors()
            msgs = [
                f"  {e['loc'][0]}: {e['msg']}" if e.get("loc") else f"  {e['msg']}"
                for e in errors
            ]
            raise ValidationError(
                "Invalid plot parameters:\n" + "\n".join(msgs)
            ) from exc

    def _apply_y_formatter(self, ax, units: UnitFormat | None) -> None:
        if units:
            ax.yaxis.set_major_formatter(_FORMATTERS[units]())

    def _apply_title(self, ax, title: str | None) -> None:
        if title:
            config = get_config()
            ax.set_title(
                title,
                loc="center",
                pad=config.layout.title.padding,
                fontproperties=theme.font,
                size=config.fonts.sizes.title,
                color=theme.colors.text,
                weight=config.layout.title.weight,
            )

    def _apply_legend(self, ax, legend: bool | None) -> None:
        _, labels = ax.get_legend_handles_labels()

        if legend is None:
            show = len(labels) > 1
        else:
            show = legend

        if show and labels:
            config = get_config()
            ax.legend(
                loc=config.legend.loc,
                frameon=config.legend.frameon,
                framealpha=config.legend.alpha,
            )

    def _apply_decorations(self, fig, source: str | None) -> None:
        add_footer(fig, source)

    def save(self, path: str, dpi: int | None = None) -> None:
        """Save chart to file.

        Raises:
            StateError: If no chart has been generated yet.
        """
        if self._fig is None:
            raise StateError("No chart generated yet. Call plot() first.")

        config = get_config()

        if dpi is None:
            dpi = config.layout.dpi

        path_obj = Path(path)
        if not path_obj.is_absolute():
            charts_path = get_charts_path()
            charts_path.mkdir(parents=True, exist_ok=True)
            path_obj = charts_path / path_obj

        logger.info("Saving: {} (dpi={})", path_obj, dpi)
        self._fig.savefig(path_obj, bbox_inches="tight", dpi=dpi)
