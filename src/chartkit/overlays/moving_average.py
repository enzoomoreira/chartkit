import pandas as pd
from matplotlib.axes import Axes

from .._internal.collision import register_passive
from ..settings import get_config


def add_moving_average(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    window: int,
    color: str | None = None,
    linestyle: str = "-",
    linewidth: float | None = None,
    label: str | None = None,
    series: str | None = None,
) -> None:
    """Adiciona linha de media movel sobre os dados.

    Args:
        series: Coluna a usar se y_data for DataFrame (default: primeira).
    """
    config = get_config()

    if isinstance(y_data, pd.DataFrame):
        col = series if series is not None else y_data.columns[0]
        y_data = y_data[col]

    min_periods = config.lines.moving_avg_min_periods
    ma = y_data.rolling(window=window, min_periods=min_periods).mean()

    line_color = color if color is not None else config.colors.moving_average
    line_width = linewidth if linewidth is not None else config.lines.overlay_width
    line_label = (
        label
        if label is not None
        else config.labels.moving_average_format.format(window=window)
    )

    lines = ax.plot(
        x,
        ma,
        color=line_color,
        linestyle=linestyle,
        linewidth=line_width,
        label=line_label,
        zorder=config.layout.zorder.moving_average,
    )
    register_passive(ax, lines[0])
