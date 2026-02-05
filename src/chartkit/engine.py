"""Motor de plotagem principal."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from ._internal import resolve_collisions
from .charts.bar import plot_bar
from .charts.line import plot_line
from .decorations import add_footer
from .metrics import MetricRegistry
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


_FORMATTERS = {
    "BRL": lambda: currency_formatter("BRL"),
    "USD": lambda: currency_formatter("USD"),
    "BRL_compact": lambda: compact_currency_formatter("BRL"),
    "USD_compact": lambda: compact_currency_formatter("USD"),
    "%": percent_formatter,
    "human": human_readable_formatter,
    "points": points_formatter,
}


class ChartingPlotter:
    """Factory de visualizacao financeira padronizada."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self._fig = None
        self._ax = None

    def plot(
        self,
        x: str | None = None,
        y: str | list[str] | None = None,
        kind: str = "line",
        title: str | None = None,
        units: str | None = None,
        source: str | None = None,
        highlight_last: bool = False,
        y_origin: str = "zero",
        save_path: str | None = None,
        metrics: str | list[str] | None = None,
        **kwargs,
    ) -> PlotResult:
        """Gera grafico padronizado.

        Args:
            units: Formatacao do eixo Y (``'BRL'``, ``'USD'``, ``'%'``,
                ``'human'``, ``'points'``, ``'BRL_compact'``, ``'USD_compact'``).
            metrics: Metrica(s) declarativas. Ver ``chartkit.metrics`` para
                sintaxe completa (ex: ``'ath'``, ``'ma:12'``, ``'band:1.5:4.5'``).
            y_origin: ``'zero'`` (default) ou ``'auto'`` (apenas para barras).
        """
        config = get_config()

        # 1. Style
        theme.apply()
        fig, ax = plt.subplots(figsize=config.layout.figsize)
        self._fig = fig
        self._ax = ax

        # 2. Data
        x_data = self.df.index if x is None else self.df[x]

        if y is None:
            y_data = self.df.select_dtypes(include=["number"])
        else:
            y_data = self.df[y]

        # 3. Y formatter
        self._apply_y_formatter(ax, units)

        # 4. Plot
        if kind == "line":
            plot_line(ax, x_data, y_data, highlight_last, **kwargs)
        elif kind == "bar":
            plot_bar(
                ax, x_data, y_data, highlight=highlight_last, y_origin=y_origin, **kwargs
            )
        else:
            raise ValueError(f"Chart type '{kind}' not supported.")

        # 5. Metrics
        if metrics:
            if isinstance(metrics, str):
                metrics = [metrics]
            MetricRegistry.apply(ax, x_data, y_data, metrics)

        # 6. Collision resolution
        resolve_collisions(ax)

        # 7. Decorations
        self._apply_title(ax, title)
        self._apply_decorations(fig, source)

        # 8. Output
        if save_path:
            self.save(save_path)

        return PlotResult(fig=self._fig, ax=ax, plotter=self)

    def _apply_y_formatter(self, ax, units: str | None) -> None:
        if units and units in _FORMATTERS:
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

    def _apply_decorations(self, fig, source: str | None) -> None:
        add_footer(fig, source)

    def save(self, path: str, dpi: int | None = None) -> None:
        """Salva o grafico em arquivo.

        Raises:
            RuntimeError: Se nenhum grafico foi gerado ainda.
        """
        if self._fig is None:
            raise RuntimeError("Nenhum grafico gerado. Chame plot() primeiro.")

        config = get_config()

        if dpi is None:
            dpi = config.layout.dpi

        path_obj = Path(path)
        if not path_obj.is_absolute():
            charts_path = get_charts_path()
            charts_path.mkdir(parents=True, exist_ok=True)
            path_obj = charts_path / path_obj

        self._fig.savefig(path_obj, bbox_inches="tight", dpi=dpi)
