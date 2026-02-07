from typing import Any

import pandas as pd
from matplotlib.axes import Axes

from .._internal.collision import register_fixed
from ..settings import get_config
from ..styling.theme import theme


def _add_extreme_line(
    ax: Axes,
    y_data: pd.Series | pd.DataFrame,
    extreme: str,
    default_color: str,
    default_label: str,
    color: str | None = None,
    linestyle: str | None = None,
    label: str | None = None,
    linewidth: float | None = None,
    series: str | None = None,
) -> None:
    """Adiciona linha horizontal no extremo (max ou min) dos dados."""
    config = get_config()

    if isinstance(y_data, pd.DataFrame):
        col = series if series is not None else y_data.columns[0]
        y_data = y_data[col]

    value = getattr(y_data, extreme)()
    if pd.isna(value):
        return

    line = ax.axhline(
        y=value,
        color=color if color is not None else default_color,
        linestyle=linestyle if linestyle is not None else config.lines.reference_style,
        linewidth=linewidth if linewidth is not None else config.lines.overlay_width,
        label=label if label is not None else default_label,
        zorder=config.layout.zorder.reference_lines,
    )
    register_fixed(ax, line)


def add_ath_line(
    ax: Axes,
    y_data: pd.Series | pd.DataFrame,
    **kwargs: Any,
) -> None:
    """Adiciona linha horizontal no All-Time High (valor maximo)."""
    config = get_config()
    _add_extreme_line(
        ax, y_data, extreme="max",
        default_color=theme.colors.positive,
        default_label=config.labels.ath,
        **kwargs,
    )


def add_atl_line(
    ax: Axes,
    y_data: pd.Series | pd.DataFrame,
    **kwargs: Any,
) -> None:
    """Adiciona linha horizontal no All-Time Low (valor minimo)."""
    config = get_config()
    _add_extreme_line(
        ax, y_data, extreme="min",
        default_color=theme.colors.negative,
        default_label=config.labels.atl,
        **kwargs,
    )


def add_hline(
    ax: Axes,
    value: float,
    color: str | None = None,
    linestyle: str | None = None,
    label: str | None = None,
    linewidth: float | None = None,
) -> None:
    """Adiciona linha horizontal em valor arbitrario."""
    config = get_config()

    line = ax.axhline(
        y=value,
        color=color if color is not None else theme.colors.grid,
        linestyle=linestyle if linestyle is not None else config.lines.reference_style,
        linewidth=linewidth if linewidth is not None else config.lines.overlay_width,
        label=label,
        zorder=config.layout.zorder.reference_lines,
    )
    register_fixed(ax, line)
