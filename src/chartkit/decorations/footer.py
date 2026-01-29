"""
Rodape padronizado para graficos.
"""

from ..settings import get_config
from ..styling.theme import theme


def add_footer(fig, source: str = None):
    """
    Adiciona rodape padrao ao grafico.

    Formato configuravel via settings:
    - Com fonte: "{footer_format}" (default: "Fonte: {source}, {company_name}")
    - Sem fonte: "{footer_format_no_source}" (default: "{company_name}")

    O footer e alinhado com a borda esquerda da area do grafico (axes).

    Args:
        fig: Matplotlib Figure onde o rodape sera adicionado.
        source: Fonte dos dados (ex: 'BCB', 'IBGE'). Se None,
                usa formato sem fonte.
    """
    config = get_config()
    branding = config.branding
    layout = config.layout.footer
    fonts = config.fonts.sizes

    # Formata texto do rodape
    if source:
        footer_text = branding.footer_format.format(
            source=source,
            company_name=branding.company_name,
        )
    else:
        footer_text = branding.footer_format_no_source.format(
            company_name=branding.company_name,
        )

    # Alinha com a borda esquerda do axes (area do grafico)
    x_pos = layout.x
    if fig.axes:
        ax = fig.axes[0]
        bbox = ax.get_position()
        x_pos = bbox.x0  # Borda esquerda do axes em coordenadas de figura

    fig.text(
        x_pos,
        layout.y,
        footer_text,
        ha="left",
        va="bottom",
        fontsize=fonts.footer,
        color=layout.color,
        fontproperties=theme.font,
    )
