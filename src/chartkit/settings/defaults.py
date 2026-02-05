"""
Valores default para configuracao.

Valores neutros usados quando nenhum arquivo de configuracao
customizado e encontrado. Configure via TOML para personalizar.
"""

__all__ = ["DEFAULT_CONFIG", "create_default_config"]

from .schema import (
    BandsConfig,
    BarsConfig,
    BrandingConfig,
    ChartingConfig,
    CollisionConfig,
    ColorsConfig,
    FontsConfig,
    FontSizesConfig,
    FooterConfig,
    FormattersConfig,
    FrequencyDetectionConfig,
    LabelsConfig,
    LayoutConfig,
    LegendConfig,
    LinesConfig,
    LocaleConfig,
    MagnitudeConfig,
    MarkersConfig,
    PathsConfig,
    TitleConfig,
    TransformsConfig,
)


def create_default_config() -> ChartingConfig:
    """
    Cria uma instancia de ChartingConfig com todos os valores default.

    Returns:
        ChartingConfig com valores padrao neutros.
    """
    return ChartingConfig(
        branding=BrandingConfig(
            company_name="",
            footer_format="Fonte: {source}, {company_name}",
            footer_format_no_source="{company_name}",
        ),
        colors=ColorsConfig(
            primary="#00464D",
            secondary="#006B6B",
            tertiary="#008B8B",
            quaternary="#20B2AA",
            quinary="#5F9EA0",
            senary="#2E8B57",
            text="#00464D",
            grid="lightgray",
            background="white",
            positive="#00464D",
            negative="#8B0000",
            moving_average="#888888",
        ),
        fonts=FontsConfig(
            file="",
            fallback="sans-serif",
            assets_path="",
            sizes=FontSizesConfig(
                default=11,
                title=18,
                footer=9,
                axis_label=11,
            ),
        ),
        layout=LayoutConfig(
            figsize=(10.0, 6.0),
            dpi=300,
            footer=FooterConfig(
                x=0.01,
                y=0.01,
                color="gray",
            ),
            title=TitleConfig(
                padding=20,
                weight="bold",
            ),
        ),
        lines=LinesConfig(
            main_width=2.0,
            overlay_width=1.5,
            reference_style="--",
            legend=LegendConfig(
                alpha=0.9,
                frameon=True,
            ),
        ),
        bars=BarsConfig(
            width_default=0.8,
            width_monthly=20,
            width_annual=300,
            frequency_detection=FrequencyDetectionConfig(
                monthly_threshold=25,
                annual_threshold=300,
            ),
        ),
        bands=BandsConfig(
            alpha=0.15,
        ),
        markers=MarkersConfig(
            scatter_size=30,
            label_offset_x=5,
            label_offset_y=8,
        ),
        collision=CollisionConfig(
            margin_px=5,
            guide_threshold_px=30,
            extra_padding_px=15,
            px_to_points_ratio=0.75,
        ),
        transforms=TransformsConfig(
            mom_periods=1,
            yoy_periods=12,
            trading_days_per_year=252,
            normalize_base=100,
            rolling_window=12,
        ),
        formatters=FormattersConfig(
            locale=LocaleConfig(
                decimal=",",
                thousands=".",
                babel_locale="pt_BR",
            ),
            magnitude=MagnitudeConfig(
                suffixes=["", "k", "M", "B", "T"],
            ),
        ),
        labels=LabelsConfig(
            ath="ATH",
            atl="ATL",
            moving_average_format="MM{window}",
        ),
        paths=PathsConfig(
            charts_subdir="charts",
            outputs_dir="",
            assets_dir="",
            project_root_markers=[
                ".git",
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                ".project-root",
            ],
        ),
    )


# Instancia singleton com valores default
DEFAULT_CONFIG = create_default_config()
