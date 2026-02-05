import pandas as pd
from matplotlib.axes import Axes

from ..overlays.markers import highlight_last_point
from ..settings import get_config
from ..styling.theme import theme


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

    colors = theme.colors.cycle()

    plot_lines = []
    for i, col in enumerate(y_data.columns):
        if "color" in kwargs:
            c = kwargs["color"]
        else:
            c = colors[i % len(colors)]

        label = str(col)

        line, = ax.plot(
            x, y_data[col], linewidth=lines.main_width, color=c, label=label,
            zorder=config.layout.zorder.data, **kwargs
        )
        plot_lines.append(line)

        if highlight:
            highlight_last_point(ax, y_data[col], color=c)

    if y_data.shape[1] > 1:
        ax.legend(
            loc="best",
            frameon=lines.legend.frameon,
            framealpha=lines.legend.alpha,
        )
