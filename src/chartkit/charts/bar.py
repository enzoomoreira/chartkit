"""
Grafico de barras para series temporais.
"""

import pandas as pd
from matplotlib.axes import Axes

from ..overlays.markers import highlight_last_bar
from ..settings import get_config
from ..styling.theme import theme


def plot_bar(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: bool = False,
    y_origin: str = "zero",
    **kwargs,
) -> None:
    """
    Plota grafico de barras com largura automatica baseada na frequencia.

    A largura das barras e calculada automaticamente com base no intervalo
    entre pontos de dados (diario, mensal ou anual).

    Args:
        ax: Matplotlib Axes onde o grafico sera desenhado.
        x: Dados do eixo X (index do DataFrame ou coluna especifica).
        y_data: Series ou DataFrame com dados do eixo Y. Se DataFrame com
            multiplas colunas, usa plotagem agrupada do pandas.
        highlight: Se True, destaca o ultimo valor com label no topo da barra.
        y_origin: Origem do eixo Y:
            - 'zero': Inclui zero no eixo Y (default, recomendado para barras)
            - 'auto': Ajusta limites para focar nos dados com margem de 10%
        **kwargs: Argumentos extras passados para ax.bar() do matplotlib.
    """
    config = get_config()
    bars = config.bars

    if "color" not in kwargs:
        kwargs["color"] = theme.colors.primary

    # Largura da barra inteligente baseada na frequencia dos dados
    width = bars.width_default
    if pd.api.types.is_datetime64_any_dtype(x):
        if len(x) > 1:
            avg_diff = (x.max() - x.min()) / (len(x) - 1)
            # Ordem importa: verificar anual primeiro (maior threshold)
            if avg_diff.days > bars.frequency_detection.annual_threshold:
                width = bars.width_annual
            elif avg_diff.days > bars.frequency_detection.monthly_threshold:
                width = bars.width_monthly

    if isinstance(y_data, pd.DataFrame):
        if y_data.shape[1] > 1:
            # Multiplas series: usa pandas plot
            y_data.plot(kind="bar", ax=ax, width=bars.width_default, **kwargs)
            return
        else:
            vals = y_data.iloc[:, 0]
    else:
        vals = y_data

    ax.bar(x, vals, width=width, **kwargs)

    # Ajusta origem do eixo Y
    if y_origin == "auto":
        # Ajusta eixo Y para focar nos dados com margem
        vals_clean = vals.dropna()
        if not vals_clean.empty:
            ymin, ymax = vals_clean.min(), vals_clean.max()
            margin = (ymax - ymin) * 0.1  # 10% de margem
            ax.set_ylim(ymin - margin, ymax + margin)
    else:
        # Default: inclui zero no eixo Y
        ymin, ymax = ax.get_ylim()
        if ymin > 0:
            ax.set_ylim(0, ymax)
        elif ymax < 0:
            ax.set_ylim(ymin, 0)

    # Destaca ultimo valor se solicitado
    if highlight:
        color = kwargs.get("color", theme.colors.primary)
        highlight_last_bar(ax, x, vals, color=color)
