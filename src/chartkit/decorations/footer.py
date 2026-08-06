from matplotlib.figure import Figure

from ..exceptions import ValidationError
from ..settings import get_config
from ..styling.theme import theme

# Trimmed from both ends of the formatted footer. Templates join their fields
# with punctuation, so an empty field leaves the separator behind.
_DANGLING = " ,;|-–—/"  # noqa: RUF001 - the dashes are data, not prose


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
        setting, template = "footer_format", branding.footer_format
        fields = {"source": source, "company_name": branding.company_name}
    else:
        setting = "footer_format_no_source"
        template = branding.footer_format_no_source
        fields = {"company_name": branding.company_name}

    try:
        footer_text = template.format(**fields)
    except KeyError as exc:
        # A typo in the TOML template otherwise surfaces as a bare KeyError
        # from inside plot(), naming the placeholder but not where it lives.
        raise ValidationError(
            f"branding.{setting} references unknown placeholder {exc}. "
            f"Available: {', '.join('{' + name + '}' for name in fields)}."
        ) from exc

    # ``company_name`` defaults to empty, which turns the default template
    # into "Fonte: Bloomberg, " -- a separator pointing at nothing.
    footer_text = footer_text.strip(_DANGLING)

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
