import pandas as pd

from .._internal.collision import register_fixed
from ..settings import get_config
from ..styling.theme import theme


def add_ath_line(
    ax,
    y_data: pd.Series | pd.DataFrame,
    color: str | None = None,
    linestyle: str | None = None,
    label: str | None = None,
    linewidth: float | None = None,
    series: str | None = None,
) -> None:
    """Adiciona linha horizontal no All-Time High (valor maximo)."""
    config = get_config()

    if isinstance(y_data, pd.DataFrame):
        col = series if series else y_data.columns[0]
        y_data = y_data[col]

    ath_value = y_data.max()
    if pd.isna(ath_value):
        return

    line = ax.axhline(
        y=ath_value,
        color=color if color else theme.colors.positive,
        linestyle=linestyle if linestyle else config.lines.reference_style,
        linewidth=linewidth if linewidth else config.lines.overlay_width,
        label=label if label else config.labels.ath,
        zorder=config.layout.zorder.reference_lines,
    )
    register_fixed(ax, line)


def add_atl_line(
    ax,
    y_data: pd.Series | pd.DataFrame,
    color: str | None = None,
    linestyle: str | None = None,
    label: str | None = None,
    linewidth: float | None = None,
    series: str | None = None,
) -> None:
    """Adiciona linha horizontal no All-Time Low (valor minimo)."""
    config = get_config()

    if isinstance(y_data, pd.DataFrame):
        col = series if series else y_data.columns[0]
        y_data = y_data[col]

    atl_value = y_data.min()
    if pd.isna(atl_value):
        return

    line = ax.axhline(
        y=atl_value,
        color=color if color else theme.colors.negative,
        linestyle=linestyle if linestyle else config.lines.reference_style,
        linewidth=linewidth if linewidth else config.lines.overlay_width,
        label=label if label else config.labels.atl,
        zorder=config.layout.zorder.reference_lines,
    )
    register_fixed(ax, line)


def add_hline(
    ax,
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
        color=color if color else theme.colors.grid,
        linestyle=linestyle if linestyle else config.lines.reference_style,
        linewidth=linewidth if linewidth else config.lines.overlay_width,
        label=label,
        zorder=config.layout.zorder.reference_lines,
    )
    register_fixed(ax, line)
