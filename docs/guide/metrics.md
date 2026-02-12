# Metrics

Declarative metrics system for adding visual elements on top of the main data.

> **Note:** Default values such as colors, line widths, and labels can be customized
> via TOML file. See [Configuration](configuration.md).

---

## Summary

| Metric | Syntax | Description |
|--------|--------|-------------|
| Moving Average | `'ma:N'` | Moving average line of N periods |
| ATH | `'ath'` | Line at all-time high |
| ATL | `'atl'` | Line at all-time low |
| Average | `'avg'` | Horizontal line at the mean of the data |
| Horizontal Line | `'hline:V'` | Horizontal line at value V |
| Band | `'band:L:U'` | Shaded area between L and U |
| Target | `'target:V'` | Target horizontal line at value V |
| Standard Deviation Band | `'std_band:W:N'` | Band of N standard deviations with window W |
| Vertical Band | `'vband:D1:D2'` | Shaded area between two dates |

---

## Basic Usage

Metrics are passed as a string or list of strings in the `metrics` parameter:

```python
# Single metric (single string)
df.chartkit.plot(metrics='ath')

# Multiple metrics (list)
df.chartkit.plot(metrics=['ath', 'atl', 'ma:12'])

# Full combination
df.chartkit.plot(metrics=['ath', 'ma:12', 'hline:3.0', 'band:1.5:4.5'])
```

The metrics system uses a centralized registry that parses specification strings
and applies the corresponding functions to the chart.

---

## Moving Average (ma:N)

Adds a moving average line over the data using the syntax `'ma:N'`, where N
is the number of periods.

```python
df.chartkit.plot(title="Data with MA12", metrics=['ma:12'])
```

### Syntax

- `'ma:3'` - 3-period moving average
- `'ma:12'` - 12-period moving average
- `'ma:24'` - 24-period moving average

### Visual Properties

| Property | Value | TOML Configuration |
|----------|-------|--------------------|
| Color | Gray (#888888) | `colors.moving_average` |
| Style | Solid line | - |
| Width | 1.5 | `lines.overlay_width` |
| Label | "MA{window}" | `labels.moving_average_format` |
| zorder | 2 | Above reference lines, below data |

### Example

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'value': [10, 12, 11, 14, 13, 15, 14, 16, 15, 18, 17, 19]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

df.chartkit.plot(
    title="Series with Moving Average",
    metrics=['ma:3'],
    units='%'
)
```

---

## ATH and ATL

Dashed horizontal lines at the historical extremes of the series.

### ATH (All-Time High)

Line at the historical maximum of the data.

```python
df.chartkit.plot(title="Chart", metrics=['ath'])
```

| Property | Value | TOML Configuration |
|----------|-------|--------------------|
| Color | Green | `colors.positive` |
| Label | "ATH" | `labels.ath` |
| Style | Dashed (--) | `lines.reference_style` |
| zorder | 1 | Reference line level |

### ATL (All-Time Low)

Line at the historical minimum of the data.

```python
df.chartkit.plot(title="Chart", metrics=['atl'])
```

| Property | Value | TOML Configuration |
|----------|-------|--------------------|
| Color | Red | `colors.negative` |
| Label | "ATL" | `labels.atl` |
| Style | Dashed (--) | `lines.reference_style` |
| zorder | 1 | Reference line level |

### Both

```python
df.chartkit.plot(title="Historical Extremes", metrics=['ath', 'atl'])
```

### Example

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'cpi': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8, 3.5, 4.0, 5.5, 4.0]
}, index=pd.date_range('2024-01', periods=10, freq='ME'))

df.chartkit.plot(
    title="CPI with Extremes",
    units='%',
    metrics=['ath', 'atl']
)
```

---

## Average (avg)

Horizontal line at the mean of the data. Uses `colors.grid` color and dashed style.

```python
df.chartkit.plot(title="Chart with Average", metrics=['avg'])
```

| Property | Value | TOML Configuration |
|----------|-------|--------------------|
| Color | Grid (lightgray) | `colors.grid` |
| Label | "AVG" | `labels.avg` |
| Style | Dashed (--) | `lines.reference_style` |
| zorder | 1 | Reference line level |

### Example

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'cpi': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8, 3.5, 4.0, 5.5, 4.0]
}, index=pd.date_range('2024-01', periods=10, freq='ME'))

df.chartkit.plot(
    title="CPI with Average",
    units='%',
    metrics=['avg', 'ath', 'atl']
)
```

---

## Horizontal Lines (hline:V)

Use the syntax `'hline:V'` to add reference lines at arbitrary values,
where V is the value on the Y-axis.

```python
# Single line
df.chartkit.plot(metrics=['hline:3.0'])

# Multiple lines
df.chartkit.plot(metrics=['hline:3.0', 'hline:4.5', 'hline:1.5'])
```

### Syntax

- `'hline:3.0'` - Horizontal line at y=3.0
- `'hline:100'` - Horizontal line at y=100
- `'hline:-5.5'` - Horizontal line at y=-5.5 (negative values supported)

### Example: Inflation Target

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'cpi': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Central target line (3.0%) and tolerance limits (1.5% and 4.5%)
df.chartkit.plot(
    title="CPI vs Target",
    units='%',
    metrics=['hline:3.0', 'hline:4.5', 'hline:1.5']
)
```

---

## Shaded Bands (band:L:U)

Use the syntax `'band:L:U'` to add shaded areas between two values,
where L is the lower limit and U is the upper limit.

```python
df.chartkit.plot(metrics=['band:1.5:4.5'])
```

### Syntax

- `'band:1.5:4.5'` - Band between 1.5 and 4.5
- `'band:0:100'` - Band between 0 and 100
- `'band:-10:10'` - Band between -10 and 10

### Visual Properties

| Property | Value |
|----------|-------|
| Style | Semi-transparent filled area |
| zorder | 0 | Furthest back, behind all other elements |

### Example: Tolerance Band

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'cpi': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Band representing the inflation target tolerance range
df.chartkit.plot(
    title="CPI with Target Band",
    units='%',
    metrics=['band:1.5:4.5']
)
```

---

## Target Line (target:V)

Use the syntax `'target:V'` to add a target horizontal line with a distinctive style
(secondary color, dash-dot). The label is automatically generated with the formatted value.

```python
# Simple target
df.chartkit.plot(metrics=['target:1000'])

# Target with currency formatting
df.chartkit.plot(units='BRL', metrics=['target:1000'])
# Label: "Target: R$ 1.000,00"
```

### Syntax

- `'target:1000'` - Target line at 1000
- `'target:3.0'` - Target line at 3.0

### Visual Properties

| Property | Value | TOML Configuration |
|----------|-------|--------------------|
| Color | Secondary | `colors.secondary` |
| Style | Dash-dot (-.) | `lines.target_style` |
| Width | 1.5 | `lines.overlay_width` |
| Label | "Meta: {value}" | `labels.target_format` |
| zorder | 1 | Reference line level |

The target line uses `secondary` color and dash-dot (`-.`) style by default, visually
distinguishing it from standard reference lines (ATH, ATL, hline) that use dashed style.

---

## Standard Deviation Band (std_band:W:N)

Use the syntax `'std_band:W:N'` to add a standard deviation band (Bollinger Band)
with a central moving average. W is the moving average window and N is the number of standard deviations.

```python
# Bollinger Band: window 20, 2 standard deviations
df.chartkit.plot(metrics=['std_band:20:2'])
```

### Syntax

- `'std_band:20:2'` - 20-period window, 2 standard deviations
- `'std_band:12:1.5'` - 12-period window, 1.5 standard deviations

### Visual Properties

| Property | Value | TOML Configuration |
|----------|-------|--------------------|
| Band color | Grid (lightgray) | `colors.grid` |
| Central line style | Dashed (--) | `lines.reference_style` |
| Width | 1.5 | `lines.overlay_width` |
| Label | "BB({window}, {num_std})" | `labels.std_band_format` |

### Example

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'price': [100, 102, 98, 105, 103, 107, 101, 108, 106, 110]
}, index=pd.date_range('2024-01', periods=10, freq='ME'))

# Bollinger Band with 5-period moving average and 2 standard deviations
df.chartkit.plot(
    title="Price with Bollinger Band",
    metrics=['std_band:5:2']
)
```

---

## Vertical Band (vband:D1:D2)

Use the syntax `'vband:D1:D2'` to add a vertical shaded area between two dates.
Ideal for highlighting specific periods such as recessions, crises, or events.

```python
# Shade period between two dates
df.chartkit.plot(metrics=['vband:2020-03-01:2020-06-30'])
```

### Syntax

- `'vband:2020-03-01:2020-06-30'` - Vertical band between March and June 2020
- `'vband:2008-09-01:2009-06-30'` - Vertical band for the financial crisis

### Example

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'gdp': [100, 102, 104, 95, 88, 92, 98, 105, 108, 110]
}, index=pd.date_range('2019-07', periods=10, freq='QE'))

# Highlight recession period
df.chartkit.plot(
    title="GDP with Crisis Period",
    metrics=['vband:2020-01-01:2020-09-30']
)
```

---

## Combining Metrics

All metrics can be freely combined in a single list.
The system applies each metric in the specified order, respecting the
zorder hierarchy for visual layering.

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'value': [10, 12, 11, 14, 13, 15, 14, 16, 15, 18, 17, 19]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

df.chartkit.plot(
    title="Complete Analysis",
    units='%',
    metrics=[
        'ath',          # All-time high
        'atl',          # All-time low
        'ma:3',         # 3-period moving average
        'hline:15',     # Reference line
        'band:12:18'    # Shaded band
    ]
)
```

### Example: Inflation Analysis

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'cpi': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8, 3.5, 4.0, 5.5, 4.0, 3.8, 4.2]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

df.chartkit.plot(
    title="CPI - Complete Analysis",
    units='%',
    metrics=[
        'band:1.5:4.5',  # Target tolerance band
        'hline:3.0',     # Target center
        'ma:3',          # Short-term trend
        'ath',           # Historical peak
        'atl'            # Historical trough
    ]
)
```

---

## Rendering Order (zorder)

The metrics system uses zorder to control visual layering
of elements. Elements with lower zorder are rendered first (furthest back),
while elements with higher zorder appear in front.

| Element | zorder | Position |
|---------|--------|----------|
| Band (`band`) | 0 | Furthest back |
| ATH/ATL/hlines | 1 | Reference lines |
| Moving average (`ma`) | 2 | Intermediate |
| Main data | 3+ | Foremost |

This hierarchy ensures that:

1. Shaded bands don't obscure other elements
2. Reference lines (ATH, ATL, hlines) are visible but don't interfere with data
3. Moving average follows the data but doesn't overlap it
4. Main data is always visible on top

---

## @ Syntax (Target Specific Column)

For DataFrames with multiple columns, use the `@` syntax to direct a
metric to a specific column:

```python
df = pd.DataFrame({
    'revenue': [100, 120, 110, 140],
    'costs': [80, 90, 85, 95],
}, index=pd.date_range('2024-01', periods=4, freq='ME'))

# ATH only on revenue column
df.chartkit.plot(metrics=['ath@revenue'])

# Moving average on costs column
df.chartkit.plot(metrics=['ma:12@costs'])

# Combination
df.chartkit.plot(metrics=['ath@revenue', 'atl@costs', 'ma:6@revenue'])
```

### Syntax

- `'metric@column'` - Applies metric only to the specified column
- `'metric:param@column'` - With parameters: `'ma:12@revenue'`
- Without `@`: metric uses the first column (or the only column for Series)

### Data-Independent Metrics

Metrics that don't depend on data (`hline`, `band`) silently ignore the `@`,
as they are registered with `uses_series=False`.

```python
# hline silently ignores @column
df.chartkit.plot(metrics=['hline:3.0', 'ath@revenue'])
```

---

## Custom Labels (| syntax)

By default, each metric uses a pre-defined label (e.g., "ATH", "MA12"). To customize
the name displayed in the legend, use the `|` syntax at the end of the specification:

```python
# Simple custom label
df.chartkit.plot(metrics=['ath|All-Time High'])

# With parameters
df.chartkit.plot(metrics=['ma:12|12-Month Average'])

# Combining with @column
df.chartkit.plot(metrics=['ma:12@revenue|12M Average'])

# With special characters in label
df.chartkit.plot(metrics=['hline:100|Target: Q1'])
```

### Syntax

- `'metric|label'` - Simple custom label
- `'metric:param|label'` - With parameters
- `'metric:param@column|label'` - With parameters and column
- Without `|`: uses the metric's default label

The `|` is extracted before `@` and `:`, allowing special characters in the label.

---

## See Also

- [Configuration](configuration.md) - Customization of colors, labels, and metric styles
