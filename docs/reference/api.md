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
    legend: bool | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    xlim: AxisLimits | None = None,
    ylim: AxisLimits | None = None,
    grid: bool | None = None,
    tick_rotation: int | Literal["auto"] | None = None,
    tick_format: str | None = None,
    tick_freq: str | None = None,
    collision: bool = True,
    debug: bool = False,
    **kwargs,
) -> PlotResult
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x` | `str \| None` | `None` | Column for X-axis. If `None`, uses the index |
| `y` | `str \| list[str] \| None` | `None` | Column(s) for Y-axis. If `None`, uses numeric columns |
| `kind` | `ChartKind` | `"line"` | Chart type: any registered enhancer (`"bar"`, `"barh"`, `"area"`, `"hist"`, `"pie"`, `"stem"`, etc.) or valid matplotlib Axes method (`"scatter"`, `"step"`, etc.) |
| `title` | `str \| None` | `None` | Chart title |
| `units` | `UnitFormat \| None` | `None` | Y-axis formatting (see table below) |
| `source` | `str \| None` | `None` | Data source for footer. When `None`, uses `branding.default_source` as fallback |
| `highlight` | `HighlightInput` | `False` | Highlight mode(s). `True` / `'last'` = last value; `'max'` / `'min'` = extremes. Accepts list to combine modes (e.g., `['max', 'min']`) |
| `metrics` | `str \| list[str] \| None` | `None` | Metric(s) to apply (string or list) |
| `legend` | `bool \| None` | `None` | Legend control. `None` = auto (shows with 2+ artists), `True` = force, `False` = suppress |
| `xlabel` | `str \| None` | `None` | X-axis label |
| `ylabel` | `str \| None` | `None` | Y-axis label |
| `xlim` | `AxisLimits \| None` | `None` | X-axis limits as `(min, max)`. Accepts strings (`"2024-01-01"`, `"100"`), datetime, pd.Timestamp, numeric, or `None` per element |
| `ylim` | `AxisLimits \| None` | `None` | Y-axis limits as `(min, max)`. Accepts strings (`"100"`), datetime, pd.Timestamp, numeric, or `None` per element |
| `grid` | `bool \| None` | `None` | Grid override. `None` uses config, `True`/`False` enables/disables |
| `tick_rotation` | `int \| Literal["auto"] \| None` | `None` | X-axis tick label rotation. `"auto"` detects overlap and escalates to 90 degrees if the configured angle is insufficient; `int` forces angle. `None` uses config |
| `tick_format` | `str \| None` | `None` | Date format for X-axis ticks (e.g., `"%b/%Y"`). `None` uses config |
| `tick_freq` | `str \| None` | `None` | Tick frequency: `"day"`, `"week"`, `"month"`, `"quarter"`, `"semester"`, `"year"`. `None` uses config |
| `collision` | `bool` | `True` | Enable collision resolution engine. `False` skips all label collision processing |
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
| `"std_band:W:N"` | Rolling band of N std deviations with window W | `metrics=["std_band:20:2"]` |
| `"std_band:0:N"` | Full-series band of N std deviations (flat) | `metrics=["std_band:0:2"]` |
| `"std_band"` | Full-series band with default deviations (2) | `metrics=["std_band"]` |
| `"avg"` | Horizontal line at data mean | `metrics=["avg"]` |
| `"vband:D1:D2"` | Vertical band between dates D1 and D2 | `metrics=["vband:2020-03-01:2020-06-30"]` |

Metrics support custom labels via `|` syntax: `'ath|Maximum'`, `'ma:12@col|12M Average'`, `'hline:100|Target: Q1'`.

#### Types

```python
ChartKind = str  # any valid matplotlib Axes method or registered enhancer
UnitFormat = Literal["BRL", "USD", "BRL_compact", "USD_compact", "%", "human", "points", "x"]
TickFreq = Literal["day", "week", "month", "quarter", "semester", "year"]
HighlightMode = Literal["last", "max", "min", "all"]
HighlightInput = bool | HighlightMode | list[HighlightMode]
AxisValue = str | int | float | datetime | date | pd.Timestamp | None
AxisLimits = tuple[AxisValue, AxisValue]
```

`AxisLimits` accepts mixed types per element. String values are auto-coerced via `coerce_axis_limits()`: numeric strings (e.g., `"100"`) become `float`, date strings (e.g., `"2024-01-01"`) become `pd.Timestamp`.

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
| `despike()` | `despike(window: int = 21, threshold: float = 5.0, method: str = "median") -> TransformAccessor` | Remove aggressive data spikes via Hampel filter (window must be odd >= 3) |
| `resample()` | `resample(freq: str = "month", method: str = "last") -> TransformAccessor` | Downsample to target frequency (`'day'`/`'week'`/`'month'`/`'quarter'`/`'year'`; agg: `'last'`/`'first'`/`'mean'`/`'sum'`) |
| `layer()` | `layer(kind, x, y, *, units, highlight, metrics, axis, **kwargs) -> Layer` | Create a Layer for `compose()` |
| `plot()` | `plot(x, y, *, kind, title, units, source, highlight, metrics, legend, xlabel, ylabel, xlim, ylim, grid, tick_rotation, tick_format, tick_freq, collision, debug, **kwargs) -> PlotResult` | Finalize chain and plot (same parameters as `df.chartkit.plot()`) |
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
    xlabel: str | None = None,
    ylabel: str | None = None,
    xlim: AxisLimits | None = None,
    ylim: AxisLimits | None = None,
    grid: bool | None = None,
    tick_rotation: int | Literal["auto"] | None = None,
    tick_format: str | None = None,
    tick_freq: str | None = None,
    collision: bool = True,
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
| `xlabel` | `str \| None` | `None` | X-axis label |
| `ylabel` | `str \| None` | `None` | Y-axis label (applied to left axis) |
| `xlim` | `AxisLimits \| None` | `None` | X-axis limits as `(min, max)`. Accepts strings (`"2024-01-01"`, `"100"`), datetime, pd.Timestamp, numeric, or `None` per element |
| `ylim` | `AxisLimits \| None` | `None` | Y-axis limits as `(min, max)` (applied to left axis). Accepts strings (`"100"`), datetime, pd.Timestamp, numeric, or `None` per element |
| `grid` | `bool \| None` | `None` | Grid override. `None` uses config, `True`/`False` enables/disables |
| `tick_rotation` | `int \| Literal["auto"] \| None` | `None` | X-axis tick label rotation. `"auto"` detects overlap and escalates to 90 degrees if the configured angle is insufficient; `int` forces angle. `None` uses config |
| `tick_format` | `str \| None` | `None` | Date format for X-axis ticks (e.g., `"%b/%Y"`). `None` uses config |
| `tick_freq` | `str \| None` | `None` | Tick frequency: `"day"`, `"week"`, `"month"`, `"quarter"`, `"semester"`, `"year"`. `None` uses config |
| `collision` | `bool` | `True` | Enable collision resolution engine. `False` skips all label collision processing |
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
    axis: AxisSide = "left",
    **kwargs,
) -> Layer
```

Same parameters as `plot()` but limited to data and rendering options. Chart-level options (`title`, `source`, `legend`, `xlabel`, `ylabel`, `xlim`, `ylim`, `grid`, `tick_rotation`, `tick_format`, `tick_freq`, `collision`, `debug`) are passed to `compose()` instead.

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
| `"x"` | Multiplier | 12,3x |

Currency formatters use Babel. Locale configurable via `formatters.locale.babel_locale`.

---

## ChartRenderer

Generic chart renderer with enhancer-based extensibility. Simple chart types (scatter, step, etc.) work automatically via `ax.{kind}()`. Complex types that need custom logic are handled by registered enhancers.

### Registered Enhancers

| Enhancer | Kind | Module |
|----------|------|--------|
| `bar` | `"bar"` | `charts/enhancers/bar.py` |
| `barh` | `"barh"` | `charts/enhancers/bar.py` |
| `stacked_bar` | `"stacked_bar"` | `charts/enhancers/stacked_bar.py` |
| `fill_between` | `"area"` / `"fill_between"` | `charts/enhancers/area.py` |
| `hist` | `"hist"` | `charts/enhancers/hist.py` |
| `pie` | `"pie"` | `charts/enhancers/pie.py` |
| `stackplot` | `"stackplot"` | `charts/enhancers/stackplot.py` |
| `stem` | `"stem"` | `charts/enhancers/stem.py` |
| `stairs` | `"stairs"` | `charts/enhancers/stairs.py` |
| `boxplot` | `"boxplot"` | `charts/enhancers/statistical.py` |
| `violinplot` | `"violinplot"` | `charts/enhancers/statistical.py` |
| `ecdf` | `"ecdf"` | `charts/enhancers/ecdf.py` |
| `eventplot` | `"eventplot"` | `charts/enhancers/eventplot.py` |

### Aliases

| Alias | Resolves To |
|-------|-------------|
| `"line"` | `"plot"` |
| `"area"` | `"fill_between"` |

### Unsupported Kinds

These chart kinds require 2D grid or vector field data and are explicitly blocked:

`imshow`, `contour`, `contourf`, `pcolormesh`, `quiver`, `streamplot`, `barbs`, `spy`

### Generic Rendering

Any valid matplotlib Axes method not listed above works automatically:

```python
df.chartkit.plot(kind='scatter', s=50, alpha=0.7)
df.chartkit.plot(kind='step', where='mid')
```

### Post-Render Collision Registration

After rendering, `ChartRenderer` automatically registers new artists for collision detection:
- New `Line2D` artists -> `register_artist_obstacle(filled=False, colocate=True)`
- New `PathCollection` (scatter) -> `register_artist_obstacle(filled=True)`
- Other new collections are left unregistered for auto-detection by `_collect_obstacles()`

### Register a Custom Enhancer

```python
from chartkit.charts.renderer import ChartRenderer

@ChartRenderer.register_enhancer("my_chart")
def plot_my_chart(ax, x, y_data, highlight, **kwargs):
    ...
```

### Methods

| Method | Return | Description |
|--------|--------|-------------|
| `register_enhancer(name)` | decorator | Registers specialized chart handler |
| `render(ax, kind, x, y_data, highlight, **kwargs)` | `None` | Renders chart (enhancer or generic) |
| `validate_kind(kind)` | `None` | Validates kind (rejects unsupported, private, and non-existent methods) |
| `available()` | `list[str]` | Lists registered enhancer names |

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
    legend: bool | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    xlim: AxisLimits | None = None,
    ylim: AxisLimits | None = None,
    grid: bool | None = None,
    tick_rotation: int | Literal["auto"] | None = None,
    tick_format: str | None = None,
    tick_freq: str | None = None,
    collision: bool = True,
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
    ticks: TicksConfig
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
| `grid` | `GridConfig` | (see below) |
| `spines` | `SpinesConfig` | (see below) |
| `footer` | `FooterConfig` | (see below) |
| `title` | `TitleConfig` | (see below) |
| `zorder` | `ZOrderConfig` | (see below) |

#### GridConfig

| Field | Type | Default |
|-------|------|---------|
| `enabled` | `bool` | `False` |
| `alpha` | `float` | `0.3` |
| `color` | `str` | `"lightgray"` |
| `linestyle` | `str` | `"-"` |
| `axis` | `Literal["x", "y", "both"]` | `"both"` |

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
| `label_padding_px` | `float` | `2.0` |
| `max_iterations` | `int` | `50` |
| `candidate_distances` | `tuple[float, ...]` | `(1.0, 1.5, 2.0)` |
| `edge_margin_factor` | `float` | `1.0` |
| `connector_threshold_px` | `float` | `30.0` |
| `connector_alpha` | `float` | `0.6` |
| `connector_style` | `str` | `"-"` |
| `connector_width` | `float` | `1.0` |

#### TicksConfig

| Field | Type | Default |
|-------|------|---------|
| `rotation` | `int \| Literal["auto"]` | `"auto"` |
| `auto_rotation_angle` | `int` | `45` |
| `date_format` | `str \| None` | `None` |
| `date_freq` | `str \| None` | `None` |

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
| `std_band_format` | `str` | `"BB({window}, {deviations})"` |
| `std_band_full_format` | `str` | `"DP({deviations})"` |

Frequency-aware metrics (`ma`, `std_band`) support a `{freq}` placeholder in their format strings. The placeholder is replaced with a short display label for the detected data frequency (e.g., `"M"` for monthly, `"T"` for quarterly, `"A"` for annual). When the frequency cannot be detected, `{freq}` resolves to an empty string. This is opt-in: add `{freq}` to the format string in your TOML config (e.g., `moving_average_format = "MM{window}{freq}"`).

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
- `plot()` or `layer()` receives a `kind` that is not a valid matplotlib Axes method or registered enhancer
- `tick_freq` receives an invalid value (not one of `TickFreq` options)
- `tick_rotation` receives a value that is not `int` or `"auto"`
- `diff(periods=0)` (returns all-zeros, almost certainly a user error)
- `zscore(window=1)` (std of 1 value is undefined)

`RegistryError` is raised when:
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
    register_artist_obstacle,
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
    ChartRenderer,
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
    despike,
    resample,
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
