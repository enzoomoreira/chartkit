"""Schema de configuracao com dataclasses tipadas."""

from dataclasses import dataclass, field

__all__ = [
    "BrandingConfig",
    "ColorsConfig",
    "FontSizesConfig",
    "FontsConfig",
    "FooterConfig",
    "TitleConfig",
    "ZOrderConfig",
    "LayoutConfig",
    "LegendConfig",
    "LinesConfig",
    "FrequencyDetectionConfig",
    "BarsConfig",
    "BandsConfig",
    "MarkersConfig",
    "CollisionConfig",
    "TransformsConfig",
    "LocaleConfig",
    "MagnitudeConfig",
    "FormattersConfig",
    "LabelsConfig",
    "PathsConfig",
    "ChartingConfig",
]


@dataclass
class BrandingConfig:
    company_name: str = ""
    footer_format: str = "Fonte: {source}, {company_name}"
    footer_format_no_source: str = "{company_name}"


@dataclass
class ColorsConfig:
    # Cores principais (gradiente institucional)
    primary: str = "#00464D"
    secondary: str = "#006B6B"
    tertiary: str = "#008B8B"
    quaternary: str = "#20B2AA"
    quinary: str = "#5F9EA0"
    senary: str = "#2E8B57"

    # Cores semanticas
    text: str = "#00464D"
    grid: str = "lightgray"
    background: str = "white"
    positive: str = "#00464D"
    negative: str = "#8B0000"

    # Overlays
    moving_average: str = "#888888"

    def cycle(self) -> list[str]:
        """Retorna lista de cores em gradiente para multiplas series."""
        return [
            self.primary,
            self.secondary,
            self.tertiary,
            self.quaternary,
            self.quinary,
            self.senary,
        ]


@dataclass
class FontSizesConfig:
    default: int = 11
    title: int = 18
    footer: int = 9
    axis_label: int = 11


@dataclass
class FontsConfig:
    file: str = ""  # Caminho relativo a assets_path ou absoluto (vazio = fallback)
    fallback: str = "sans-serif"
    assets_path: str = ""  # Vazio = auto-discovery do projeto host
    sizes: FontSizesConfig = field(default_factory=FontSizesConfig)


@dataclass
class FooterConfig:
    x: float = 0.01
    y: float = 0.01
    color: str = "gray"


@dataclass
class TitleConfig:
    padding: int = 20
    weight: str = "bold"


@dataclass
class ZOrderConfig:
    """Ordem de camadas: bands(0) < reference_lines(1) < moving_average(2) < data(3) < markers(5)."""

    bands: int = 0
    reference_lines: int = 1
    moving_average: int = 2
    data: int = 3
    markers: int = 5


@dataclass
class LayoutConfig:
    figsize: tuple[float, float] = (10.0, 6.0)
    dpi: int = 300
    footer: FooterConfig = field(default_factory=FooterConfig)
    title: TitleConfig = field(default_factory=TitleConfig)
    zorder: ZOrderConfig = field(default_factory=ZOrderConfig)


@dataclass
class LegendConfig:
    alpha: float = 0.9
    frameon: bool = True


@dataclass
class LinesConfig:
    main_width: float = 2.0
    overlay_width: float = 1.5
    reference_style: str = "--"
    moving_avg_min_periods: int = 1
    legend: LegendConfig = field(default_factory=LegendConfig)


@dataclass
class FrequencyDetectionConfig:
    monthly_threshold: int = 25
    annual_threshold: int = 300


@dataclass
class BarsConfig:
    width_default: float = 0.8
    width_monthly: int = 20
    width_annual: int = 300
    auto_margin: float = 0.1  # Margem (%) para y_origin='auto'
    frequency_detection: FrequencyDetectionConfig = field(
        default_factory=FrequencyDetectionConfig
    )


@dataclass
class BandsConfig:
    alpha: float = 0.15


@dataclass
class MarkersConfig:
    scatter_size: int = 30


@dataclass
class CollisionConfig:
    movement: str = "y"
    obstacle_padding_px: float = 8.0
    label_padding_px: float = 4.0
    max_iterations: int = 50
    connector_threshold_px: float = 30.0
    connector_alpha: float = 0.6
    connector_style: str = "-"


@dataclass
class TransformsConfig:
    mom_periods: int = 1
    yoy_periods: int = 12
    trading_days_per_year: int = 252
    normalize_base: int = 100
    rolling_window: int = 12


@dataclass
class LocaleConfig:
    decimal: str = ","
    thousands: str = "."
    babel_locale: str = "pt_BR"


@dataclass
class MagnitudeConfig:
    suffixes: list[str] = field(
        default_factory=lambda: ["", "k", "M", "B", "T"]
    )


@dataclass
class FormattersConfig:
    locale: LocaleConfig = field(default_factory=LocaleConfig)
    magnitude: MagnitudeConfig = field(default_factory=MagnitudeConfig)


@dataclass
class LabelsConfig:
    ath: str = "ATH"
    atl: str = "ATL"
    moving_average_format: str = "MM{window}"


@dataclass
class PathsConfig:
    charts_subdir: str = "charts"
    outputs_dir: str = ""  # Vazio = auto-discovery do projeto host
    assets_dir: str = ""  # Vazio = auto-discovery do projeto host
    project_root_markers: list[str] = field(
        default_factory=lambda: [
            ".git",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            ".project-root",
        ]
    )


@dataclass
class ChartingConfig:
    """Configuracao principal que agrega todas as sub-configuracoes."""

    branding: BrandingConfig = field(default_factory=BrandingConfig)
    colors: ColorsConfig = field(default_factory=ColorsConfig)
    fonts: FontsConfig = field(default_factory=FontsConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
    lines: LinesConfig = field(default_factory=LinesConfig)
    bars: BarsConfig = field(default_factory=BarsConfig)
    bands: BandsConfig = field(default_factory=BandsConfig)
    markers: MarkersConfig = field(default_factory=MarkersConfig)
    collision: CollisionConfig = field(default_factory=CollisionConfig)
    transforms: TransformsConfig = field(default_factory=TransformsConfig)
    formatters: FormattersConfig = field(default_factory=FormattersConfig)
    labels: LabelsConfig = field(default_factory=LabelsConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
