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
    decimals: int | None = None,
    source: str | None = None,
    highlight: HighlightInput = False,
    metrics: str | list[str] | None = None,
    legend: bool | None = None,
    figsize: tuple[float, float] | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    xlim: AxisLimits | None = None,
    ylim: AxisLimits | None = None,
    grid: bool | None = None,
    tick_rotation: int | Literal["auto"] | None = None,
    tick_format: str | None = None,
    tick_freq: TickFreq | None = None,
    collision: bool = True,
    debug: bool = False,
    **kwargs: Any,
) -> PlotResult
```

`ChartingAccessor.plot`, `TransformAccessor.plot` and `ChartingPlotter.plot` share this
signature exactly -- parameter names, order, defaults and annotations. `tests/test_api_parity.py`
enforces it, and also asserts that every parameter is actually forwarded to the engine rather
than accepted and dropped.

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x` | `str \| None` | `None` | Column for X-axis. If `None`, uses the index |
| `y` | `str \| list[str] \| None` | `None` | Column(s) for Y-axis. If `None`, uses numeric columns |
| `kind` | `ChartKind` | `"line"` | Chart type. Must be one of `ChartRenderer.available()`; anything else raises `ValidationError` |
| `title` | `str \| None` | `None` | Chart title |
| `units` | `UnitFormat \| None` | `None` | Y-axis formatting (see table below) |
| `decimals` | `int \| None` | `None` | Decimal places for axis tick labels and highlight labels, overriding the formatter default. Ignored by `"BRL"` / `"USD"` (Babel derives the digit count from the currency) and when `units` is `None` |
| `source` | `str \| None` | `None` | Data source for footer. When `None`, uses `branding.default_source` as fallback |
| `highlight` | `HighlightInput` | `False` | Highlight mode(s). `True` / `'last'` = last value; `'max'` / `'min'` = extremes. Accepts list to combine modes (e.g., `['max', 'min']`) |
| `metrics` | `str \| list[str] \| None` | `None` | Metric(s) to apply (string or list) |
| `legend` | `bool \| None` | `None` | Legend control. `None` = auto (shows with 2+ artists), `True` = force, `False` = suppress |
| `figsize` | `tuple[float, float] \| None` | `None` | Figure size `(width, height)` in inches. `None` uses `layout.figsize` from config |
| `xlabel` | `str \| None` | `None` | X-axis label |
| `ylabel` | `str \| None` | `None` | Y-axis label |
| `xlim` | `AxisLimits \| None` | `None` | X-axis limits as `(min, max)`. Accepts strings (`"2024-01-01"`, `"100"`), datetime, pd.Timestamp, numeric, or `None` per element |
| `ylim` | `AxisLimits \| None` | `None` | Y-axis limits as `(min, max)`. Accepts strings (`"100"`), datetime, pd.Timestamp, numeric, or `None` per element |
| `grid` | `bool \| None` | `None` | Grid override. `None` uses config, `True`/`False` enables/disables |
| `tick_rotation` | `int \| Literal["auto"] \| None` | `None` | X-axis tick label rotation. `"auto"` detects overlap and escalates to 90 degrees if the configured angle is insufficient; `int` forces angle. `None` uses config |
| `tick_format` | `str \| None` | `None` | Date format for X-axis ticks (e.g., `"%b/%Y"`). `None` uses config |
| `tick_freq` | `TickFreq \| None` | `None` | Tick frequency: `"day"`, `"week"`, `"month"`, `"quarter"`, `"semester"`, `"year"`. `None` uses config |
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
# The Literal arm drives editor autocomplete; the `| str` arm keeps the type open
# for kinds added via ChartRenderer.register_enhancer().
ChartKind = Literal[
    "area", "bar", "barh", "boxplot", "ecdf", "errorbar", "eventplot", "fill",
    "fill_between", "fill_betweenx", "hist", "line", "loglog", "pie", "plot",
    "scatter", "semilogx", "semilogy", "stacked_bar", "stackplot", "stairs",
    "stem", "step", "violinplot",
] | str
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

Plot result with method chaining. Holds the figure it describes, and `save()` writes
that figure -- both `plot()` and `compose()` return the same shape.

```python
@dataclass
class PlotResult:
    fig: Figure
    ax: Axes
```

### Methods and Properties

| Member | Type | Return | Description |
|--------|------|--------|-------------|
| `save(path, dpi=None)` | method | `PlotResult` | Saves chart to file |
| `show()` | method | `PlotResult` | Displays interactive chart (hands the figure to pyplot) |
| `close()` | method | `None` | Releases the figure and its artists |
| `describe(geometry=False)` | method | `dict` | Structural description of the rendered chart |
| `explain()` | method | `str` | Same information as text, for reading in a terminal |
| `axes` | property | `Axes` | Access to matplotlib Axes |
| `figure` | property | `Figure` | Access to matplotlib Figure |

### Inspecting a Chart

`describe()` reports what was rendered without producing an image: series and
their points, colours, line styles, patches, texts, legend entries, axis limits
and tick labels. Every Axes in the figure is covered, so a chart composed with
`compose()` reports its right-hand axis as well.

```python
result = df.chartkit.plot(kind="bar", units="%")

result.describe()["axes"][0]["lines"][0]["color"]   # '#00464d'
print(result.explain())                             # human-readable dump
```

Two fields exist because matplotlib keeps the information away from the artist
you would expect to hold it:

- `containers` names each group of patches. A bar chart marks its rectangles
  `_nolegend_` and puts the series name on the `BarContainer`, so a
  single-series bar chart -- which draws no legend -- carries its name nowhere
  else.
- `x_offset` / `y_offset` report the common factor the tick formatter pulled
  out into a corner annotation. Without `units`, an axis running in billions
  draws ticks reading `8.395` to `8.403` alongside a `1e9` marker; reading the
  ticks alone understates it by that factor. The currency, percentage and date
  formatters produce no offset and report `""`.

```python
described = df.chartkit.plot(kind="bar").describe()["axes"][0]

[group["label"] for group in described["containers"]]   # ['revenue']
described["y_offset"]                                   # '1e9'
```

The description is reported in data coordinates, so it does not change when the
same chart is drawn at a different `figsize` or `dpi`. That makes it safe to
compare against a stored baseline, which is how the render snapshots in
`tests/visual/` work.

`geometry=True` adds an `overlaps` entry listing pairs of labels whose drawn
extents intersect -- the direct way to check that the collision engine placed
every label readably:

```python
assert result.describe(geometry=True)["overlaps"] == []
```

Geometry is measured in pixels and depends on font rasterisation, so use it for
inspection rather than as a baseline. The same caveat applies to the `position`
of any label the collision engine moved, even at the default detail level.

### Figure Lifecycle

Charts are created outside `pyplot`, so the figure is released as soon as the
`PlotResult` goes out of scope -- there is no global registry holding it. Call
`close()` to release it eagerly, or use the context manager form:

```python
with df.chartkit.plot(title="Report") as chart:
    chart.save("report.png")
# figure released here
```

`close()` matters in two cases: long loops where you want memory freed
immediately, and after `show()`, which does register the figure with pyplot.

### Signatures

```python
def save(self, path: str, dpi: int | None = None) -> PlotResult
def show(self) -> PlotResult
def close(self) -> None
def describe(self, *, geometry: bool = False) -> dict[str, Any]
def explain(self) -> str
def __enter__(self) -> PlotResult
def __exit__(self, exc_type, exc, tb) -> None

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
| `variation()` | `variation(horizon: Horizon = "month", periods: int \| None = None, freq: Freq \| None = None) -> TransformAccessor` | Percentage variation by horizon (`'month'` or `'year'`, frequency auto-detection) |
| `accum()` | `accum(window: int \| None = None, freq: Freq \| None = None) -> TransformAccessor` | Accumulated via compound product in rolling window (fallback: `config.transforms.accum_window`) |
| `diff()` | `diff(periods: int = 1) -> TransformAccessor` | Absolute difference between periods (periods != 0; negative for forward diff) |
| `normalize()` | `normalize(base: float \| None = None, base_date: str \| None = None) -> TransformAccessor` | Normalize series (default: `config.transforms.normalize_base`) |
| `drawdown()` | `drawdown() -> TransformAccessor` | Percentage distance from historical peak |
| `zscore()` | `zscore(window: int \| None = None) -> TransformAccessor` | Statistical standardization (global or rolling, window >= 2) |
| `annualize()` | `annualize(periods: int \| None = None, freq: Freq \| None = None) -> TransformAccessor` | Annualize periodic rate via compound interest (frequency auto-detection) |
| `despike()` | `despike(window: int = 21, threshold: float = 5.0, method: DespikeMethod = "median") -> TransformAccessor` | Remove aggressive data spikes via Hampel filter (window must be odd >= 3) |
| `resample()` | `resample(freq: ResampleFreq = "month", method: ResampleMethod = "last") -> TransformAccessor` | Downsample to target frequency (`'day'`/`'week'`/`'month'`/`'quarter'`/`'year'`; agg: `'last'`/`'first'`/`'mean'`/`'sum'`) |
| `layer()` | `layer(x, y, *, kind, units, decimals, highlight, metrics, axis, **kwargs) -> Layer` | Create a Layer for `compose()` |
| `plot()` | `plot(x, y, *, kind, title, units, decimals, source, highlight, metrics, legend, figsize, xlabel, ylabel, xlim, ylim, grid, tick_rotation, tick_format, tick_freq, collision, debug, **kwargs) -> PlotResult` | Finalize chain and plot (same parameters as `df.chartkit.plot()`) |
| `df` | `@property -> pd.DataFrame` | Access to transformed DataFrame |

### Types

The values the runtime validators already enforced are exposed as `Literal` aliases in
`chartkit.transforms.types`, so a typo is caught by the type checker instead of at call time:

```python
Horizon        = Literal["month", "year"]
Freq           = Literal["D", "B", "W", "M", "Q", "Y", "BME", "BMS",
                         "daily", "business", "weekly", "monthly",
                         "quarterly", "yearly", "annual"]
DespikeMethod  = Literal["median", "interpolate"]
ResampleFreq   = Literal["day", "D", "week", "W", "month", "M",
                         "quarter", "Q", "year", "Y", "annual"]
ResampleMethod = Literal["last", "first", "mean", "sum"]
```

`normalize(base=...)` is a `float`, not an `int`: rebasing to `1.0` is the convention for index
and multiple charts, alongside the usual `100`.

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
    tick_freq: TickFreq | None = None,
    collision: bool = True,
    debug: bool = False,
) -> PlotResult
```

Compose multiple layers into a single chart with optional dual axes.

`compose()` takes only chart-level options. Per-series settings -- including `units` and its
companion `decimals` -- live on the `Layer`, because each axis is formatted independently.

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
| `tick_freq` | `TickFreq \| None` | `None` | Tick frequency: `"day"`, `"week"`, `"month"`, `"quarter"`, `"semester"`, `"year"`. `None` uses config |
| `collision` | `bool` | `True` | Enable collision resolution engine. `False` skips all label collision processing |
| `debug` | `bool` | `False` | Draw collision debug overlay |

Raises `ValidationError` if no layers are provided, all layers are on the right axis, or any layer uses a non-composable kind (boxplot, violinplot, hist, ecdf, pie, eventplot).

### Layer

```python
AxisSide = Literal["left", "right"]

@dataclass(frozen=True)
class Layer:
    df: pd.DataFrame
    x: str | None = None
    y: str | list[str] | None = None
    kind: ChartKind = "line"
    units: UnitFormat | None = None
    decimals: int | None = None
    highlight: HighlightInput = False
    metrics: str | list[str] | None = None
    axis: AxisSide = "left"
    kwargs: dict[str, Any] = field(default_factory=dict)
```

Create layers via `df.chartkit.layer()` or `df.chartkit.variation().layer()`. The `create_layer()` function validates eagerly (units, highlight, kind, axis) before constructing the Layer, so an invalid layer fails at creation rather than halfway through `compose()`.

### df.chartkit.layer()

```python
def layer(
    x: str | None = None,
    y: str | list[str] | None = None,
    *,
    kind: ChartKind = "line",
    units: UnitFormat | None = None,
    decimals: int | None = None,
    highlight: HighlightInput = False,
    metrics: str | list[str] | None = None,
    axis: AxisSide = "left",
    **kwargs: Any,
) -> Layer
```

Positional parameters mirror `plot()`: `layer('date', 'value')` selects the same columns that
`plot('date', 'value')` would. `kind` is keyword-only in both.

Same parameters as `plot()` but limited to data and rendering options. Chart-level options (`title`, `source`, `legend`, `figsize`, `xlabel`, `ylabel`, `xlim`, `ylim`, `grid`, `tick_rotation`, `tick_format`, `tick_freq`, `collision`, `debug`) are passed to `compose()` instead.

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

Aliases are defined centrally in `charts/_classification.py` as `KIND_ALIASES` and referenced by `ChartRenderer._ALIASES`.

| Alias | Resolves To |
|-------|-------------|
| `"line"` | `"plot"` |
| `"area"` | `"fill_between"` |

### Generic Rendering

These kinds have no enhancer and are driven straight through `ax.{kind}(x, y_series)`:

`plot`, `scatter`, `step`, `errorbar`, `fill`, `fill_betweenx`, `loglog`, `semilogx`, `semilogy`

```python
df.chartkit.plot(kind='scatter', s=50, alpha=0.7)
df.chartkit.plot(kind='step', where='mid')
```

### Rejected Kinds

`kind` is validated against an allowlist rather than "is it a callable `Axes` attribute". Two
groups are refused:

**2D grid and vector field data** get a dedicated message naming the input-shape mismatch:

`imshow`, `contour`, `contourf`, `pcolormesh`, `quiver`, `streamplot`, `barbs`, `spy`

**Everything else** raises `ValidationError` listing `available()`. This covers `Axes` methods
with an incompatible signature (`hlines`, `vlines`, `psd`, `acorr`, `hexbin`, `broken_barh`) and
methods that do not plot at all (`clear`, `set_title`, `grid`, `legend`, `twinx`, `remove`).
Previously both reached matplotlib and raised a `TypeError` about arguments the caller never
wrote.

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
| `validate_kind(kind)` | `None` | Validates kind against the allowlist. Raises `ValidationError` |
| `available()` | `list[str]` | Sorted list of every accepted kind: enhancers, generic kinds and aliases |

---

## Kind Classification

The `charts/_classification.py` module defines per-kind feature capabilities and provides validation functions used by `plot()`, `layer()`, and `compose()`.

### AxisGroup

```python
AxisGroup = Literal["series", "distribution", "aggregation", "isolated", "event"]
```

### KindCaps

```python
@dataclass(frozen=True)
class KindCaps:
    group: AxisGroup
    highlight: bool
    temporal_metrics: bool
    all_metrics: bool
    composable: bool
```

Capability matrix for classified kinds:

| Kind | Group | Highlight | Metrics | Temporal Metrics | Composable |
|------|-------|-----------|---------|------------------|------------|
| `plot`, `scatter`, `step`, `bar`, `barh`, `stacked_bar`, `fill_between`, `stairs`, `stem` | series | yes | yes | yes | yes |
| `stackplot` | series | no | yes | yes | yes |
| `boxplot`, `violinplot` | distribution | no | no | no | no |
| `hist`, `ecdf` | aggregation | no | no | no | no |
| `pie` | isolated | no | no | no | no |
| `eventplot` | event | no | no | no | no |

Unclassified generic kinds (any valid matplotlib Axes method not in the table) are allowed through all validations.

### Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `resolve_kind_alias(kind)` | `(str) -> str` | Resolves user-facing kind to canonical name (e.g., `"line"` -> `"plot"`) |
| `get_kind_caps(kind)` | `(str) -> KindCaps \| None` | Returns capabilities for a classified kind, or `None` for unclassified generic kinds |
| `validate_highlight_for_kind(kind, resolved=None)` | `(str, str \| None) -> None` | Raises `ValidationError` if kind does not support highlight |
| `validate_metrics_for_kind(kind, specs, resolved=None)` | `(str, str \| Sequence, str \| None) -> None` | Raises `ValidationError` if any metric is incompatible with kind |

### KIND_ALIASES

```python
KIND_ALIASES: dict[str, str] = {"line": "plot", "area": "fill_between"}
```

Single source of truth for chart kind aliases. `ChartRenderer._ALIASES` references this dict.

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
    fills: FillsConfig
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
| `moving_avg_min_periods` | `int \| None` | `None` (full window) |

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

#### FillsConfig

Opacity of filled chart bodies. Both are constrained to `0.0 <= alpha <= 1.0`.

| Field | Type | Default | Applies to |
|-------|------|---------|------------|
| `area_alpha` | `float` | `0.3` | `kind='area'` fills |
| `violin_alpha` | `float` | `0.7` | `kind='violinplot'` bodies |

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
- `highlight=True` with a kind that does not support highlight (e.g., `pie`, `hist`, `boxplot`)
- Metrics passed to a kind that does not support metrics (e.g., `metrics=['ath']` with `kind='pie'`)
- Temporal metrics (`ma`, `std_band`, `vband`) passed to a kind that only supports non-temporal metrics
- `compose()` receives a layer with a non-composable kind (e.g., `boxplot`, `pie`, `eventplot`)

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
