import numpy as np
import pandas as pd

from .._internal.collision import register_moveable
from ..settings import get_config
from ..styling.theme import theme


def highlight_last_point(ax, series: pd.Series, color: str | None = None) -> None:
    """Destaca o ultimo ponto valido com marcador e label formatado.

    Ignora silenciosamente se a serie estiver vazia, toda NaN, ou com
    ultimo valor infinito. O valor e formatado pelo formatter do eixo Y.
    """
    if series.empty:
        return

    config = get_config()
    markers = config.markers

    valid_series = series.dropna()
    if valid_series.empty:
        return

    last_date = valid_series.index[-1]
    last_val = valid_series.iloc[-1]

    if not np.isfinite(last_val):
        return

    if color is None:
        color = theme.colors.primary

    ax.scatter(
        [last_date],
        [last_val],
        color=color,
        s=markers.scatter_size,
        zorder=config.layout.zorder.markers,
    )

    y_fmt = ax.yaxis.get_major_formatter()
    label_text = y_fmt(last_val, None)

    if not label_text:
        label_text = f"{last_val:.2f}"

    # Espacos no inicio criam gap visual entre o marcador e o texto
    text = ax.text(
        last_date,
        last_val,
        f"  {label_text}",
        ha="left",
        va="center",
        color=color,
        fontproperties=theme.font,
        fontweight="bold",
        zorder=config.layout.zorder.markers,
    )

    register_moveable(ax, text)


def highlight_last_bar(ax, x, series: pd.Series, color: str | None = None) -> None:
    """Destaca o valor da ultima barra com label no topo.

    Ignora silenciosamente se a serie estiver vazia, toda NaN, ou com
    ultimo valor infinito.
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

    # Resolve posicao X a partir do indice
    if hasattr(x, "get_loc"):
        try:
            x_pos = x.get_loc(last_idx)
            x_val = x[x_pos]
        except KeyError:
            x_val = last_idx
    else:
        x_val = last_idx

    y_fmt = ax.yaxis.get_major_formatter()
    label_text = y_fmt(last_val, None)

    if not label_text:
        label_text = f"{last_val:.2f}"

    va = "bottom" if last_val >= 0 else "top"

    text = ax.text(
        x_val,
        last_val,
        label_text,
        ha="center",
        va=va,
        color=color,
        fontproperties=theme.font,
        fontweight="bold",
        zorder=config.layout.zorder.markers,
    )

    register_moveable(ax, text)
