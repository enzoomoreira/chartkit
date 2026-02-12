from matplotlib.figure import Figure

from ..settings import get_config
from ..styling.theme import theme


def add_footer(fig: Figure, source: str | None = None) -> None:
    """Add standard footer to the chart, aligned with the left edge of the axes.

    The format is controlled by ``branding.footer_format`` (with source) or
    ``branding.footer_format_no_source`` (without source) in settings.

    Args:
        source: Data source. When ``None``, uses ``branding.default_source``
            from configuration as fallback.
    """
    config = get_config()
    branding = config.branding
    layout = config.layout.footer
    fonts = config.fonts.sizes

    if source is None:
        source = branding.default_source

    if source:
        footer_text = branding.footer_format.format(
            source=source,
            company_name=branding.company_name,
        )
    else:
        footer_text = branding.footer_format_no_source.format(
            company_name=branding.company_name,
        )

    # Align with left edge of axes (chart area)
    x_pos = fig.axes[0].get_position().x0 if fig.axes else 0.01

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
