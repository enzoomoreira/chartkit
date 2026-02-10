from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd
from matplotlib.axes import Axes

from .._internal.collision import register_moveable
from ..settings import get_config
from ..styling.theme import theme


@dataclass(frozen=True)
class HighlightStyle:
    """Estrategia de posicionamento para highlight de ultimo valor."""

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


def add_highlight(
    ax: Axes,
    series: pd.Series,
    style: str | HighlightStyle = "line",
    color: str | None = None,
    x: pd.Index | pd.Series | None = None,
) -> None:
    """Destaca o ultimo ponto valido com label formatado.

    Ignora silenciosamente se a serie estiver vazia, toda NaN, ou com
    ultimo valor infinito.

    Args:
        style: Nome de um style registrado em ``HIGHLIGHT_STYLES`` ou
            instancia de ``HighlightStyle``.
        x: Dados X explicitos. Necessario quando a posicao X requer
            resolucao (ex: bar charts com DatetimeIndex).
    """
    if series.empty:
        return

    config = get_config()

    valid_series = series.dropna()
    if valid_series.empty:
        return

    last_idx = valid_series.index[-1]
    last_val = valid_series.iloc[-1]

    if not np.isfinite(last_val):
        return

    if color is None:
        color = theme.colors.primary

    if isinstance(style, str):
        style = HIGHLIGHT_STYLES[style]

    # Resolve posicao X
    if x is not None and hasattr(x, "get_loc"):
        try:
            loc_idx = x.get_loc(last_idx)
            x_val = x[loc_idx]
        except KeyError:
            x_val = last_idx
    else:
        x_val = last_idx

    x_pos = cast(float, x_val)
    y_pos = cast(float, last_val)

    # Scatter marker
    if style.show_scatter:
        ax.scatter(
            [x_pos],
            [y_pos],
            color=color,
            s=config.markers.scatter_size,
            zorder=config.layout.zorder.markers,
        )

    # Label formatado
    y_fmt = ax.yaxis.get_major_formatter()
    label_text = y_fmt(last_val, None)

    if not label_text:
        label_text = f"{last_val:.2f}"

    va = style.va
    if va is None:
        va = "bottom" if last_val >= 0 else "top"

    text = ax.text(
        x_pos,
        y_pos,
        f"{style.label_prefix}{label_text}",
        ha=style.ha,
        va=va,
        color=color,
        fontproperties=theme.font,
        fontweight="bold",
        zorder=config.layout.zorder.markers,
    )

    register_moveable(ax, text)
