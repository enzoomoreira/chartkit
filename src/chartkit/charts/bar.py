from typing import cast

import pandas as pd
from matplotlib.axes import Axes

from ..overlays.markers import highlight_last
from ..settings import get_config
from ..styling.theme import theme
from .registry import ChartRegistry


@ChartRegistry.register("bar")
def plot_bar(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: bool = False,
    y_origin: str = "zero",
    **kwargs,
) -> None:
    """Plota grafico de barras com largura automatica baseada na frequencia.

    Args:
        y_origin: ``'zero'`` inclui zero no eixo Y (default),
            ``'auto'`` ajusta limites para focar nos dados com margem.
    """
    config = get_config()
    bars = config.bars

    if "color" not in kwargs:
        kwargs["color"] = theme.colors.primary

    # Largura inteligente baseada na frequencia dos dados
    width = bars.width_default
    if pd.api.types.is_datetime64_any_dtype(x):
        if len(x) > 1:
            span = cast(pd.Timestamp, x.max()) - cast(pd.Timestamp, x.min())
            avg_diff = span / (len(x) - 1)
            if avg_diff.days > bars.frequency_detection.annual_threshold:
                width = bars.width_annual
            elif avg_diff.days > bars.frequency_detection.monthly_threshold:
                width = bars.width_monthly

    if isinstance(y_data, pd.DataFrame):
        if y_data.shape[1] > 1:
            y_data.plot(kind="bar", ax=ax, width=bars.width_default, **kwargs)
            return
        else:
            vals = y_data.iloc[:, 0]
    else:
        vals = y_data

    ax.bar(x, vals, width=width, zorder=config.layout.zorder.data, **kwargs)

    if y_origin == "auto":
        vals_clean = vals.dropna()
        if not vals_clean.empty:
            ymin, ymax = vals_clean.min(), vals_clean.max()
            margin = (ymax - ymin) * bars.auto_margin
            ax.set_ylim(ymin - margin, ymax + margin)
    else:
        ymin, ymax = ax.get_ylim()
        if ymin > 0:
            ax.set_ylim(0, ymax)
        elif ymax < 0:
            ax.set_ylim(ymin, 0)

    if highlight:
        color = kwargs.get("color", theme.colors.primary)
        highlight_last(ax, vals, style="bar", color=color, x=x)
