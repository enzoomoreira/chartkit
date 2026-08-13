"""Configuration schema with pydantic models."""

from typing import Any, Literal

from pydantic import BaseModel, Field, PositiveInt
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
    "SpinesConfig",
    "ZOrderConfig",
    "GridConfig",
    "LayoutConfig",
    "LegendConfig",
    "LinesConfig",
    "BarsConfig",
    "BandsConfig",
    "FillsConfig",
    "MarkersConfig",
    "CollisionConfig",
    "TicksConfig",
    "TransformsConfig",
    "LocaleConfig",
    "MagnitudeConfig",
    "FormattersConfig",
    "LabelsConfig",
    "PathsConfig",
    "ChartingConfig",
]


class BrandingConfig(BaseModel):
    """Company branding for chart footers.

    Attributes:
        company_name: Displayed in the footer.
        default_source: Default data source when ``source`` is not provided.
        footer_format: Template with ``{source}`` and ``{company_name}`` placeholders.
        footer_format_no_source: Template used when ``source`` is empty.
    """

    company_name: str = ""
    default_source: str = ""
    footer_format: str = "Fonte: {source}, {company_name}"
    footer_format_no_source: str = "{company_name}"


class ColorsConfig(BaseModel):
    """Color palette. First 6 colors form the series cycle.

    The cycle separates by hue, not by lightness. Six shades of one teal --
    which is what this was -- is a sequential palette doing a categorical job:
    neighbouring series landed 12.9 CIELAB units apart, below the ~25 at which
    two colours stop reading as one. The dark teal anchors the set; the rest
    are copper, steel blue, olive, wine and muted purple, no pair closer than
    26.4.

    Attributes:
        positive: Color for positive values in diverging charts.
        negative: Color for negative values in diverging charts.
        moving_average: Color for moving average overlay lines.
    """

    primary: str = "#00464D"
    secondary: str = "#B5651D"
    tertiary: str = "#4C7FA8"
    quaternary: str = "#7A9A3B"
    quinary: str = "#8C4A5F"
    senary: str = "#6B5B95"

    text: str = "#00464D"
    grid: str = "lightgray"
    background: str = "white"
    positive: str = "#00464D"
    negative: str = "#8B0000"

    moving_average: str = "#888888"

    def cycle(self) -> list[str]:
        """Return color gradient list for multiple series."""
        return [
            self.primary,
            self.secondary,
            self.tertiary,
            self.quaternary,
            self.quinary,
            self.senary,
        ]


class FontSizesConfig(BaseModel):
    """Font sizes in points for chart elements."""

    default: int = 11
    title: int = 18
    footer: int = 9
    axis_label: int = 11


class FontsConfig(BaseModel):
    """Font configuration.

    Attributes:
        file: Path to a ``.ttf``/``.otf`` font file. Empty uses matplotlib default.
        fallback: Fallback font family when ``file`` is not found.
    """

    file: str = ""
    fallback: str = "sans-serif"
    sizes: FontSizesConfig = Field(default_factory=FontSizesConfig)


class FooterConfig(BaseModel):
    """Footer positioning and style.

    Attributes:
        y: Vertical position in figure coordinates (0=bottom, 1=top).
    """

    y: float = 0.01
    color: str = "gray"


class TitleConfig(BaseModel):
    """Title positioning and style."""

    padding: int = 20
    weight: str = "bold"


class SpinesConfig(BaseModel):
    """Chart border visibility control."""

    top: bool = False
    right: bool = False
    left: bool = True
    bottom: bool = True


class ZOrderConfig(BaseModel):
    """Layer order: bands(0) < reference_lines(1) < moving_average(2) < data(3) < markers(5)."""

    bands: int = 0
    reference_lines: int = 1
    moving_average: int = 2
    data: int = 3
    markers: int = 5


class GridConfig(BaseModel):
    """Grid line configuration.

    Attributes:
        axis: Which axes show grid lines (``"x"``, ``"y"``, or ``"both"``).
    """

    enabled: bool = False
    alpha: float = 0.3
    color: str = "lightgray"
    linestyle: str = "-"
    axis: Literal["x", "y", "both"] = "both"


class LayoutConfig(BaseModel):
    """Figure layout and sub-configurations.

    Attributes:
        figsize: Default figure size ``(width, height)`` in inches.
        dpi: Resolution for saved figures.
        base_style: Matplotlib style applied before custom rcParams.
        save_bbox: Bounding box mode passed to ``savefig``. ``"tight"``
            crops to the drawn content; ``"standard"`` keeps the figure at
            exactly ``figsize``, which is what a fixed report template needs.
            Cropping also discards the bottom margin that tick rotation
            reserves for the footer.
    """

    figsize: tuple[float, float] = (10.0, 6.0)
    dpi: int = 300
    base_style: str = "seaborn-v0_8-white"
    save_bbox: Literal["tight", "standard"] = "tight"
    grid: GridConfig = Field(default_factory=GridConfig)
    spines: SpinesConfig = Field(default_factory=SpinesConfig)
    footer: FooterConfig = Field(default_factory=FooterConfig)
    title: TitleConfig = Field(default_factory=TitleConfig)
    zorder: ZOrderConfig = Field(default_factory=ZOrderConfig)


class LegendConfig(BaseModel):
    """Legend appearance.

    Attributes:
        loc: Matplotlib legend location string (e.g. ``"best"``, ``"upper right"``).
    """

    loc: str = "best"
    alpha: float = 0.9
    frameon: bool = True


class TicksConfig(BaseModel):
    """X-axis tick configuration.

    Attributes:
        rotation: Default tick rotation. ``"auto"`` detects overlap.
        auto_rotation_angle: Angle used when ``"auto"`` detects overlap.
        min_gap_px: Separation ``"auto"`` demands between neighbouring labels
            before it leaves them horizontal. The default is the width of a
            space at the default label size: any closer and two labels read as
            one word. ``0`` restores strict-intersection detection.
        date_format: Default date format (e.g. ``"%b/%Y"``). ``None`` auto-selects.
        date_freq: Default tick frequency. ``None`` auto-infers from data.
    """

    rotation: int | Literal["auto"] = "auto"
    auto_rotation_angle: int = Field(default=45, gt=0, le=90)
    min_gap_px: float = Field(default=4.0, ge=0.0)
    date_format: str | None = None
    date_freq: Literal["day", "week", "month", "quarter", "semester", "year"] | None = (
        None
    )


class LinesConfig(BaseModel):
    """Line styling for data and overlays.

    Attributes:
        main_width: Width for primary data lines.
        overlay_width: Width for overlay lines (moving average, reference).
        reference_style: Linestyle for reference lines (ATH, ATL).
        target_style: Linestyle for target lines.
        moving_avg_min_periods: Observations required before a rolling overlay
            produces a value. ``None`` demands the full window, so an ``ma:12``
            starts on its twelfth point and the line means what its label says.
            Set an explicit value to draw earlier from a partial sample.
    """

    main_width: float = 2.0
    overlay_width: float = 1.5
    reference_style: str = "--"
    target_style: str = "-."
    moving_avg_min_periods: int | None = Field(default=None, ge=1)


class BarsConfig(BaseModel):
    """Bar chart configuration.

    Attributes:
        width_fraction: Bar thickness as a fraction of the space one bar owns --
            one unit on a categorical axis, the median gap between dates on a
            temporal one. ``1.0`` makes neighbouring bars touch.
        auto_margin: X-axis margin fraction added around bars.
        warning_threshold: Log warning if bar count exceeds this.
    """

    width_fraction: float = Field(default=0.8, gt=0.0, le=1.0)
    auto_margin: float = 0.1
    warning_threshold: int = 500


class BandsConfig(BaseModel):
    """Shaded band overlay configuration."""

    alpha: float = 0.15


class FillsConfig(BaseModel):
    """Opacity of filled chart bodies.

    Attributes:
        area_alpha: Fill opacity for ``kind='area'``.
        violin_alpha: Body opacity for ``kind='violinplot'``.
    """

    area_alpha: float = Field(default=0.3, ge=0.0, le=1.0)
    violin_alpha: float = Field(default=0.7, ge=0.0, le=1.0)


class MarkersConfig(BaseModel):
    """Data point highlight marker configuration.

    Attributes:
        label_offset_fraction: Vertical offset as fraction of Y range.
    """

    scatter_size: int = 30
    font_weight: str = "bold"
    label_offset_fraction: float = 0.015


class CollisionConfig(BaseModel):
    """Label collision resolution engine configuration.

    Attributes:
        movement: Allowed movement axes (``"x"``, ``"y"``, or ``"xy"``).
        obstacle_padding_px: Padding around obstacles in pixels.
        label_padding_px: Padding around labels in pixels.
        max_iterations: Maximum solver iterations.
        candidate_distances: Multipliers (in label heights) for proactive
            candidate generation in 8 cardinal directions.
        edge_margin_factor: Edge margin as fraction of label height.
            Labels closer than this to the axes border receive a penalty.
        connector_threshold_px: Distance threshold to draw a connector line.
    """

    movement: Literal["x", "y", "xy"] = "y"
    obstacle_padding_px: float = 8.0
    label_padding_px: float = 2.0
    max_iterations: int = 50
    candidate_distances: tuple[float, ...] = (1.0, 1.5, 2.0)
    edge_margin_factor: float = 1.0
    connector_threshold_px: float = 30.0
    connector_alpha: float = 0.6
    connector_style: str = "-"
    connector_width: float = 1.0


class TransformsConfig(BaseModel):
    """Default parameters for transform functions.

    Attributes:
        normalize_base: Default base value for ``normalize()``.
        accum_window: Default rolling window for ``accum()`` when auto-detect fails.
    """

    normalize_base: PositiveInt = 100
    accum_window: PositiveInt = 12


class LocaleConfig(BaseModel):
    """Number and date formatting locale.

    Attributes:
        babel_locale: Babel locale (ISO 639 + ISO 3166) for currency amounts and
            for the month and weekday names an X-axis ``tick_format`` asks for.
    """

    decimal: str = ","
    thousands: str = "."
    babel_locale: str = "pt_BR"


class MagnitudeConfig(BaseModel):
    """Suffixes for human-readable number formatting (1k, 1M, 1B, 1T)."""

    # The formatter walks this list by magnitude and indexes the last entry as
    # its ceiling, so an empty list is an IndexError waiting for a big number.
    suffixes: list[str] = Field(
        default_factory=lambda: ["", "k", "M", "B", "T"], min_length=1
    )


class FormattersConfig(BaseModel):
    """Y-axis formatter sub-configurations."""

    locale: LocaleConfig = Field(default_factory=LocaleConfig)
    magnitude: MagnitudeConfig = Field(default_factory=MagnitudeConfig)


class LabelsConfig(BaseModel):
    """Default label text for metrics and overlays.

    Format strings use ``{param}`` placeholders filled at render time.
    Available placeholders for frequency-aware metrics:
    ``{freq}`` -- short display label for the detected data frequency
    (e.g. ``"M"`` for monthly, ``"T"`` for quarterly). Empty string when
    frequency is unknown. Opt-in: add ``{freq}`` to the format string
    in your TOML config (e.g. ``moving_average_format = "MM{window}{freq}"``).
    """

    ath: str = "ATH"
    atl: str = "ATL"
    avg: str = "AVG"
    moving_average_format: str = "MM{window}"
    target_format: str = "Meta: {value}"
    std_band_format: str = "BB({window}, {deviations})"
    std_band_full_format: str = "DP({deviations})"


class PathsConfig(BaseModel):
    """Directory paths for file I/O.

    Attributes:
        charts_subdir: Subdirectory under ``outputs_dir`` for saved charts.
        outputs_dir: Explicit outputs directory. Empty uses auto-discovery.
        assets_dir: Explicit assets directory. Empty uses auto-discovery.
    """

    charts_subdir: str = "charts"
    outputs_dir: str = ""
    assets_dir: str = ""


# Init kwarg carrying the merged TOML payload from ConfigLoader to the
# settings sources. Consumed in settings_customise_sources, so it never
# reaches field validation.
TOML_DATA_KWARG = "_toml_data"


class _DictSource(PydanticBaseSettingsSource):
    """Custom source that receives a pre-merged dict from TOML files."""

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
        for field_name in self.settings_cls.model_fields:
            val = self._data.get(field_name)
            if val is not None:
                d[field_name] = val
        return d


class ChartingConfig(BaseSettings):
    """Main configuration that aggregates all sub-configurations."""

    model_config = SettingsConfigDict(
        env_prefix="CHARTKIT_",
        env_nested_delimiter="__",
    )

    branding: BrandingConfig = Field(default_factory=BrandingConfig)
    colors: ColorsConfig = Field(default_factory=ColorsConfig)
    fonts: FontsConfig = Field(default_factory=FontsConfig)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    lines: LinesConfig = Field(default_factory=LinesConfig)
    bars: BarsConfig = Field(default_factory=BarsConfig)
    bands: BandsConfig = Field(default_factory=BandsConfig)
    fills: FillsConfig = Field(default_factory=FillsConfig)
    markers: MarkersConfig = Field(default_factory=MarkersConfig)
    collision: CollisionConfig = Field(default_factory=CollisionConfig)
    transforms: TransformsConfig = Field(default_factory=TransformsConfig)
    formatters: FormattersConfig = Field(default_factory=FormattersConfig)
    labels: LabelsConfig = Field(default_factory=LabelsConfig)
    legend: LegendConfig = Field(default_factory=LegendConfig)
    ticks: TicksConfig = Field(default_factory=TicksConfig)
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
        # The merged TOML arrives as an init kwarg rather than class state: a
        # ClassVar is shared by every loader and every thread, so two configs
        # being built at once would read each other's files.
        toml_data: dict[str, Any] = {}
        init_kwargs = getattr(init_settings, "init_kwargs", None)
        if isinstance(init_kwargs, dict):
            toml_data = init_kwargs.pop(TOML_DATA_KWARG, None) or {}

        sources: list[PydanticBaseSettingsSource] = [init_settings, env_settings]
        if toml_data:
            sources.append(_DictSource(settings_cls, toml_data))
        return tuple(sources)
