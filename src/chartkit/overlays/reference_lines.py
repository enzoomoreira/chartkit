"""
Linhas de referencia horizontais para graficos.

Inclui linhas ATH/ATL (All-Time High/Low) e linhas customizadas.
"""

import pandas as pd

from ..settings import get_config
from ..styling.theme import theme


def add_ath_line(
    ax,
    y_data: pd.Series | pd.DataFrame,
    color: str = None,
    linestyle: str = None,
    label: str = None,
    linewidth: float = None,
    series: str = None,
) -> None:
    """
    Adiciona linha horizontal no All-Time High (valor maximo).

    Args:
        ax: Matplotlib Axes
        y_data: Series ou DataFrame com os dados
        color: Cor da linha (default: config.colors.positive)
        linestyle: Estilo da linha (default: config.lines.reference_style)
        label: Rotulo da linha (default: config.labels.ath)
        linewidth: Espessura da linha (default: config.lines.overlay_width)
        series: Nome da coluna se y_data for DataFrame (default: primeira coluna)
    """
    config = get_config()

    # Resolve series se for DataFrame
    if isinstance(y_data, pd.DataFrame):
        col = series if series else y_data.columns[0]
        y_data = y_data[col]

    # Calcula ATH ignorando NaN
    ath_value = y_data.max()
    if pd.isna(ath_value):
        return  # Sem dados validos

    # Valores default da config
    line_color = color if color else theme.colors.positive
    line_style = linestyle if linestyle else config.lines.reference_style
    line_width = linewidth if linewidth else config.lines.overlay_width
    line_label = label if label else config.labels.ath

    ax.axhline(
        y=ath_value,
        color=line_color,
        linestyle=line_style,
        linewidth=line_width,
        label=line_label,
        zorder=config.layout.zorder.reference_lines,
    )


def add_atl_line(
    ax,
    y_data: pd.Series | pd.DataFrame,
    color: str = None,
    linestyle: str = None,
    label: str = None,
    linewidth: float = None,
    series: str = None,
) -> None:
    """
    Adiciona linha horizontal no All-Time Low (valor minimo).

    Args:
        ax: Matplotlib Axes
        y_data: Series ou DataFrame com os dados
        color: Cor da linha (default: config.colors.negative)
        linestyle: Estilo da linha (default: config.lines.reference_style)
        label: Rotulo da linha (default: config.labels.atl)
        linewidth: Espessura da linha (default: config.lines.overlay_width)
        series: Nome da coluna se y_data for DataFrame (default: primeira coluna)
    """
    config = get_config()

    # Resolve series se for DataFrame
    if isinstance(y_data, pd.DataFrame):
        col = series if series else y_data.columns[0]
        y_data = y_data[col]

    # Calcula ATL ignorando NaN
    atl_value = y_data.min()
    if pd.isna(atl_value):
        return  # Sem dados validos

    # Valores default da config
    line_color = color if color else theme.colors.negative
    line_style = linestyle if linestyle else config.lines.reference_style
    line_width = linewidth if linewidth else config.lines.overlay_width
    line_label = label if label else config.labels.atl

    ax.axhline(
        y=atl_value,
        color=line_color,
        linestyle=line_style,
        linewidth=line_width,
        label=line_label,
        zorder=config.layout.zorder.reference_lines,
    )


def add_hline(
    ax,
    value: float,
    color: str = None,
    linestyle: str = None,
    label: str = None,
    linewidth: float = None,
) -> None:
    """
    Adiciona linha horizontal em valor arbitrario.

    Util para marcar metas, limites ou valores de referencia.

    Args:
        ax: Matplotlib Axes
        value: Valor Y onde a linha sera desenhada
        color: Cor da linha (default: config.colors.grid)
        linestyle: Estilo da linha (default: config.lines.reference_style)
        label: Rotulo da linha (opcional)
        linewidth: Espessura da linha (default: config.lines.overlay_width)

    Example:
        >>> add_hline(ax, 3.0, label='Meta de Inflacao', color='green')
    """
    config = get_config()

    # Valores default da config
    line_color = color if color else theme.colors.grid
    line_style = linestyle if linestyle else config.lines.reference_style
    line_width = linewidth if linewidth else config.lines.overlay_width

    ax.axhline(
        y=value,
        color=line_color,
        linestyle=line_style,
        linewidth=line_width,
        label=label,
        zorder=config.layout.zorder.reference_lines,
    )
