"""
Media movel para graficos.
"""

import pandas as pd

from ..settings import get_config


def add_moving_average(
    ax,
    x,
    y_data: pd.Series | pd.DataFrame,
    window: int,
    color: str = None,
    linestyle: str = "-",
    linewidth: float = None,
    label: str = None,
    series: str = None,
) -> None:
    """
    Adiciona linha de media movel sobre os dados.

    Args:
        ax: Matplotlib Axes
        x: Dados do eixo X (index)
        y_data: Series ou DataFrame com os dados
        window: Janela da media movel (numero de periodos)
        color: Cor da linha (default: config.colors.moving_average)
        linestyle: Estilo da linha (default: '-')
        linewidth: Espessura da linha (default: config.lines.overlay_width)
        label: Rotulo para legenda (default: config.labels.moving_average_format)
        series: Nome da coluna se y_data for DataFrame (default: primeira coluna)

    Example:
        >>> add_moving_average(ax, df.index, df['valor'], window=12)
    """
    config = get_config()

    # Resolve series se for DataFrame
    if isinstance(y_data, pd.DataFrame):
        col = series if series else y_data.columns[0]
        # TODO(errors): validar col em y_data.columns (KeyError cru se invalido)
        y_data = y_data[col]

    # Calcula media movel com min_periods configuravel
    min_periods = config.lines.moving_avg_min_periods
    ma = y_data.rolling(window=window, min_periods=min_periods).mean()

    # Cor default: config.colors.moving_average
    line_color = color if color else config.colors.moving_average

    # Largura default: config.lines.overlay_width
    line_width = linewidth if linewidth else config.lines.overlay_width

    # Label default: config.labels.moving_average_format
    line_label = label if label else config.labels.moving_average_format.format(window=window)

    ax.plot(
        x,
        ma,
        color=line_color,
        linestyle=linestyle,
        linewidth=line_width,
        label=line_label,
        zorder=config.layout.zorder.moving_average,
    )
