from ..settings import get_config
from ..styling.theme import theme


def add_footer(fig, source: str | None = None) -> None:
    """Adiciona rodape padrao ao grafico, alinhado com a borda esquerda do axes.

    O formato e controlado por ``branding.footer_format`` (com source) ou
    ``branding.footer_format_no_source`` (sem source) em settings.
    """
    config = get_config()
    branding = config.branding
    layout = config.layout.footer
    fonts = config.fonts.sizes

    if source:
        footer_text = branding.footer_format.format(
            source=source,
            company_name=branding.company_name,
        )
    else:
        footer_text = branding.footer_format_no_source.format(
            company_name=branding.company_name,
        )

    # Alinha com borda esquerda do axes (area do grafico)
    x_pos = layout.x
    if fig.axes:
        ax = fig.axes[0]
        bbox = ax.get_position()
        x_pos = bbox.x0

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
