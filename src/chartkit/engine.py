"""Motor de plotagem principal."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast, get_args

import matplotlib.pyplot as plt
import pandas as pd
from pydantic import BaseModel, StrictBool

from ._internal import resolve_collisions
from .charts import ChartRegistry
from .decorations import add_footer
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
            raise ValueError(
                f"Highlight mode '{highlight}' invalido. Disponiveis: {available}"
            )
        return [cast(HighlightMode, highlight)]
    modes: list[HighlightMode] = []
    for m in highlight:
        if m not in _VALID_HIGHLIGHT_MODES:
            available = ", ".join(sorted(_VALID_HIGHLIGHT_MODES))
            raise ValueError(f"Highlight mode '{m}' invalido. Disponiveis: {available}")
        modes.append(cast(HighlightMode, m))
    return modes


class _PlotParams(BaseModel):
    units: UnitFormat | None = None
    legend: StrictBool | None = None


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
        """Gera grafico padronizado.

        Args:
            x: Coluna para o eixo X. ``None`` usa o index do DataFrame.
            y: Coluna(s) para o eixo Y. ``None`` usa todas as numericas.
            kind: Tipo de grafico.
            title: Titulo exibido acima do grafico.
            units: Formatacao do eixo Y.
            source: Fonte dos dados exibida no rodape. Sobrescreve
                ``branding.default_source`` do config quando fornecido.
            highlight: Modo(s) de destaque de pontos. ``True`` ou ``'last'``
                destaca o ultimo ponto; ``'max'``/``'min'`` destaca
                maximo/minimo. Aceita lista para combinar modos.
            metrics: Metrica(s) declarativas. Use ``|`` para label customizado
                na legenda (ex: ``'ath|Maximo'``, ``'ma:12@col|Media 12M'``).
            fill_between: Tupla ``(col1, col2)`` para sombrear area entre
                duas colunas do DataFrame.
            legend: Controle da legenda. ``None`` = auto (mostra quando ha
                2+ artists rotulados), ``True`` = forca, ``False`` = suprime.
            **kwargs: Parametros chart-specific (ex: ``y_origin='auto'`` para barras)
                e parametros matplotlib passados diretamente ao renderer.
        """
        highlight_modes = _normalize_highlight(highlight)
        self._validate_params(units=units, legend=legend)
        config = get_config()

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

        # 3. Y formatter
        self._apply_y_formatter(ax, units)

        # 4. Plot
        chart_fn = ChartRegistry.get(kind)
        chart_fn(ax, x_data, y_data, highlight=highlight_modes, **kwargs)

        # 5. Metrics
        if metrics:
            if isinstance(metrics, str):
                metrics = [metrics]
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
        from pydantic import ValidationError

        try:
            _PlotParams(units=units, legend=legend)
        except ValidationError as exc:
            errors = exc.errors()
            msgs = [
                f"  {e['loc'][0]}: {e['msg']}" if e.get("loc") else f"  {e['msg']}"
                for e in errors
            ]
            raise ValueError(
                "Parametros de plot invalidos:\n" + "\n".join(msgs)
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
