from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

import numpy as np
import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from .._internal.collision import register_moveable
from ..exceptions import RegistryError
from ..settings import get_config
from ..styling.theme import theme

HighlightMode = Literal["last", "max", "min"]

__all__ = [
    "HighlightMode",
    "HighlightStyle",
    "HIGHLIGHT_STYLES",
    "add_highlight",
]


@dataclass(frozen=True)
class HighlightStyle:
    """Estrategia de posicionamento para highlight por chart type."""

    ha: str
    va: str | None  # None = auto-detect pelo sinal do valor
    label_prefix: str
    show_scatter: bool


HIGHLIGHT_STYLES: dict[str, HighlightStyle] = {
    "line": HighlightStyle(
        ha="left", va="center", label_prefix="  ", show_scatter=True
    ),
    "bar": HighlightStyle(ha="center", va=None, label_prefix="", show_scatter=False),
}


def _resolve_target(
    valid_series: pd.Series, mode: HighlightMode
) -> tuple[Any, float] | None:
    """Resolve o (indice, valor) alvo para um modo de highlight.

    Retorna ``None`` se o valor nao for finito.
    """
    if mode == "last":
        idx = valid_series.index[-1]
        val = valid_series.iloc[-1]
    elif mode == "max":
        idx = valid_series.idxmax()
        val = valid_series[idx]
    else:  # min
        idx = valid_series.idxmin()
        val = valid_series[idx]

    if not np.isfinite(val):
        logger.debug("Highlight mode '{}': target value is not finite, skipping", mode)
        return None
    return idx, float(val)


def _render_point(
    ax: Axes,
    idx: Any,
    val: float,
    x: pd.Index | pd.Series | None,
    ha: str,
    va: str,
    label_prefix: str,
    show_scatter: bool,
    color: str,
) -> None:
    """Renderiza scatter marker + text label para um ponto de highlight."""
    config = get_config()

    # Resolve posicao X
    if x is not None and hasattr(x, "get_loc"):
        try:
            loc_idx = x.get_loc(idx)
            x_val = x[loc_idx]
        except KeyError:
            x_val = idx
    else:
        x_val = idx

    x_pos = cast(float, x_val)
    y_pos = cast(float, val)

    if show_scatter:
        ax.scatter(
            [x_pos],
            [y_pos],
            color=color,
            s=config.markers.scatter_size,
            zorder=config.layout.zorder.markers,
        )

    y_fmt = ax.yaxis.get_major_formatter()
    label_text = y_fmt(val, None)

    if not label_text:
        label_text = f"{val:.2f}"

    text = ax.text(
        x_pos,
        y_pos,
        f"{label_prefix}{label_text}",
        ha=ha,
        va=va,
        color=color,
        fontproperties=theme.font,
        fontweight=config.markers.font_weight,
        zorder=config.layout.zorder.markers,
    )

    register_moveable(ax, text)


def add_highlight(
    ax: Axes,
    series: pd.Series,
    style: str | HighlightStyle = "line",
    color: str | None = None,
    x: pd.Index | pd.Series | None = None,
    modes: list[HighlightMode] | None = None,
) -> None:
    """Destaca pontos de dados com label formatado.

    Suporta multiplos modos de selecao (last, max, min). Indices duplicados
    sao renderizados apenas uma vez. Ignora silenciosamente series vazias,
    toda NaN, ou com valores nao-finitos.

    Args:
        style: Nome de um style registrado em ``HIGHLIGHT_STYLES`` ou
            instancia de ``HighlightStyle``.
        x: Dados X explicitos. Necessario quando a posicao X requer
            resolucao (ex: bar charts com DatetimeIndex).
        modes: Modos de highlight a aplicar. ``None`` = ``["last"]``.
    """
    if series.empty:
        logger.warning("Highlight skipped: series is empty")
        return

    valid_series = series.dropna()
    if valid_series.empty:
        logger.warning("Highlight skipped: all values are NaN")
        return

    if modes is None:
        modes = ["last"]

    if color is None:
        color = theme.colors.primary

    if isinstance(style, str):
        if style not in HIGHLIGHT_STYLES:
            available = ", ".join(sorted(HIGHLIGHT_STYLES))
            raise RegistryError(
                f"Highlight style '{style}' nao suportado. Disponiveis: {available}"
            )
        style = HIGHLIGHT_STYLES[style]

    seen_indices: set[object] = set()

    for mode in modes:
        target = _resolve_target(valid_series, mode)
        if target is None:
            continue

        idx, val = target
        if idx in seen_indices:
            continue
        seen_indices.add(idx)

        # Posicionamento: max/min usam centro acima/abaixo; last usa chart-type style
        if mode in ("max", "min"):
            ha = "center"
            va = "bottom" if mode == "max" else "top"
            prefix = ""
        else:
            ha = style.ha
            prefix = style.label_prefix
            va = style.va if style.va is not None else ("bottom" if val >= 0 else "top")

        _render_point(ax, idx, val, x, ha, va, prefix, style.show_scatter, color)
