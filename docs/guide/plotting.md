# Chart Types and Formatting

Complete guide to the chart types available in chartkit and formatting options.

## Line Chart

The line chart is chartkit's default type. Ideal for visualizing temporal trends.

### Single Line

```python
import pandas as pd
import chartkit

# Sample data
df = pd.DataFrame({
    'rate': [10.5, 11.2, 10.8, 12.1, 11.9, 13.0]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Basic line chart
df.chartkit.plot(title="Interest Rate")
```

### Multiple Series

To plot multiple series on the same chart, simply include multiple columns in the DataFrame:

```python
df = pd.DataFrame({
    'series_a': [10, 12, 11, 14, 13, 15],
    'series_b': [8, 9, 10, 11, 12, 13],
    'series_c': [12, 11, 13, 12, 14, 13],
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Plots all numeric columns
df.chartkit.plot(title="Series Comparison")

# Or select specific columns
df.chartkit.plot(y=['series_a', 'series_b'], title="Series A and B")
```

### Column Selection

Use the `y` parameter to specify which columns to plot:

```python
# A single column (pass as string)
df.chartkit.plot(y='series_a', title="Series A Only")

# Multiple columns (pass as list)
df.chartkit.plot(y=['series_a', 'series_b'], title="Selected Series")
```

If `y` is not specified, all numeric columns will be plotted.

### plot() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x` | `str \| None` | `None` | Column for X-axis. If `None`, uses the DataFrame index |
| `y` | `str \| list[str] \| None` | `None` | Column(s) for Y-axis. If `None`, uses all numeric columns |
| `kind` | `ChartKind` | `"line"` | Chart type: `"line"`, `"bar"`, `"barh"`, `"stacked_bar"`, `"area"`, `"hist"`, `"pie"`, `"scatter"`, `"step"`, `"stem"`, `"stairs"`, `"boxplot"`, `"violinplot"`, `"ecdf"`, `"eventplot"`, `"stackplot"`, or any valid matplotlib Axes method |
| `title` | `str \| None` | `None` | Chart title |
| `units` | `UnitFormat \| None` | `None` | Y-axis formatting (see [Formatters](#formatters-table)) |
| `source` | `str \| None` | `None` | Data source for footer |
| `highlight` | `HighlightInput` | `False` | Highlight mode(s): `True`, `'last'`, `'max'`, `'min'`, `'all'`, or a list |
| `metrics` | `str \| list[str] \| None` | `None` | Declarative metrics (see [Metrics Guide](metrics.md)) |
| `legend` | `bool \| None` | `None` | `None` = auto (shows with 2+ artists), `True` = force, `False` = suppress |
| `xlabel` | `str \| None` | `None` | X-axis label |
| `ylabel` | `str \| None` | `None` | Y-axis label |
| `xlim` | `AxisLimits \| None` | `None` | X-axis limits as `(min, max)`. Accepts strings (`"2024-01-01"`, `"100"`), datetime, pd.Timestamp, numeric, or `None` per element |
| `ylim` | `AxisLimits \| None` | `None` | Y-axis limits as `(min, max)`. Accepts strings (`"100"`), datetime, pd.Timestamp, numeric, or `None` per element |
| `grid` | `bool \| None` | `None` | Grid override. `None` uses config, `True`/`False` enables/disables |
| `tick_rotation` | `int \| "auto" \| None` | `None` | X-axis tick label rotation. `"auto"` detects overlap and escalates to 90 degrees if the configured angle is insufficient; `int` forces angle. `None` uses config |
| `tick_format` | `str \| None` | `None` | Date format for X-axis ticks (e.g., `"%b/%Y"`). `None` uses config |
| `tick_freq` | `str \| None` | `None` | Tick frequency: `"day"`, `"week"`, `"month"`, `"quarter"`, `"semester"`, `"year"`. `None` uses config. See [Smart Tick Alignment](#smart-tick-alignment) |
| `collision` | `bool` | `True` | Enable collision resolution engine. `False` skips all label collision processing |
| `debug` | `bool` | `False` | Show collision debug overlay (see [Collision Guide](collision.md)) |
| `**kwargs` | - | - | Chart-specific args (e.g., `sort`, `color`, `y_origin` for bars) |

For full type definitions and signatures, see the [API Reference](../reference/api.md).

---

## Bar Chart

Use `kind='bar'` to create bar charts. Ideal for comparisons between categories or visualizing positive and negative values.

### Basic Bars

```python
df = pd.DataFrame({
    'sales': [150, 200, 180, 220, 250, 230]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.chartkit.plot(kind='bar', title="Monthly Sales")
```

### Multiple Columns (Grouped Bars)

When a DataFrame has multiple numeric columns, bar charts render as grouped bars with automatic color cycling and offset calculation:

```python
df = pd.DataFrame({
    'revenue': [100, 120, 140, 160],
    'expenses': [80, 95, 110, 120],
}, index=pd.date_range('2024-01', periods=4, freq='QE'))

df.chartkit.plot(kind='bar', title="Revenue vs Expenses", units='BRL_compact')
```

### Categorical Axes

Bar charts automatically detect string/categorical indices (not just temporal). Both single-column and multi-column DataFrames work with categorical data:

```python
# Single-column categorical
df = pd.DataFrame({
    'score': [85, 92, 78, 95, 88]
}, index=['Team A', 'Team B', 'Team C', 'Team D', 'Team E'])

df.chartkit.plot(kind='bar', title="Team Scores")

# Multi-column categorical (grouped bars by category)
df = pd.DataFrame({
    '2023': [15, 22, 18, 12],
    '2024': [17, 20, 19, 14],
}, index=['North', 'South', 'East', 'West'])

df.chartkit.plot(kind='bar', title="Sales by Region", units='human')
```

Supported index types: string indices, `pd.CategoricalIndex`, `pd.StringDtype`, and object dtype with string values. Bar width defaults to `bars.width_default` (0.8) for categorical data.

### Sorting Bars

Single-column bar charts can be sorted via the `sort` keyword argument. Labels move with their values:

```python
# Ascending order
df.chartkit.plot(kind='bar', title="Ranked", sort='ascending')

# Descending order
df.chartkit.plot(kind='bar', title="Ranked", sort='descending')

# Sorting with color cycling and highlights
df.chartkit.plot(kind='bar', title="Ranked", sort='descending', color='cycle', highlight='max')
```

`sort` accepts `None` (default, keeps original order), `'ascending'`, or `'descending'`. Not supported for multi-column charts.

### Per-Bar Color Cycling

Use `color='cycle'` to apply a different color from the theme palette to each bar (single-column only). The default theme has 6 colors (primary through senary) that cycle when there are more bars:

```python
df.chartkit.plot(kind='bar', title="Categories", color='cycle')
```

### Automatic Bar Width

Bar width is detected automatically based on data frequency:

| Data Type | Width | Trigger |
|-----------|-------|---------|
| Categorical/string index | `bars.width_default` (0.8) | Non-numeric, non-datetime index |
| Monthly datetime | `bars.width_monthly` (20 days) | Avg gap > `frequency_detection.monthly_threshold` (25 days) |
| Annual datetime | `bars.width_annual` (300 days) | Avg gap > `frequency_detection.annual_threshold` (300 days) |
| Other datetime | `bars.width_default` (0.8) | Fallback |

All thresholds are configurable via [Configuration](configuration.md).

### Bars with Positive and Negative Values

chartkit automatically handles positive and negative values:

```python
df = pd.DataFrame({
    'balance': [100, -50, 200, -75, 150, -25]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.chartkit.plot(kind='bar', title="Monthly Balance", units='BRL')
```

### Y-Axis Origin (y_origin)

The `y_origin` parameter controls how the Y-axis limits are set. Available for both `bar` and `stacked_bar` charts:

```python
# Zero origin (default) - Y-axis includes zero, shows full magnitude
df.chartkit.plot(kind='bar', title="Monthly Balance", y_origin='zero')

# Auto origin - focuses on data variation with 10% margin
df.chartkit.plot(kind='bar', title="Monthly Balance", y_origin='auto')
```

| Value | Behavior |
|-------|----------|
| `'zero'` | Y-axis always includes zero. For positive-only data, starts at 0; for negative-only, ends at 0. |
| `'auto'` | Y-axis adjusts to data range with configurable margin (`bars.auto_margin`, default 10%). |

Use `y_origin='zero'` when absolute magnitude matters. Use `y_origin='auto'` when you want to highlight small variations in large values.

---

## Stacked Bar Chart

Use `kind='stacked_bar'` to create stacked bar charts. Ideal for showing the composition of a total over time.

### Basic Stacked Bars

```python
df = pd.DataFrame({
    'product_a': [100, 120, 130, 140],
    'product_b': [80, 90, 85, 95],
    'product_c': [50, 60, 55, 70],
}, index=pd.date_range('2024-01', periods=4, freq='QE'))

df.chartkit.plot(kind='stacked_bar', title="Revenue by Product")
```

Each DataFrame column becomes a layer of the bar, using colors from the configured palette. The legend is automatically generated for DataFrames with multiple columns, and bar widths are automatically adjusted by data frequency.

Stacked bars also support categorical indices and the `y_origin` parameter:

```python
df = pd.DataFrame({
    'online': [120, 200, 150, 80],
    'physical': [300, 250, 180, 220],
}, index=['North', 'South', 'East', 'West'])

df.chartkit.plot(kind='stacked_bar', title="Sales Channel by Region")
```

---

## Horizontal Bar Chart

Use `kind='barh'` to create horizontal bar charts. The Y axis holds categories or positions, the X axis holds values.

### Basic Horizontal Bars

```python
df = pd.DataFrame({
    'sales': [150, 200, 180, 220, 250]
}, index=['Team A', 'Team B', 'Team C', 'Team D', 'Team E'])

df.chartkit.plot(kind='barh', title="Sales by Team")
```

### Multiple Columns (Grouped)

```python
df = pd.DataFrame({
    '2023': [15, 22, 18, 12],
    '2024': [17, 20, 19, 14],
}, index=['North', 'South', 'East', 'West'])

df.chartkit.plot(kind='barh', title="Sales by Region")
```

### Sorting

Single-column horizontal bars support `sort='ascending'` or `sort='descending'`:

```python
df.chartkit.plot(kind='barh', title="Ranked", sort='descending')
```

### Color Cycling

```python
df.chartkit.plot(kind='barh', title="Categories", color='cycle')
```

Horizontal bars also support `y_origin` (`'zero'` or `'auto'`) which controls the X-axis origin.

---

## Area Chart

Use `kind='area'` (alias for `fill_between`) to create filled area charts. Behavior depends on the number of columns:

- **1 column**: fills from zero to y (classic area chart).
- **2 columns**: fills between the two series (spread / interval), with contour lines on each.
- **3+ columns**: each column fills from zero independently.

```python
df = pd.DataFrame({
    'revenue': [100, 120, 130, 140, 160],
    'costs': [80, 90, 85, 95, 100],
}, index=pd.date_range('2024-01', periods=5, freq='ME'))

# Single series area (fill from zero)
df[['revenue']].chartkit.plot(kind='area', title="Revenue", units='BRL_compact')

# Two series: fills between the pair (spread/interval)
df.chartkit.plot(kind='area', title="Revenue vs Costs Spread", units='BRL_compact')
```

For stacked areas use `kind='stackplot'` instead.

---

## Other Chart Types

chartkit supports many additional chart types through registered enhancers and generic rendering. Any valid matplotlib Axes method can be used as `kind`.

### Enhancers (Specialized Handling)

These types have dedicated enhancers with color cycling, proper label handling, and correct argument mapping:

| Kind | Description | Notes |
|------|-------------|-------|
| `'hist'` | Histogram | Data is passed for binning, not as (x, y) pairs. Multi-column aligns bins |
| `'pie'` | Pie chart | Single-column only. Index used as slice labels |
| `'stackplot'` | Stacked area | All columns stacked. Use `kind='area'` for overlapped areas |
| `'stem'` | Stem plot | Vertical lines from baseline to data points |
| `'stairs'` | Step function | Values as heights with auto-generated edges |
| `'boxplot'` | Box-and-whisker | Each column becomes a box. `patch_artist=True` forced |
| `'violinplot'` | Violin plot | Kernel density + quartile markers per column |
| `'ecdf'` | Empirical CDF | Data values on X, cumulative probability on Y |
| `'eventplot'` | Event positions | Each column becomes a row of vertical event markers |

```python
# Histogram
df.chartkit.plot(kind='hist', title="Distribution", bins=20)

# Pie chart
df[['share']].chartkit.plot(kind='pie', title="Market Share")

# Stacked area
df.chartkit.plot(kind='stackplot', title="Composition")

# Box plot
df.chartkit.plot(kind='boxplot', title="Distribution by Column")
```

### Generic Rendering

Any matplotlib Axes method not listed above works automatically:

```python
df.chartkit.plot(kind='scatter', s=50, alpha=0.7)
df.chartkit.plot(kind='step', where='mid')
```

Extra `**kwargs` are passed directly to the matplotlib method.

### Unsupported Kinds

Chart kinds that require 2D grid data or vector fields are explicitly blocked with descriptive error messages:

`imshow`, `contour`, `contourf`, `pcolormesh`, `quiver`, `streamplot`, `barbs`, `spy`

---

## Y-Axis Formatting

The `units` parameter controls how Y-axis values are formatted. chartkit offers several pre-defined formatters.

### Currencies

```python
# Brazilian Real: R$ 1.234,56
df.chartkit.plot(title="Values in BRL", units='BRL')

# US Dollar: $ 1,234.56
df.chartkit.plot(title="Values in USD", units='USD')
```

### Compact Currencies

For large values, use compact formats:

```python
# Compact Real: R$ 1,2 mi (millions), R$ 1,2 bi (billions)
df.chartkit.plot(title="GDP", units='BRL_compact')

# Compact Dollar: $1.2M, $1.2B
df.chartkit.plot(title="Revenue", units='USD_compact')
```

### Percentage

```python
# Percentage: 10.5%
df.chartkit.plot(title="Inflation Rate", units='%')
```

The percentage formatter uses the configured locale (decimal separator based on `babel_locale`).

### Integers (Points)

```python
# Integers with locale-aware thousand separators: 1.234.567
df.chartkit.plot(title="Number of Customers", units='points')
```

Ideal for large integer values such as population, number of customers, etc.

### Human-Readable Notation

```python
# Compact notation: 1.2M (millions), 1.2B (billions)
df.chartkit.plot(title="Volume", units='human')
```

The `human` format is similar to `BRL_compact`, but without the currency symbol. Useful for general numeric values.

### Formatters Table

| Value | Format | Example |
|-------|--------|---------|
| `'BRL'` | Brazilian Real | R$ 1.234,56 |
| `'USD'` | US Dollar | $ 1,234.56 |
| `'BRL_compact'` | Compact Real | R$ 1,2 mi |
| `'USD_compact'` | Compact Dollar | $1.2M |
| `'%'` | Percentage | 10,5% |
| `'points'` | Locale-aware integers | 1.234.567 |
| `'human'` | Compact notation | 1,2M |
| `'x'` | Multiplier | 12,3x |

Currency formatters use the [Babel](https://babel.pocoo.org/) library and support any ISO 4217 currency code.

---

## Footer with Source

The `source` parameter adds a footer with the data source:

```python
df.chartkit.plot(
    title="Selic Rate",
    units='%',
    source='Central Bank of Brazil'
)
```

When `source` is not provided, chartkit uses `branding.default_source` from the configuration as a fallback. If both are empty, the footer displays only the `company_name`.

The footer text follows the format configured in `branding.footer_format`. The default is:

```
Fonte: {source}, {company_name}
```

### Customizing the Footer Format

Via TOML file:

```toml
[branding]
company_name = "My Company"
footer_format = "Fonte: {source} | By: {company_name}"
```

Via code:

```python
from chartkit import configure

configure(branding={
    'company_name': 'My Company',
    'footer_format': 'Fonte: {source} | By: {company_name}'
})
```

---

## Smart Tick Alignment

When using `tick_freq` or `tick_format`, chartkit aligns ticks to real data points instead of fixed calendar boundaries. This prevents the common misalignment where, e.g., quarterly data at end-of-quarter dates (Mar, Jun, Sep, Dec) gets ticks placed on day 1 of start-of-quarter months (Jan, Apr, Jul, Oct).

### How It Works

1. **Data-aligned ticks**: For frequencies `"month"`, `"quarter"`, `"semester"`, and `"year"`, ticks are placed on the last real data point in each period rather than on arbitrary calendar boundaries.

2. **Auto-inference**: When no explicit `tick_freq` is set, chartkit uses `pd.infer_freq()` to detect the data's temporal pattern. For sparse frequencies (quarterly, semi-annual, annual), ticks are positioned directly on the actual index dates.

3. **Phantom tick clipping**: After setting the locator, ticks that fall outside the real data range are removed. This prevents empty periods caused by `xlim` padding (common in bar charts).

### Frequency Alignment

| Frequency | Tick Months |
|-----------|-------------|
| `"quarter"` | 3, 6, 9, 12 (end-of-quarter) |
| `"semester"` | 6, 12 (end-of-semester) |
| `"month"` | All months |
| `"year"` | Last data point per year |

```python
# Quarterly data: ticks land on Mar, Jun, Sep, Dec (where the data is)
df = pd.DataFrame({'gdp': [100, 102, 104, 106]},
                  index=pd.date_range('2024-03', periods=4, freq='QE'))
df.chartkit.plot(title="Quarterly GDP", tick_freq='quarter', tick_format='%b/%Y')
```

---

## Highlighting Values (highlight)

The `highlight` parameter adds markers and labels at specific points of each series. Accepts `bool`, string, or list of modes:

| Value | Behavior |
|-------|----------|
| `True` / `'last'` | Highlights the last value of each series |
| `'max'` | Highlights the maximum value of each series |
| `'min'` | Highlights the minimum value of each series |
| `'all'` | Annotates every data point with its value |
| `['max', 'min']` | Combines multiple modes |
| `False` | No highlight (default) |

Not all chart kinds support highlight. Passing `highlight=True` to an unsupported kind raises `ValidationError`. The following kinds do **not** support highlight:

`stackplot`, `boxplot`, `violinplot`, `hist`, `ecdf`, `pie`, `eventplot`

```python
# Highlight last value (equivalent)
df.chartkit.plot(title="Interest Rate", highlight=True)
df.chartkit.plot(title="Interest Rate", highlight='last')

# Highlight max and min
df.chartkit.plot(title="Interest Rate", highlight=['max', 'min'])

# Highlight all: last, max, and min
df.chartkit.plot(title="Interest Rate", highlight=['last', 'max', 'min'])

# Annotate every data point
df.chartkit.plot(kind='bar', title="Monthly Sales", highlight='all')
```

### Full Example

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'selic': [13.75, 13.25, 12.75, 12.25, 11.75, 11.25]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.chartkit.plot(
    title="Selic Rate",
    units='%',
    source='BCB',
    highlight=['last', 'max']
)
```

---

## Method Chaining with PlotResult

The `plot()` method returns a `PlotResult` object that allows operation chaining.

### Saving a Chart

```python
# Saves to the configured charts directory
df.chartkit.plot(title="Chart").save('my_chart.png')

# Saves with custom DPI
df.chartkit.plot(title="Chart").save('my_chart.png', dpi=150)

# Absolute path
df.chartkit.plot(title="Chart").save('C:/temp/chart.png')
```

If the path is relative, the chart is saved to `CHARTS_PATH` (configurable).

### Showing a Chart

```python
# Displays in interactive window
df.chartkit.plot(title="Chart").show()
```

### Full Chaining

```python
# Save and show in the same call
df.chartkit.plot(title="Chart").save('chart.png').show()

# Save with high DPI, then show
df.chartkit.plot(title="Chart").save('chart.png', dpi=300).show()
```

### Accessing Axes and Figure

`PlotResult` exposes the matplotlib `Axes` and `Figure` for advanced customizations:

```python
result = df.chartkit.plot(title="Chart")

# Access the Axes
result.axes.set_xlim(['2024-01-01', '2024-12-31'])
result.axes.axhline(5, color='red', linestyle='--')
result.axes.set_ylabel('My Label')

# Access the Figure
result.figure.set_size_inches(14, 8)
result.figure.suptitle('Super Title')

# Save after customizations
result.save('custom_chart.png')
```

### PlotResult API

| Method/Property | Return | Description |
|-----------------|--------|-------------|
| `save(path, dpi=None)` | `PlotResult` | Saves the chart and returns self |
| `show()` | `PlotResult` | Displays the chart and returns self |
| `axes` | `Axes` | Access to matplotlib Axes |
| `figure` | `Figure` | Access to matplotlib Figure |

---

## Chart Composition (Multi-Layer)

For complex charts that combine different chart types or need dual Y-axes, use `layer()` + `compose()`. This section provides a quick overview. For tutorials and reusable snippets, see the dedicated [Composition Guide](composition.md).

### Basic Composition

```python
from chartkit import compose

# Two DataFrames with different data
price = pd.DataFrame({'close': [100, 105, 102, 110]}, index=dates)
volume = pd.DataFrame({'vol': [1e6, 1.2e6, 0.8e6, 1.5e6]}, index=dates)

# Create layers
layer_price = price.chartkit.layer(kind='line', units='BRL', highlight=True)
layer_volume = volume.chartkit.layer(kind='bar', units='human', axis='right')

# Compose into a single chart
compose(layer_price, layer_volume, title="Price and Volume", source="Bloomberg")
```

### Rules

- At least one layer must use `axis='left'`
- Conflicting units on the same axis trigger a warning
- `layer()` captures intent; rendering happens only in `compose()`
- Non-composable kinds (`boxplot`, `violinplot`, `hist`, `ecdf`, `pie`, `eventplot`) are rejected by `compose()` with `ValidationError`. Only series-group kinds (line, bar, scatter, area, etc.) can participate in multi-layer charts

### How It Works

1. `df.chartkit.layer()` creates a `Layer` (frozen dataclass) that captures plotting intent without rendering
2. `compose(*layers)` creates a figure, sets up dual axes if needed, renders each layer, consolidates the legend, resolves cross-axis collisions, and returns a `PlotResult`
3. The returned `PlotResult` supports the same `.save()` / `.show()` chaining as `plot()`

### Learn More

- [Composition Guide](composition.md) for end-to-end tutorials and snippets
- [API Reference](../reference/api.md#chart-composition) for full signatures

---

## Full Examples

### Financial Dashboard

```python
import pandas as pd
import chartkit

# Selic Rate
selic = pd.DataFrame({
    'rate': [13.75, 13.25, 12.75, 12.25, 11.75, 11.25]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

selic.chartkit.plot(
    title="Selic Rate",
    units='%',
    source='Central Bank of Brazil',
    highlight=True
).save('selic.png')

# Dollar Exchange Rate
dollar = pd.DataFrame({
    'exchange_rate': [4.95, 5.02, 4.98, 5.15, 5.08, 5.22]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

dollar.chartkit.plot(
    title="Dollar Exchange Rate",
    units='BRL',
    source='BCB',
    highlight=True
).save('dollar.png')
```

### Investment Comparison

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'CDI': [100, 101.1, 102.2, 103.4, 104.6, 105.8],
    'Ibovespa': [100, 98.5, 102.3, 105.1, 103.8, 108.2],
    'S&P 500': [100, 101.5, 103.2, 105.8, 107.1, 109.5],
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.chartkit.plot(
    title="Investment Comparison (Base 100)",
    units='points',
    source='Bloomberg',
    highlight=True
).save('comparison.png')
```

### Monthly Balance with Bars

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'balance': [15000, -8000, 22000, -5000, 18000, 25000]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.chartkit.plot(
    kind='bar',
    title="Monthly Balance",
    units='BRL_compact',
    source='Accounting',
    y_origin='zero'
).save('monthly_balance.png')
```

---

## Next Steps

- [Composition](composition.md) - Multi-layer charts with `layer()` + `compose()`
- [Transforms](transforms.md) - Temporal transformations (YoY, MoM, etc.)
- [Metrics](metrics.md) - Declarative overlays (ATH, moving averages, bands)
- [Configuration](configuration.md) - Full customization
