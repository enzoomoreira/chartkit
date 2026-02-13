# API Reference

Complete technical reference for chartkit.

---

## Pandas Accessor

### df.chartkit.plot()

```python
def plot(
    x: str | None = None,
    y: str | list[str] | None = None,
    *,
    kind: ChartKind = "line",
    title: str | None = None,
    units: UnitFormat | None = None,
    source: str | None = None,
    highlight: HighlightInput = False,
    metrics: str | list[str] | None = None,
    fill_between: tuple[str, str] | None = None,
    legend: bool | None = None,
    debug: bool = False,
    **kwargs,
) -> PlotResult
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x` | `str \| None` | `None` | Column for X-axis. If `None`, uses the index |
| `y` | `str \| list[str] \| None` | `None` | Column(s) for Y-axis. If `None`, uses numeric columns |
| `kind` | `ChartKind` | `"line"` | Chart type registered in `ChartRegistry` (e.g., `"line"`, `"bar"`, `"stacked_bar"`) |
| `title` | `str \| None` | `None` | Chart title |
| `units` | `UnitFormat \| None` | `None` | Y-axis formatting (see table below) |
| `source` | `str \| None` | `None` | Data source for footer. When `None`, uses `branding.default_source` as fallback |
| `highlight` | `HighlightInput` | `False` | Highlight mode(s). `True` / `'last'` = last value; `'max'` / `'min'` = extremes. Accepts list to combine modes (e.g., `['max', 'min']`) |
| `metrics` | `str \| list[str] \| None` | `None` | Metric(s) to apply (string or list) |
| `fill_between` | `tuple[str, str] \| None` | `None` | Tuple `(col1, col2)` to shade area between two columns |
| `legend` | `bool \| None` | `None` | Legend control. `None` = auto (shows with 2+ artists), `True` = force, `False` = suppress |
| `debug` | `bool` | `False` | Draw collision debug overlay (colored bboxes for obstacles, labels, and line paths) |
| `**kwargs` | - | - | Chart-specific parameters (e.g., `y_origin='auto'`) and extra matplotlib args |

#### Available Metrics

| Syntax | Description | Example |
|--------|-------------|---------|
| `"ath"` | All-Time High (line at historical maximum) | `metrics=["ath"]` |
| `"atl"` | All-Time Low (line at historical minimum) | `metrics=["atl"]` |
| `"ma:N"` | N-period moving average | `metrics=["ma:12"]` |
| `"hline:V"` | Horizontal line at value V | `metrics=["hline:3.0"]` |
| `"band:L:U"` | Shaded band between L and U | `metrics=["band:1.5:4.5"]` |
| `"target:V"` | Target line at value V | `metrics=["target:1000"]` |
| `"std_band:W:N"` | Band of N standard deviations with window W | `metrics=["std_band:20:2"]` |
| `"avg"` | Horizontal line at data mean | `metrics=["avg"]` |
| `"vband:D1:D2"` | Vertical band between dates D1 and D2 | `metrics=["vband:2020-03-01:2020-06-30"]` |

Metrics support custom labels via `|` syntax: `'ath|Maximum'`, `'ma:12@col|12M Average'`, `'hline:100|Target: Q1'`.

#### Types

```python
ChartKind = Literal["line", "bar", "stacked_bar"]
UnitFormat = Literal["BRL", "USD", "BRL_compact", "USD_compact", "%", "human", "points"]
HighlightMode = Literal["last", "max", "min", "all"]
HighlightInput = bool | HighlightMode | list[HighlightMode]
```

---

## PlotResult

Plot result with method chaining. The `plotter` field accepts any object satisfying the `Saveable` Protocol (either `ChartingPlotter` or composed chart plotter).

```python
class Saveable(Protocol):
    def save(self, path: str, dpi: int | None = None) -> None: ...

@dataclass
class PlotResult:
    fig: Figure
    ax: Axes
    plotter: Saveable
```

### Methods and Properties

| Member | Type | Return | Description |
|--------|------|--------|-------------|
| `save(path, dpi=None)` | method | `PlotResult` | Saves chart to file |
| `show()` | method | `PlotResult` | Displays interactive chart |
| `axes` | property | `Axes` | Access to matplotlib Axes |
| `figure` | property | `Figure` | Access to matplotlib Figure |

### Signatures

```python
def save(self, path: str, dpi: int | None = None) -> PlotResult
def show(self) -> PlotResult

@property
def axes(self) -> Axes

@property
def figure(self) -> Figure
```

---

## TransformAccessor

Chainable accessor for transformations. Each method returns a new `TransformAccessor`.

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `variation()` | `variation(horizon: str = "month", periods: int \| None = None, freq: str \| None = None) -> TransformAccessor` | Percentage variation by horizon (`'month'` or `'year'`, frequency auto-detection) |
| `accum()` | `accum(window: int \| None = None, freq: str \| None = None) -> TransformAccessor` | Accumulated via compound product in rolling window (fallback: `config.transforms.accum_window`) |
| `diff()` | `diff(periods: int = 1) -> TransformAccessor` | Absolute difference between periods (periods != 0; negative for forward diff) |
| `normalize()` | `normalize(base: int \| None = None, base_date: str \| None = None) -> TransformAccessor` | Normalize series (default: `config.transforms.normalize_base`) |
| `drawdown()` | `drawdown() -> TransformAccessor` | Percentage distance from historical peak |
| `zscore()` | `zscore(window: int \| None = None) -> TransformAccessor` | Statistical standardization (global or rolling, window >= 2) |
| `annualize()` | `annualize(periods: int \| None = None, freq: str \| None = None) -> TransformAccessor` | Annualize periodic rate via compound interest (frequency auto-detection) |
| `to_month_end()` | `to_month_end() -> TransformAccessor` | Normalize index to month-end (consolidates duplicates) |
| `layer()` | `layer(kind, x, y, *, units, highlight, metrics, fill_between, axis, **kwargs) -> Layer` | Create a Layer for `compose()` |
| `plot()` | `plot(**kwargs) -> PlotResult` | Finalize chain and plot |
| `df` | `@property -> pd.DataFrame` | Access to transformed DataFrame |

---

## Chart Composition

### compose()

```python
def compose(
    *layers: Layer,
    title: str | None = None,
    source: str | None = None,
    legend: bool | None = None,
    figsize: tuple[float, float] | None = None,
    debug: bool = False,
) -> PlotResult
```

Compose multiple layers into a single chart with optional dual axes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `*layers` | `Layer` | - | One or more Layer objects |
| `title` | `str \| None` | `None` | Chart title |
| `source` | `str \| None` | `None` | Data source for footer |
| `legend` | `bool \| None` | `None` | Legend control |
| `figsize` | `tuple[float, float] \| None` | `None` | Override figure size |
| `debug` | `bool` | `False` | Draw collision debug overlay |

Raises `ValidationError` if no layers are provided or all layers are on the right axis.

### Layer

```python
AxisSide = Literal["left", "right"]

@dataclass(frozen=True)
class Layer:
    df: pd.DataFrame
    kind: ChartKind = "line"
    x: str | None = None
    y: str | list[str] | None = None
    units: UnitFormat | None = None
    highlight: HighlightInput = False
    metrics: str | list[str] | None = None
    fill_between: tuple[str, str] | None = None
    axis: AxisSide = "left"
    kwargs: dict[str, Any] = field(default_factory=dict)
```

Create layers via `df.chartkit.layer()` or `df.chartkit.variation().layer()`. The `create_layer()` function validates eagerly (units, highlight, kind, axis) before constructing the Layer.

### df.chartkit.layer()

```python
def layer(
    kind: ChartKind = "line",
    x: str | None = None,
    y: str | list[str] | None = None,
    *,
    units: UnitFormat | None = None,
    highlight: HighlightInput = False,
    metrics: str | list[str] | None = None,
    fill_between: tuple[str, str] | None = None,
    axis: AxisSide = "left",
    **kwargs,
) -> Layer
```

Same parameters as `plot()` but without chart-level options (title, source, legend).

---

## Formatters (units)

| Value | Format | Example |
|-------|--------|---------|
| `"BRL"` | Brazilian Real | R$ 1.234,56 |
| `"USD"` | US Dollar | $1,234.56 |
| `"BRL_compact"` | Compact Real | R$ 1,2 mi |
| `"USD_compact"` | Compact Dollar | $1.2M |
| `"%"` | Percentage | 10,5% |
| `"points"` | Locale-aware integers | 1.234.567 |
| `"human"` | Compact notation | 1,2M |

Currency formatters use Babel. Locale configurable via `formatters.locale.babel_locale`.

---

## ChartRegistry

Pluggable chart type system via decorator.

### Register new type

```python
from chartkit.charts.registry import ChartRegistry

@ChartRegistry.register("scatter")
def plot_scatter(ax, x, y_data, highlight=None, **kwargs):
    ...
```

### Methods

| Method | Return | Description |
|--------|--------|-------------|
| `register(name)` | decorator | Registers function as chart type |
| `get(name)` | `ChartFunc` | Returns registered function |
| `available()` | `list[str]` | Lists registered names |

---

## ChartingPlotter

Advanced usage for full control.

### Constructor

```python
class ChartingPlotter:
    def __init__(self, df: pd.DataFrame) -> None
```

### Methods

```python
def plot(
    x: str | None = None,
    y: str | list[str] | None = None,
    *,
    kind: ChartKind = "line",
    title: str | None = None,
    units: UnitFormat | None = None,
    source: str | None = None,
    highlight: HighlightInput = False,
    metrics: str | list[str] | None = None,
    fill_between: tuple[str, str] | None = None,
    legend: bool | None = None,
    debug: bool = False,
    **kwargs,
) -> PlotResult

def save(self, path: str, dpi: int | None = None) -> None
```

---

## Configuration

### configure()

```python
def configure(
    config_path: Path | None = None,
    outputs_path: Path | None = None,
    assets_path: Path | None = None,
    **section_overrides,
) -> ConfigLoader
```

Section overrides:

```python
configure(branding={"company_name": "Company"})
configure(colors={"primary": "#FF0000"})
configure(layout={"figsize": [12.0, 8.0], "dpi": 150})
```

### get_config()

```python
def get_config() -> ChartingConfig
```

Returns pydantic BaseSettings with all settings.

### reset_config()

```python
def reset_config() -> ConfigLoader
```

Resets settings to defaults.

### configure_logging()

```python
def configure_logging(level: str = "DEBUG", sink: TextIO | None = None) -> int
```

Enables library logging (disabled by default). Repeated calls remove the previous handler before adding a new one, avoiding log duplication. Returns the added handler ID.

### disable_logging()

```python
def disable_logging() -> None
```

Disables library logging and removes all handlers added by `configure_logging()`. Reverts to initial state (logging disabled).

---

## ChartingConfig

Main configuration structure.

```python
class ChartingConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CHARTKIT_",
        env_nested_delimiter="__",
    )

    branding: BrandingConfig
    colors: ColorsConfig
    fonts: FontsConfig
    layout: LayoutConfig
    lines: LinesConfig
    bars: BarsConfig
    bands: BandsConfig
    markers: MarkersConfig
    collision: CollisionConfig
    transforms: TransformsConfig
    formatters: FormattersConfig
    labels: LabelsConfig
    legend: LegendConfig
    paths: PathsConfig
```

#### LegendConfig

| Field | Type | Default |
|-------|------|---------|
| `loc` | `str` | `"best"` |
| `alpha` | `float` | `0.9` |
| `frameon` | `bool` | `True` |

### Sub-configurations

#### BrandingConfig

| Field | Type | Default |
|-------|------|---------|
| `company_name` | `str` | `""` |
| `default_source` | `str` | `""` |
| `footer_format` | `str` | `"Fonte: {source}, {company_name}"` |
| `footer_format_no_source` | `str` | `"{company_name}"` |

#### ColorsConfig

| Field | Type | Default |
|-------|------|---------|
| `primary` | `str` | `"#00464D"` |
| `secondary` | `str` | `"#006B6B"` |
| `tertiary` | `str` | `"#008B8B"` |
| `quaternary` | `str` | `"#20B2AA"` |
| `quinary` | `str` | `"#5F9EA0"` |
| `senary` | `str` | `"#2E8B57"` |
| `text` | `str` | `"#00464D"` |
| `grid` | `str` | `"lightgray"` |
| `background` | `str` | `"white"` |
| `positive` | `str` | `"#00464D"` |
| `negative` | `str` | `"#8B0000"` |
| `moving_average` | `str` | `"#888888"` |

#### FontsConfig

| Field | Type | Default |
|-------|------|---------|
| `file` | `str` | `""` |
| `fallback` | `str` | `"sans-serif"` |
| `sizes` | `FontSizesConfig` | (see below) |

#### FontSizesConfig

| Field | Type | Default |
|-------|------|---------|
| `default` | `int` | `11` |
| `title` | `int` | `18` |
| `footer` | `int` | `9` |
| `axis_label` | `int` | `11` |

#### LayoutConfig

| Field | Type | Default |
|-------|------|---------|
| `figsize` | `tuple[float, float]` | `(10.0, 6.0)` |
| `dpi` | `int` | `300` |
| `base_style` | `str` | `"seaborn-v0_8-white"` |
| `grid` | `bool` | `False` |
| `spines` | `SpinesConfig` | (see below) |
| `footer` | `FooterConfig` | (see below) |
| `title` | `TitleConfig` | (see below) |
| `zorder` | `ZOrderConfig` | (see below) |

#### SpinesConfig

| Field | Type | Default |
|-------|------|---------|
| `top` | `bool` | `False` |
| `right` | `bool` | `False` |
| `left` | `bool` | `True` |
| `bottom` | `bool` | `True` |

#### FooterConfig

| Field | Type | Default |
|-------|------|---------|
| `y` | `float` | `0.01` |
| `color` | `str` | `"gray"` |

#### TitleConfig

| Field | Type | Default |
|-------|------|---------|
| `padding` | `int` | `20` |
| `weight` | `str` | `"bold"` |

#### ZOrderConfig

| Field | Type | Default |
|-------|------|---------|
| `bands` | `int` | `0` |
| `reference_lines` | `int` | `1` |
| `moving_average` | `int` | `2` |
| `data` | `int` | `3` |
| `markers` | `int` | `5` |

#### LinesConfig

| Field | Type | Default |
|-------|------|---------|
| `main_width` | `float` | `2.0` |
| `overlay_width` | `float` | `1.5` |
| `reference_style` | `str` | `"--"` |
| `target_style` | `str` | `"-."` |
| `moving_avg_min_periods` | `int` | `1` |

#### BarsConfig

| Field | Type | Default |
|-------|------|---------|
| `width_default` | `float` | `0.8` |
| `width_monthly` | `int` | `20` |
| `width_annual` | `int` | `300` |
| `auto_margin` | `float` | `0.1` |
| `warning_threshold` | `int` | `500` |
| `frequency_detection` | `FrequencyDetectionConfig` | (see below) |

#### FrequencyDetectionConfig

| Field | Type | Default |
|-------|------|---------|
| `monthly_threshold` | `int` | `25` |
| `annual_threshold` | `int` | `300` |

#### BandsConfig

| Field | Type | Default |
|-------|------|---------|
| `alpha` | `float` | `0.15` |

#### MarkersConfig

| Field | Type | Default |
|-------|------|---------|
| `scatter_size` | `int` | `30` |
| `font_weight` | `str` | `"bold"` |
| `label_offset_fraction` | `float` | `0.015` |

#### CollisionConfig

| Field | Type | Default |
|-------|------|---------|
| `movement` | `Literal["x", "y", "xy"]` | `"y"` |
| `obstacle_padding_px` | `float` | `8.0` |
| `label_padding_px` | `float` | `4.0` |
| `max_iterations` | `int` | `50` |
| `connector_threshold_px` | `float` | `30.0` |
| `connector_alpha` | `float` | `0.6` |
| `connector_style` | `str` | `"-"` |
| `connector_width` | `float` | `1.0` |

#### TransformsConfig

| Field | Type | Default |
|-------|------|---------|
| `normalize_base` | `PositiveInt` | `100` |
| `accum_window` | `PositiveInt` | `12` |

#### FormattersConfig

| Field | Type | Default |
|-------|------|---------|
| `locale` | `LocaleConfig` | (see below) |
| `magnitude` | `MagnitudeConfig` | (see below) |

#### LocaleConfig

| Field | Type | Default |
|-------|------|---------|
| `decimal` | `str` | `","` |
| `thousands` | `str` | `"."` |
| `babel_locale` | `str` | `"pt_BR"` |

#### MagnitudeConfig

| Field | Type | Default |
|-------|------|---------|
| `suffixes` | `list[str]` | `["", "k", "M", "B", "T"]` |

#### LabelsConfig

| Field | Type | Default |
|-------|------|---------|
| `ath` | `str` | `"ATH"` |
| `atl` | `str` | `"ATL"` |
| `avg` | `str` | `"AVG"` |
| `moving_average_format` | `str` | `"MM{window}"` |
| `target_format` | `str` | `"Meta: {value}"` |
| `std_band_format` | `str` | `"BB({window}, {num_std})"` |

#### PathsConfig

| Field | Type | Default |
|-------|------|---------|
| `charts_subdir` | `str` | `"charts"` |
| `outputs_dir` | `str` | `""` |
| `assets_dir` | `str` | `""` |

---

## Exceptions

| Class | Base | Description |
|-------|------|-------------|
| `ChartKitError` | `Exception` | Library base exception |
| `TransformError` | `ChartKitError` | Error during transform validation or execution |
| `ValidationError` | `ChartKitError`, `ValueError` | Parameter or input validation error |
| `RegistryError` | `ChartKitError`, `LookupError` | Registry lookup error (chart type, metric, style) |
| `StateError` | `ChartKitError`, `RuntimeError` | Invalid state operation error |

The new exceptions inherit from corresponding built-in types, maintaining compatibility with `except ValueError`, `except LookupError`, and `except RuntimeError`. Use `except ChartKitError` to catch all library errors.

`TransformError` is raised when:
- `drawdown()` receives data with non-positive values
- Auto-detection of frequency fails and no `periods=`/`freq=` was provided
- Detected frequency is not supported (with message listing valid frequencies)
- Mutually exclusive parameters (`periods` and `freq`) are passed simultaneously
- `normalize(base_date=...)` receives an invalid date

`ValidationError` is raised when:
- `plot()` receives an invalid mode in `highlight` (e.g., `"banana"` instead of `"last"`, `"max"` or `"min"`)
- `plot()` receives an invalid value in `units` (e.g., `"EUR"` instead of `"BRL"`)
- `y_origin` receives a value outside `"zero"` / `"auto"` in bar charts
- `diff(periods=0)` (returns all-zeros, almost certainly a user error)
- `zscore(window=1)` (std of 1 value is undefined)

`RegistryError` is raised when:
- `ChartRegistry.get()` receives an unregistered chart type
- `add_highlight()` receives a `style` not registered in `HIGHLIGHT_STYLES`

`StateError` is raised when:
- An operation requires state that has not been initialized

---

## Module Exports

```python
from chartkit import (
    # Configuration
    configure,
    configure_logging,
    disable_logging,
    get_config,
    reset_config,
    ChartingConfig,

    # Paths (lazy evaluation)
    CHARTS_PATH,
    OUTPUTS_PATH,
    ASSETS_PATH,

    # Collision API
    register_fixed,
    register_moveable,
    register_passive,

    # Composition
    AxisSide,
    Layer,
    compose,

    # Types
    ChartKind,
    HighlightInput,
    HighlightMode,
    UnitFormat,

    # Main classes
    ChartingAccessor,
    ChartingPlotter,
    ChartRegistry,
    PlotResult,
    TransformAccessor,
    MetricRegistry,
    theme,

    # Exceptions
    ChartKitError,
    TransformError,
    ValidationError,
    RegistryError,
    StateError,

    # Transforms (standalone functions)
    variation,
    accum,
    diff,
    normalize,
    drawdown,
    zscore,
    annualize,
    to_month_end,
)
```

### Path Functions

```python
from chartkit.settings import (
    get_outputs_path,   # -> Path
    get_charts_path,    # -> Path
    get_assets_path,    # -> Path
)
```
