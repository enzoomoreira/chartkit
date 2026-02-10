import numpy as np
import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from ..overlays.markers import add_highlight
from ..settings import get_config
from ..styling.theme import theme
from ._helpers import detect_bar_width
from .registry import ChartRegistry

__all__ = ["plot_stacked_bar"]


@ChartRegistry.register("stacked_bar")
def plot_stacked_bar(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: bool = False,
    y_origin: str = "zero",
    **kwargs,
) -> None:
    """Plota grafico de barras empilhadas para composicao.

    Cada coluna do DataFrame vira uma camada da pilha, com cores da paleta.
    Series unica se comporta identicamente a um bar chart normal.

    Args:
        y_origin: ``'zero'`` inclui zero no eixo Y (default),
            ``'auto'`` ajusta limites para focar nos dados com margem.
    """
    config = get_config()
    bars = config.bars

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    if len(y_data) > 500:
        logger.warning(
            "Stacked bar com {} pontos pode ficar ilegivel. Considere kind='line'.",
            len(y_data),
        )

    user_color = kwargs.pop("color", None)
    colors = theme.colors.cycle()
    width = detect_bar_width(x, bars)

    bottom = np.zeros(len(y_data))
    for i, col in enumerate(y_data.columns):
        c = user_color if user_color is not None else colors[i % len(colors)]
        vals = y_data[col].fillna(0)

        ax.bar(
            x,
            vals,
            width=width,
            bottom=bottom,
            color=c,
            label=str(col),
            zorder=config.layout.zorder.data,
            **kwargs,
        )
        bottom = bottom + vals.values

    if y_origin == "auto":
        total = y_data.sum(axis=1)
        total_clean = total.dropna()
        if not total_clean.empty:
            ymin, ymax = total_clean.min(), total_clean.max()
            margin = (ymax - ymin) * bars.auto_margin
            ax.set_ylim(ymin - margin, ymax + margin)
    else:
        ymin, ymax = ax.get_ylim()
        if ymin > 0:
            ax.set_ylim(0, ymax)
        elif ymax < 0:
            ax.set_ylim(ymin, 0)

    if highlight:
        total = y_data.sum(axis=1)
        color = user_color if user_color is not None else theme.colors.primary
        add_highlight(ax, total, style="bar", color=color, x=x)
