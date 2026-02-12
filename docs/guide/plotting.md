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

### Bars with Positive and Negative Values

chartkit automatically handles positive and negative values:

```python
df = pd.DataFrame({
    'balance': [100, -50, 200, -75, 150, -25]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.chartkit.plot(kind='bar', title="Monthly Balance", units='BRL')
```

### Y-Axis Origin (y_origin)

The `y_origin` parameter is specific to bar charts and passed via `**kwargs`:

```python
# Zero origin (default) - shows full magnitude
df.chartkit.plot(kind='bar', title="Monthly Balance", y_origin='zero')

# Auto origin - focuses on data variation
df.chartkit.plot(kind='bar', title="Monthly Balance", y_origin='auto')
```

| Value | Behavior |
|-------|----------|
| `'zero'` | Y-axis always starts from zero. Shows real magnitude. |
| `'auto'` | Matplotlib defines limits. Focuses on data variation. |

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

---

## Area Between Series (fill_between)

The `fill_between` parameter shades the area between two DataFrame columns. Useful for visualizing spreads, confidence intervals, or differences between series.

```python
df = pd.DataFrame({
    'selic': [13.75, 13.25, 12.75, 12.25, 11.75, 11.25],
    'cpi': [5.5, 5.2, 4.8, 4.5, 4.2, 3.9],
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Shade area between Selic and CPI
df.chartkit.plot(
    title="Selic - CPI Spread",
    units='%',
    fill_between=('selic', 'cpi')
)
```

The parameter receives a tuple with two column names: `(col1, col2)`.

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

## Highlighting Values (highlight)

The `highlight` parameter adds markers and labels at specific points of each series. Accepts `bool`, string, or list of modes:

| Value | Behavior |
|-------|----------|
| `True` / `'last'` | Highlights the last value of each series |
| `'max'` | Highlights the maximum value of each series |
| `'min'` | Highlights the minimum value of each series |
| `['max', 'min']` | Combines multiple modes |
| `False` | No highlight (default) |

```python
# Highlight last value (equivalent)
df.chartkit.plot(title="Interest Rate", highlight=True)
df.chartkit.plot(title="Interest Rate", highlight='last')

# Highlight max and min
df.chartkit.plot(title="Interest Rate", highlight=['max', 'min'])

# Highlight all: last, max, and min
df.chartkit.plot(title="Interest Rate", highlight=['last', 'max', 'min'])
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

- [Transforms](transforms.md) - Temporal transformations (YoY, MoM, etc.)
- [Metrics](metrics.md) - Declarative overlays (ATH, moving averages, bands)
- [Configuration](../reference/configuration.md) - Full customization
