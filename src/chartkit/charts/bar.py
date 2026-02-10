from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from ..overlays.markers import add_highlight
from ..settings import get_config
from ..styling.theme import theme
from ._helpers import detect_bar_width
from .registry import ChartRegistry

if TYPE_CHECKING:
    from ..overlays.markers import HighlightMode


@ChartRegistry.register("bar")
def plot_bar(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode] | None = None,
    y_origin: Literal["zero", "auto"] = "zero",
    **kwargs,
) -> None:
    """Plota grafico de barras com largura automatica baseada na frequencia.

    Args:
        y_origin: ``'zero'`` inclui zero no eixo Y (default),
            ``'auto'`` ajusta limites para focar nos dados com margem.
    """
    if y_origin not in ("zero", "auto"):
        raise ValueError(f"y_origin deve ser 'zero' ou 'auto', recebeu: {y_origin!r}")

    config = get_config()
    bars = config.bars

    if "color" not in kwargs:
        kwargs["color"] = theme.colors.primary

    multi_col = isinstance(y_data, pd.DataFrame) and y_data.shape[1] > 1

    if multi_col:
        if len(y_data) > 500:
            logger.warning(
                "Bar chart com {} pontos pode ficar ilegivel. Considere kind='line'.",
                len(y_data),
            )
        # pandas .plot(kind="bar") usa eixo categorico; width e relativo (0-1)
        y_data.plot(kind="bar", ax=ax, width=bars.width_default, **kwargs)
    else:
        vals = y_data.iloc[:, 0] if isinstance(y_data, pd.DataFrame) else y_data

        if len(vals) > 500:
            logger.warning(
                "Bar chart com {} pontos pode ficar ilegivel. Considere kind='line'.",
                len(vals),
            )

        width = detect_bar_width(x, bars)
        ax.bar(x, vals, width=width, zorder=config.layout.zorder.data, **kwargs)

    if y_origin == "auto":
        all_vals = y_data.stack().dropna() if multi_col else vals.dropna()
        if not all_vals.empty:
            ymin, ymax = all_vals.min(), all_vals.max()
            margin = (ymax - ymin) * bars.auto_margin
            ax.set_ylim(ymin - margin, ymax + margin)
    else:
        ymin, ymax = ax.get_ylim()
        if ymin > 0:
            ax.set_ylim(0, ymax)
        elif ymax < 0:
            ax.set_ylim(ymin, 0)

    if highlight and not multi_col:
        color = kwargs.get("color", theme.colors.primary)
        add_highlight(ax, vals, style="bar", color=color, x=x, modes=highlight)
