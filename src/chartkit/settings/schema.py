"""
Schema de configuracao.

Define dataclasses tipadas para todas as configuracoes da biblioteca,
permitindo validacao em tempo de desenvolvimento e autocompletar em IDEs.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BrandingConfig:
    """Configuracoes de branding/marca para rodapes."""

    company_name: str = ""
    footer_format: str = "Fonte: {source}, {company_name}"
    footer_format_no_source: str = "{company_name}"


@dataclass
class ColorsConfig:
    """Paleta de cores para graficos."""

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
    """Tamanhos de fonte em pontos."""

    default: int = 11
    title: int = 18
    footer: int = 9
    axis_label: int = 11


@dataclass
class FontsConfig:
    """Configuracoes de fontes."""

    # Caminho relativo a assets/ ou caminho absoluto (vazio = usa fallback)
    file: str = ""
    fallback: str = "sans-serif"
    sizes: FontSizesConfig = field(default_factory=FontSizesConfig)


@dataclass
class FooterConfig:
    """Configuracoes de posicao e estilo do rodape."""

    x: float = 0.01
    y: float = 0.01
    color: str = "gray"


@dataclass
class TitleConfig:
    """Configuracoes de estilo do titulo."""

    padding: int = 20
    weight: str = "bold"


@dataclass
class LayoutConfig:
    """Configuracoes de layout do grafico."""

    figsize: tuple[float, float] = (10.0, 6.0)
    dpi: int = 300
    footer: FooterConfig = field(default_factory=FooterConfig)
    title: TitleConfig = field(default_factory=TitleConfig)


@dataclass
class LegendConfig:
    """Configuracoes de legenda."""

    alpha: float = 0.9
    frameon: bool = True


@dataclass
class LinesConfig:
    """Configuracoes de linhas."""

    main_width: float = 2.0
    overlay_width: float = 1.5
    reference_style: str = "--"
    legend: LegendConfig = field(default_factory=LegendConfig)


@dataclass
class FrequencyDetectionConfig:
    """Thresholds para deteccao de frequencia de dados."""

    monthly_threshold: int = 25
    annual_threshold: int = 300


@dataclass
class BarsConfig:
    """Configuracoes de graficos de barras."""

    width_default: float = 0.8
    width_monthly: int = 20
    width_annual: int = 300
    frequency_detection: FrequencyDetectionConfig = field(
        default_factory=FrequencyDetectionConfig
    )


@dataclass
class BandsConfig:
    """Configuracoes de bandas sombreadas."""

    alpha: float = 0.15


@dataclass
class MarkersConfig:
    """Configuracoes de marcadores (scatter, labels)."""

    scatter_size: int = 30
    label_offset_x: int = 5
    label_offset_y: int = 8


@dataclass
class CollisionConfig:
    """Configuracoes para deteccao de colisao de labels."""

    margin_px: int = 5
    guide_threshold_px: int = 30
    extra_padding_px: int = 15
    px_to_points_ratio: float = 0.75


@dataclass
class TransformsConfig:
    """Configuracoes para transformacoes de dados."""

    mom_periods: int = 1
    yoy_periods: int = 12
    trading_days_per_year: int = 252
    normalize_base: int = 100
    rolling_window: int = 12


@dataclass
class CurrencyConfig:
    """Prefixos de moeda."""

    BRL: str = "R$ "
    USD: str = "$ "


@dataclass
class LocaleConfig:
    """Configuracoes de locale para formatacao."""

    decimal: str = ","
    thousands: str = "."


@dataclass
class MagnitudeConfig:
    """Sufixos para notacao compacta."""

    suffixes: list[str] = field(
        default_factory=lambda: ["", "k", "M", "B", "T"]
    )


@dataclass
class FormattersConfig:
    """Configuracoes de formatadores de texto."""

    currency: CurrencyConfig = field(default_factory=CurrencyConfig)
    locale: LocaleConfig = field(default_factory=LocaleConfig)
    magnitude: MagnitudeConfig = field(default_factory=MagnitudeConfig)


@dataclass
class LabelsConfig:
    """Configuracoes de rotulos padrao."""

    ath: str = "ATH"
    atl: str = "ATL"
    moving_average_format: str = "MM{window}"


@dataclass
class PathsConfig:
    """Configuracoes de caminhos e diretorios."""

    charts_subdir: str = "charts"
    default_output_dir: str = "outputs"
    project_root_markers: list[str] = field(
        default_factory=lambda: [
            ".git",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            ".project-root",
        ]
    )
    output_conventions: list[str] = field(
        default_factory=lambda: [
            "outputs",
            "data/outputs",
            "output",
            "data/output",
        ]
    )


@dataclass
class ChartingConfig:
    """
    Configuracao principal da biblioteca de charting.

    Agrega todas as sub-configuracoes em uma unica estrutura tipada.
    Pode ser criada a partir de defaults ou carregada de arquivo TOML.

    Example:
        >>> from chartkit.settings import get_config
        >>> config = get_config()
        >>> print(config.colors.primary)
        '#00464D'
    """

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
