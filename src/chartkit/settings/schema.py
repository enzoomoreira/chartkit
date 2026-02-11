"""Schema de configuracao com pydantic models."""

from typing import Any, ClassVar

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

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


class BrandingConfig(BaseModel):
    company_name: str = ""
    default_source: str = ""
    footer_format: str = "Fonte: {source}, {company_name}"
    footer_format_no_source: str = "{company_name}"


class ColorsConfig(BaseModel):
    primary: str = "#00464D"
    secondary: str = "#006B6B"
    tertiary: str = "#008B8B"
    quaternary: str = "#20B2AA"
    quinary: str = "#5F9EA0"
    senary: str = "#2E8B57"

    text: str = "#00464D"
    grid: str = "lightgray"
    background: str = "white"
    positive: str = "#00464D"
    negative: str = "#8B0000"

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


class FontSizesConfig(BaseModel):
    default: int = 11
    title: int = 18
    footer: int = 9
    axis_label: int = 11


class FontsConfig(BaseModel):
    file: str = ""
    fallback: str = "sans-serif"
    assets_path: str = ""
    sizes: FontSizesConfig = Field(default_factory=FontSizesConfig)


class FooterConfig(BaseModel):
    y: float = 0.01
    color: str = "gray"


class TitleConfig(BaseModel):
    padding: int = 20
    weight: str = "bold"


class ZOrderConfig(BaseModel):
    """Ordem de camadas: bands(0) < reference_lines(1) < moving_average(2) < data(3) < markers(5)."""

    bands: int = 0
    reference_lines: int = 1
    moving_average: int = 2
    data: int = 3
    markers: int = 5


class LayoutConfig(BaseModel):
    figsize: tuple[float, float] = (10.0, 6.0)
    dpi: int = 300
    footer: FooterConfig = Field(default_factory=FooterConfig)
    title: TitleConfig = Field(default_factory=TitleConfig)
    zorder: ZOrderConfig = Field(default_factory=ZOrderConfig)


class LegendConfig(BaseModel):
    loc: str = "best"
    alpha: float = 0.9
    frameon: bool = True


class LinesConfig(BaseModel):
    main_width: float = 2.0
    overlay_width: float = 1.5
    reference_style: str = "--"
    moving_avg_min_periods: int = 1


class FrequencyDetectionConfig(BaseModel):
    monthly_threshold: int = 25
    annual_threshold: int = 300


class BarsConfig(BaseModel):
    width_default: float = 0.8
    width_monthly: int = 20
    width_annual: int = 300
    auto_margin: float = 0.1
    frequency_detection: FrequencyDetectionConfig = Field(
        default_factory=FrequencyDetectionConfig
    )


class BandsConfig(BaseModel):
    alpha: float = 0.15


class MarkersConfig(BaseModel):
    scatter_size: int = 30


class CollisionConfig(BaseModel):
    movement: str = "y"
    obstacle_padding_px: float = 8.0
    label_padding_px: float = 4.0
    max_iterations: int = 50
    connector_threshold_px: float = 30.0
    connector_alpha: float = 0.6
    connector_style: str = "-"


class TransformsConfig(BaseModel):
    trading_days_per_year: int = 252
    normalize_base: int = 100
    rolling_window: int = 12


class LocaleConfig(BaseModel):
    decimal: str = ","
    thousands: str = "."
    babel_locale: str = "pt_BR"


class MagnitudeConfig(BaseModel):
    suffixes: list[str] = Field(default_factory=lambda: ["", "k", "M", "B", "T"])


class FormattersConfig(BaseModel):
    locale: LocaleConfig = Field(default_factory=LocaleConfig)
    magnitude: MagnitudeConfig = Field(default_factory=MagnitudeConfig)


class LabelsConfig(BaseModel):
    ath: str = "ATH"
    atl: str = "ATL"
    avg: str = "AVG"
    moving_average_format: str = "MM{window}"


class PathsConfig(BaseModel):
    charts_subdir: str = "charts"
    outputs_dir: str = ""
    assets_dir: str = ""


class _DictSource(PydanticBaseSettingsSource):
    """Source customizado que recebe um dict pre-mergeado de TOML files."""

    def __init__(self, settings_cls: type[BaseSettings], data: dict) -> None:
        super().__init__(settings_cls)
        self._data = data

    def get_field_value(
        self, field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        val = self._data.get(field_name)
        return val, field_name, False

    def __call__(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for field_name, field in self.settings_cls.model_fields.items():
            val = self._data.get(field_name)
            if val is not None:
                d[field_name] = val
        return d


class ChartingConfig(BaseSettings):
    """Configuracao principal que agrega todas as sub-configuracoes."""

    model_config = SettingsConfigDict(
        env_prefix="CHARTKIT_",
        env_nested_delimiter="__",
    )

    _toml_data: ClassVar[dict] = {}

    branding: BrandingConfig = Field(default_factory=BrandingConfig)
    colors: ColorsConfig = Field(default_factory=ColorsConfig)
    fonts: FontsConfig = Field(default_factory=FontsConfig)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    lines: LinesConfig = Field(default_factory=LinesConfig)
    bars: BarsConfig = Field(default_factory=BarsConfig)
    bands: BandsConfig = Field(default_factory=BandsConfig)
    markers: MarkersConfig = Field(default_factory=MarkersConfig)
    collision: CollisionConfig = Field(default_factory=CollisionConfig)
    transforms: TransformsConfig = Field(default_factory=TransformsConfig)
    formatters: FormattersConfig = Field(default_factory=FormattersConfig)
    labels: LabelsConfig = Field(default_factory=LabelsConfig)
    legend: LegendConfig = Field(default_factory=LegendConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        sources: list[PydanticBaseSettingsSource] = [init_settings, env_settings]
        if cls._toml_data:
            sources.append(_DictSource(settings_cls, cls._toml_data))
        return tuple(sources)
