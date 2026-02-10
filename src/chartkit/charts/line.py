from typing import cast

import pandas as pd
from matplotlib.axes import Axes

from ..overlays.markers import add_highlight
from ..settings import get_config
from ..styling.theme import theme
from .registry import ChartRegistry


@ChartRegistry.register("line")
def plot_line(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: bool,
    **kwargs,
) -> None:
    """Plota series temporais como grafico de linha.

    Se y_data for DataFrame, cada coluna vira uma serie com cor da paleta.
    """
    config = get_config()
    lines = config.lines

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    user_color = kwargs.pop("color", None)
    user_linewidth = kwargs.pop("linewidth", None)
    user_zorder = kwargs.pop("zorder", None)

    colors = theme.colors.cycle()

    plot_lines = []
    for i, col in enumerate(y_data.columns):
        c = user_color if user_color is not None else colors[i % len(colors)]
        label = str(col)

        (line,) = ax.plot(
            x,
            y_data[col],
            linewidth=user_linewidth
            if user_linewidth is not None
            else lines.main_width,
            color=c,
            label=label,
            zorder=user_zorder
            if user_zorder is not None
            else config.layout.zorder.data,
            **kwargs,
        )
        plot_lines.append(line)

        if highlight:
            add_highlight(ax, cast(pd.Series, y_data[col]), style="line", color=c)
