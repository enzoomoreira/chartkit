# Transforms

Transformation functions for financial time series.

## Summary

| Function | Description | Typical Use |
|----------|-------------|-------------|
| `variation()` | Percentage variation by horizon | Monthly CPI, annual growth |
| `accum()` | Accumulated in rolling window | Trailing 12m CPI, Selic 12m |
| `diff()` | Absolute difference | Variation in p.p. |
| `normalize()` | Normalize to base | Compare scales |
| `drawdown()` | Percentage distance from peak | Asset decline |
| `zscore()` | Statistical standardization | Compare series |
| `annualize()` | Annualize periodic rate | Annual CDI |
| `to_month_end()` | Normalize to month-end | Align series |

## Import

```python
from chartkit import (
    variation, accum, diff, normalize,
    drawdown, zscore,
    annualize, to_month_end,
)
```

## Chained Usage via Accessor

All transforms can be chained directly on the DataFrame using the `.chartkit` accessor:

```python
import pandas as pd

# Load data
df = pd.read_csv('data.csv', index_col=0, parse_dates=True)

# Simple chaining
df.chartkit.variation(horizon='year').plot(title="Annual Variation")

# With metrics and saving
df.chartkit.annualize().plot(metrics=['ath']).save('chart.png')

# Access the transformed DataFrame (without plotting)
df_transformed = df.chartkit.variation(horizon='year').df
```

The accessor returns a `TransformAccessor` that allows chaining as many transformations as needed before finalizing with `.plot()` or accessing the DataFrame via `.df`.

## Unified Input Contract

All transformation functions accept multiple input types:

- `pd.DataFrame` and `pd.Series` (primary types)
- `dict`, `list`, and `np.ndarray` (automatically converted)

Coercion is done internally. Non-numeric columns are filtered with a warning, and `inf`/`-inf` values in the result are replaced with `NaN`.

## Auto-Detection of Frequency

The `variation`, `accum`, and `annualize` functions automatically detect data frequency via `pd.infer_freq`, resolving the appropriate number of periods (e.g., 12 for monthly data, 252 for daily).

You can use the `freq=` parameter as an alternative to `periods=`/`window=`:

```python
# Auto-detect (uses pd.infer_freq)
df_var = variation(df, horizon='year')

# Explicit frequency
df_var = variation(df, horizon='year', freq='M')    # Monthly: 12 periods
df_var = variation(df, horizon='year', freq='Q')    # Quarterly: 4 periods

# Explicit periods (mutually exclusive with freq)
df_var = variation(df, horizon='year', periods=4)   # Direct override
```

Supported frequencies: `D`, `B`, `W`, `M`, `Q`, `Y`, `BME`, `BMS` (including aliases like `daily`, `business`, `weekly`, `monthly`, `quarterly`, `yearly`, `annual` and anchored pandas freq codes like `W-SUN`, `QE-DEC`, `BQE-DEC`, `BYE-DEC`).

If the detected frequency is not supported, a `TransformError` is raised with a message listing valid frequencies and suggesting the use of explicit `periods=`.

---

## Basic Transformations

### variation() - Percentage Variation

Calculates percentage variation between periods with a configurable horizon. The `horizon` determines the number of comparison periods based on data frequency (e.g., `'month'` on monthly data -> 1 period, `'year'` on monthly data -> 12 periods).

```python
def variation(df, horizon: str = "month", periods: int | None = None, freq: str | None = None) -> DataFrame | Series
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | DataFrame \| Series | - | Input data |
| `horizon` | str | `"month"` | Comparison horizon: `'month'` or `'year'` |
| `periods` | int \| None | None | Override for number of periods. Mutually exclusive with `freq` |
| `freq` | str \| None | None | Data frequency (`'D'`, `'M'`, `'Q'`, etc.). Mutually exclusive with `periods` |

**Example:**

```python
import pandas as pd
from chartkit import variation

# Monthly data
df = pd.DataFrame({
    'value': [100, 102, 101, 105]
}, index=pd.date_range('2024-01', periods=4, freq='ME'))

# Month-over-month variation (auto-detect: monthly data -> periods=1)
df_mom = variation(df)
# Result: [NaN, 2.0, -0.98, 3.96]

# Year-over-year variation (auto-detect: monthly data -> periods=12)
df_yoy = variation(df, horizon='year')

# Quarterly data + annual horizon (auto-detect: quarterly -> 4 periods)
df_yoy = variation(df_quarterly, horizon='year')

# Explicit frequency
df_yoy = variation(df, horizon='year', freq='Q')  # Quarterly: 4 periods

# Explicit periods
df_yoy = variation(df, horizon='year', periods=4)

# Via accessor
df.chartkit.variation(horizon='month').plot(title="Monthly Variation")
df.chartkit.variation(horizon='year').plot(title="Annual Variation")
```

---

### accum() - Accumulated in Rolling Window

Calculates accumulated variation via compound product in a rolling window. The window is resolved by the following precedence: explicit `window=` > explicit `freq=` > auto-detect via `pd.infer_freq` > fallback to `config.transforms.accum_window` (default: 12).

**Formula:** `(Product(1 + x/100) - 1) * 100`

```python
def accum(df, window: int | None = None, freq: str | None = None) -> DataFrame | Series
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | DataFrame \| Series | - | Rates in percentage |
| `window` | int \| None | None | Window size in periods. Mutually exclusive with `freq` |
| `freq` | str \| None | None | Data frequency (`'D'`, `'M'`, `'Q'`, etc.). Mutually exclusive with `window` |

**Example:**

```python
from chartkit import accum

# Monthly CPI -> trailing 12-month CPI (auto-detect: monthly -> 12)
cpi_12m = accum(monthly_cpi)

# Explicit 6-month window
cpi_6m = accum(monthly_cpi, window=6)

# Explicit frequency
cpi_12m = accum(monthly_cpi, freq='M')

# Via accessor with plotting
monthly_cpi.chartkit.accum().plot(
    title="CPI Trailing 12 Months",
    units='%'
)
```

---

### diff() - Absolute Difference

Calculates absolute difference between periods. `periods=0` is rejected with `ValidationError` (would return all-zeros, almost certainly a user error).

```python
def diff(df, periods: int = 1) -> DataFrame | Series
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | DataFrame \| Series | - | Data with temporal index |
| `periods` | int | 1 | Periods for difference (must be >= 1) |

**Example:**

```python
from chartkit import diff

# Variation in percentage points
df_diff = diff(selic)  # Difference from previous period

# 12-month difference
df_diff_12m = diff(selic, periods=12)

# Via accessor
selic.chartkit.diff().plot(title="Selic Variation (p.p.)")
```

---

### normalize() - Normalization

Normalizes series to a base value at a specific date. Useful for comparing series with different scales. Uses the first non-NaN value as reference; `base_date` finds the nearest date if the exact date doesn't exist in the index.

```python
def normalize(df, base: int | None = None, base_date: str | None = None) -> DataFrame | Series
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | DataFrame \| Series | - | Data with temporal index |
| `base` | int \| None | None | Base value for normalization (default: `config.transforms.normalize_base`) |
| `base_date` | str \| None | None | Base date. If None, uses first non-NaN value. Finds nearest if exact date doesn't exist |

**Example:**

```python
from chartkit import normalize
import pandas as pd

# Base 100 at first date
df_norm = normalize(df)

# Base 100 at specific date
df_norm = normalize(df, base_date='2020-01-01')

# Compare two series with different scales
series_a = normalize(df['ibovespa'])
series_b = normalize(df['sp500'])

comparison = pd.concat([series_a, series_b], axis=1)
comparison.chartkit.plot(title="Base 100 Comparison")

# Via accessor
df.chartkit.normalize(base_date='2020-01-01').plot(
    title="Normalized Indices (Base 100 = Jan/2020)"
)
```

---

## Statistical Analysis

### drawdown() - Distance from Peak

Calculates the percentage distance from the historical peak (cumulative maximum). Returns values <= 0, where 0 indicates the value is at the peak and negative values indicate the magnitude of the decline.

**Formula:** `(data / cummax - 1) * 100`

Requires strictly positive values. Raises `TransformError` if data contains zero or negative values.

```python
def drawdown(df) -> DataFrame | Series
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | DataFrame \| Series | - | Data with positive values (prices, indices) |

**Example:**

```python
from chartkit import drawdown

# Decline from peak
dd = drawdown(ibovespa)
# Result: [0, -2.3, -5.1, 0, -1.2, ...]

# Via accessor
ibovespa.chartkit.drawdown().plot(
    title="Ibovespa Drawdown",
    units='%'
)
```

---

### zscore() - Statistical Standardization

Transforms the series into standard deviation units relative to the mean. Allows comparing series with completely different units on the same chart. `window=1` is rejected with `ValidationError` (std of 1 value is undefined, would produce all-NaN).

- **Global** (without `window`): `(data - mean) / std`
- **Rolling** (with `window`): `(data - rolling_mean) / rolling_std`

```python
def zscore(df, window: int | None = None) -> DataFrame | Series
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | DataFrame \| Series | - | Input data |
| `window` | int \| None | None | Rolling window (must be >= 2). If None, calculates global z-score |

**Example:**

```python
from chartkit import zscore

# Global z-score
df_z = zscore(df)

# Rolling z-score (12-period window)
df_z = zscore(df, window=12)

# Compare series with different scales
import pandas as pd

df = pd.DataFrame({
    'ibovespa': ibov_values,
    'sp500': sp_values,
})

# Z-score eliminates scale, allows direct comparison
df.chartkit.zscore().plot(title="Ibovespa vs S&P 500 (Z-Score)")
```

---

## Interest Rate Transformations

### annualize() - Annualize Periodic Rate

Annualizes a periodic rate to an annual rate using compound interest. The number of periods per year is automatically resolved by data frequency (e.g., 252 for daily, 12 for monthly). Supports auto-detection of frequency.

**Formula:** `((1 + r/100) ^ periods_per_year - 1) * 100`

```python
def annualize(df, periods: int | None = None, freq: str | None = None) -> DataFrame | Series
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | DataFrame \| Series | - | Rates in % |
| `periods` | int \| None | None | Periods per year for compounding. Mutually exclusive with `freq` |
| `freq` | str \| None | None | Data frequency (`'D'`, `'B'`, `'M'`, `'Q'`, etc.). Mutually exclusive with `periods` |

**Example:**

```python
from chartkit import annualize

# Daily CDI -> annualized CDI (auto-detect: daily -> 252 periods)
annual_cdi = annualize(daily_cdi)

# Explicit frequency
annual_cdi = annualize(daily_cdi, freq='B')  # Business days: 252 periods

# Explicit periods
annual_cdi = annualize(daily_cdi, periods=252)

# Monthly rate -> annualized (auto-detect: monthly -> 12 periods)
annual_rate = annualize(monthly_rate)

# Via accessor
daily_cdi.chartkit.annualize().plot(
    title="Annualized CDI",
    units='%'
)
```

---

### to_month_end() - Normalize to Month-End

Normalizes temporal index to the last day of the month, consolidating monthly observations. Each timestamp is mapped to the last day of its respective month. If multiple rows fall in the same month (e.g., daily data), keeps only the last chronological observation of that month -- the resulting index has no duplicates.

Raises `TypeError` if the index is not a `DatetimeIndex`.

```python
def to_month_end(df) -> DataFrame | Series
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | DataFrame \| Series | - | Data with DatetimeIndex |

**Example:**

```python
from chartkit import to_month_end

# Daily data -> one row per month (last observation)
monthly = to_month_end(daily_prices)

# Align series before operations
selic = to_month_end(selic)
cpi = to_month_end(cpi)

# Now they can be operated together
spread = selic - cpi

# Via accessor
selic.chartkit.to_month_end().plot()
```

---

## Composite Use Cases

### Base 100 Index Comparison

Compare asset performance with different scales:

```python
import pandas as pd
from chartkit import normalize

# Two series with different scales
df = pd.DataFrame({
    'ibovespa': [100000, 105000, 102000, 110000],
    'sp500': [4000, 4200, 4100, 4400],
}, index=pd.date_range('2024-01', periods=4, freq='ME'))

# Normalize to base 100
df_norm = normalize(df)

# Compare evolution
df_norm.chartkit.plot(title="Ibovespa vs S&P500 (Base 100)")
```

### Monthly CPI to 12 Months

Transform monthly variation into annualized accumulated:

```python
# Monthly CPI (e.g., 0.5, 0.3, 0.8, ...)
monthly_cpi.chartkit.accum().plot(
    title="CPI Trailing 12 Months",
    units='%'
)
```

### Daily Selic to Annual Rate

Convert daily CDI/Selic rate to annual equivalent:

```python
# Daily CDI (e.g., 0.0398, 0.0399, ...)
cdi.chartkit.annualize().plot(
    title="CDI - Annual Equivalent Rate",
    units='%'
)
```

### Real Interest Rate (Selic - CPI)

Calculate spread between nominal rate and inflation:

```python
from chartkit import to_month_end, accum

# Align frequencies
selic = to_month_end(monthly_selic)
cpi = to_month_end(monthly_cpi)

# Calculate trailing 12-month accumulated
selic_12m = accum(selic)
cpi_12m = accum(cpi)

# Spread (simplified approximation)
real_rate = selic_12m - cpi_12m
real_rate.chartkit.plot(
    title="Real Interest Rate (Selic - CPI)",
    units='p.p.'
)
```

### Annual Variation with Metric Highlights

Analyze annual variation with automatic metrics:

```python
# GDP or other economic indicator
gdp.chartkit.variation(horizon='year').plot(
    title="GDP Growth (Annual)",
    metrics=['ath', 'atl', 'last'],
    units='%'
)
```

### Complex Chaining

Multiple transformations in sequence:

```python
# Daily rate -> annualized -> annual variation
daily_cdi.chartkit \
    .annualize() \
    .variation(horizon='year') \
    .plot(title="Annualized CDI - Annual Variation")

# Access transformed data without plotting
df_final = daily_cdi.chartkit \
    .annualize() \
    .to_month_end() \
    .df

# Use transformed DataFrame in other operations
df_final.describe()
```
