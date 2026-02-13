# Cookbook

Practical recipes and real-world use cases for Brazilian financial data.

---

## Compose: Price + Volume (Dual Axis)

**Use case:** Plot asset price and traded volume in the same figure with separate y-axes.

```python
import pandas as pd
import chartkit
from chartkit import compose

dates = pd.date_range('2024-01', periods=8, freq='ME')

price = pd.DataFrame({
    'close': [98, 101, 103, 99, 105, 108, 110, 113]
}, index=dates)

volume = pd.DataFrame({
    'volume': [1.1e6, 1.3e6, 1.0e6, 1.6e6, 1.4e6, 1.9e6, 1.8e6, 2.2e6]
}, index=dates)

layer_price = price.chartkit.layer(units='USD', highlight=['last', 'max'], axis='left')
layer_volume = volume.chartkit.layer(kind='bar', units='human', axis='right')

compose(
    layer_price,
    layer_volume,
    title='Price and Volume',
    source='Exchange Feed'
).save('price_volume_dual_axis.png')
```

---

## Compose: YoY vs Accumulated Inflation

**Use case:** Compare year-over-year inflation and accumulated inflation in one composed chart.

```python
import pandas as pd
import chartkit
from chartkit import compose

cpi = pd.DataFrame({
    'cpi': [0.38, 0.46, 0.52, 0.41, 0.35, 0.29, 0.21, 0.18, 0.24, 0.31, 0.43, 0.57,
            0.49, 0.55, 0.62, 0.44, 0.36, 0.33, 0.25, 0.19, 0.27, 0.34, 0.41, 0.58]
}, index=pd.date_range('2023-01', periods=24, freq='ME'))

yoy_layer = cpi.chartkit.variation(horizon='year').layer(
    units='%',
    metrics=['ath', 'atl'],
    axis='left'
)

accum_layer = cpi.chartkit.accum().layer(
    units='%',
    metrics=['ma:6'],
    axis='right'
)

compose(
    yoy_layer,
    accum_layer,
    title='CPI YoY vs Accumulated',
    source='IBGE'
).save('cpi_yoy_vs_accum.png')
```

For more patterns, see [Composition Guide](guide/composition.md).

---

## Trailing 12-Month CPI

**Use case:** Visualize trailing 12-month accumulated inflation with a band indicating the inflation target and its tolerance range.

```python
import pandas as pd
import chartkit

# Monthly CPI data (month-over-month % change)
monthly_cpi = pd.DataFrame({
    'cpi': [0.42, 0.83, 0.16, 0.61, 0.44, 0.26,
            0.12, -0.02, 0.26, 0.24, 0.28, 0.56,
            0.42, 0.83, 0.71, 0.38, 0.46, 0.21]
}, index=pd.date_range('2023-01', periods=18, freq='ME'))

# Transform monthly CPI into trailing 12-month accumulated
# The accum function applies: (Product(1 + x/100) - 1) * 100
cpi_12m = monthly_cpi.chartkit.accum()

# Plot with target band (3% center, 1.5 p.p. tolerance)
cpi_12m.plot(
    title="CPI Trailing 12 Months",
    units='%',
    source='IBGE',
    metrics=[
        'hline:3.0',      # Central target
        'band:1.5:4.5'    # Tolerance band (+/- 1.5 p.p.)
    ]
).save('cpi_12m.png')
```

---

## Selic vs CPI (Real Interest Rate)

**Use case:** Compare the evolution of the Selic rate and trailing CPI to visualize the implied real interest rate.

```python
import pandas as pd
import chartkit
from chartkit import to_month_end

# Selic (target % p.a.) and 12-month CPI (% p.a.) data
data = pd.DataFrame({
    'selic': [13.75, 13.75, 13.75, 13.25, 12.75, 12.25,
              11.75, 11.25, 10.75, 10.50, 10.50, 10.50],
    'cpi_12m': [5.77, 5.60, 4.65, 4.18, 3.94, 3.16,
                3.99, 4.24, 4.42, 4.50, 4.62, 4.51]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

# Normalize indices to month-end (ensures alignment)
data = to_month_end(data)

# Plot both series on the same chart
data.chartkit.plot(
    title="Selic vs CPI 12m",
    units='%',
    source='BCB/IBGE',
    highlight=True
).save('selic_vs_cpi.png')

# Optional: calculate and plot the real interest rate
# Real rate = ((1 + selic/100) / (1 + cpi/100) - 1) * 100
data['real_rate'] = ((1 + data['selic']/100) / (1 + data['cpi_12m']/100) - 1) * 100

data[['real_rate']].chartkit.plot(
    title="Ex-Post Real Interest Rate",
    units='%',
    source='BCB/IBGE',
    metrics=['hline:0']  # Zero reference line
).save('real_rate.png')
```

---

## Base 100 Comparison

**Use case:** Compare the evolution of assets with very different scales (e.g., Ibovespa in thousands vs S&P 500 in thousands, but distinct absolute values).

```python
import pandas as pd
import chartkit
from chartkit import normalize

# Ibovespa and S&P 500 data with different scales
indices = pd.DataFrame({
    'ibovespa': [127500, 128900, 126100, 131200, 129800, 134500,
                 132100, 135800, 133200, 138900, 136500, 140200],
    'sp500': [4770, 4845, 4769, 4958, 4890, 5026,
              4967, 5137, 5078, 5234, 5186, 5321]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

# Normalize both series to base 100 at the first date
# This allows comparing relative percentage variation
indices_norm = normalize(indices, base=100)

# Plot comparison
indices_norm.chartkit.plot(
    title="Ibovespa vs S&P 500 (Base 100)",
    units='points',
    source='B3/NYSE',
    highlight=True
).save('indices_base100.png')

# Alternative: normalize from a specific date
indices_norm_2024 = normalize(indices, base=100, base_date='2024-06-30')

indices_norm_2024.chartkit.plot(
    title="Ibovespa vs S&P 500 (Base 100 at Jun/24)",
    units='points',
    source='B3/NYSE'
).save('indices_base100_jun.png')
```

---

## Annualized CDI

**Use case:** Convert the daily CDI rate (expressed in % per day) to an equivalent annualized rate.

```python
import pandas as pd
import chartkit
from chartkit import annualize

# Daily CDI data (% per day)
# Note: typical daily CDI values are very small (~0.04% per day)
daily_cdi = pd.DataFrame({
    'cdi': [0.0407, 0.0407, 0.0403, 0.0399, 0.0395,
            0.0391, 0.0387, 0.0383, 0.0379, 0.0375,
            0.0371, 0.0367, 0.0363, 0.0359, 0.0355]
}, index=pd.date_range('2024-06-01', periods=15, freq='B'))  # B = business days

# Annualize using compound interest formula
# Formula: ((1 + rate/100) ^ periods_per_year - 1) * 100
# Auto-detect: data with freq='B' (business days) -> 252 periods
annualized_cdi = annualize(daily_cdi)

# Plot annualized CDI
annualized_cdi.chartkit.plot(
    title="Annualized CDI",
    units='%',
    source='CETIP',
    highlight=True,
    metrics=['ath', 'atl']  # Show period high and low
).save('annualized_cdi.png')
```

---

## Year-over-Year Variation with Extremes

**Use case:** Calculate year-over-year variation and highlight extreme values (ATH/ATL) to identify historical peaks and troughs.

```python
import pandas as pd
import chartkit
from chartkit import variation

# Industrial production data (index, base 100)
production = pd.DataFrame({
    'production': [98.5, 99.2, 100.1, 101.3, 100.8, 102.5,
                   103.2, 102.1, 104.5, 105.2, 103.8, 106.1,
                   104.2, 105.8, 107.2, 108.5, 106.9, 109.3,
                   110.1, 108.5, 111.2, 112.5, 110.8, 114.2]
}, index=pd.date_range('2022-01', periods=24, freq='ME'))

# Calculate annual variation (12 periods for monthly data)
production_var = variation(production, horizon='year', periods=12)

# Plot with historical extremes highlighted
production_var.chartkit.plot(
    title="Industrial Production - Annual Variation",
    units='%',
    source='IBGE',
    metrics=['ath', 'atl'],  # All-Time High and All-Time Low
    highlight=True
).save('production_annual.png')

# For quarterly data, use periods=4
quarterly_gdp = pd.DataFrame({
    'gdp': [2.1, 2.3, 2.5, 2.8, 2.2, 2.4, 2.6, 2.9]
}, index=pd.date_range('2022-03', periods=8, freq='QE'))

gdp_var = variation(quarterly_gdp, horizon='year', periods=4)

gdp_var.chartkit.plot(
    title="GDP - Annual Variation",
    units='%',
    source='IBGE',
    metrics=['ath', 'atl']
).save('gdp_annual.png')
```

---

## Series with Moving Average

**Use case:** Smooth a volatile series with a moving average to identify trends.

```python
import pandas as pd
import chartkit

# Retail sales data (seasonally adjusted index)
retail = pd.DataFrame({
    'sales': [102.5, 98.3, 105.2, 101.8, 99.5, 103.2,
              100.1, 97.8, 104.5, 102.2, 98.9, 106.1,
              103.5, 99.2, 107.8, 104.1, 100.5, 108.5,
              105.2, 101.8, 110.2, 106.5, 102.9, 112.1]
}, index=pd.date_range('2022-01', periods=24, freq='ME'))

# Plot with 12-period moving average
retail.chartkit.plot(
    title="Retail Sales with Moving Average",
    units='points',
    source='IBGE',
    metrics=['ma:12'],  # 12-month moving average
    highlight=True
).save('retail_ma12.png')

# Combining moving average with ATH/ATL
retail.chartkit.plot(
    title="Retail Sales - Complete Analysis",
    units='points',
    source='IBGE',
    metrics=[
        'ma:3',   # MA3 for short-term trend
        'ma:12',  # MA12 for long-term trend
        'ath',    # All-time high
        'atl'     # All-time low
    ]
).save('retail_complete.png')
```

---

## Inflation Target

**Use case:** Visualize inflation relative to the Central Bank target, including the tolerance band.

```python
import pandas as pd
import chartkit

# Trailing 12-month CPI data
cpi_12m = pd.DataFrame({
    'cpi': [5.77, 5.60, 4.65, 4.18, 3.94, 3.16,
            3.99, 4.24, 4.42, 4.50, 4.62, 4.51,
            4.56, 4.83, 5.19, 5.26, 5.35, 5.52]
}, index=pd.date_range('2024-01', periods=18, freq='ME'))

# Plot with target and tolerance band
# Inflation target 2024-2025: 3.0% with +/- 1.5 p.p. tolerance
cpi_12m.chartkit.plot(
    title="CPI 12m vs Inflation Target",
    units='%',
    source='IBGE',
    highlight=True,
    metrics=[
        'hline:3.0',      # Central target (dashed line)
        'band:1.5:4.5',   # Tolerance band (shaded area)
        'hline:4.5',      # Target ceiling
        'hline:1.5'       # Target floor
    ]
).save('cpi_target.png')

# Simplified version with band only
cpi_12m.chartkit.plot(
    title="CPI 12m - Target Regime",
    units='%',
    source='IBGE',
    metrics=[
        'hline:3.0',      # Central target
        'band:1.5:4.5'    # Tolerance band
    ]
).save('cpi_target_simple.png')
```

---

## Combining Multiple Techniques

**Use case:** Complete time series analysis combining transforms and overlays.

```python
import pandas as pd
import chartkit
from chartkit import accum, normalize

# Monthly CPI data
monthly_cpi = pd.DataFrame({
    'cpi': [0.42, 0.83, 0.16, 0.61, 0.44, 0.26,
            0.12, -0.02, 0.26, 0.24, 0.28, 0.56,
            0.42, 0.83, 0.71, 0.38, 0.46, 0.21,
            0.35, 0.44, 0.52, 0.39, 0.41, 0.67]
}, index=pd.date_range('2023-01', periods=24, freq='ME'))

# Full pipeline: monthly CPI -> trailing 12m -> plot with metrics
(monthly_cpi
    .chartkit
    .accum()  # Transform to trailing 12-month accumulated
    .plot(
        title="CPI Trailing 12m - Complete Analysis",
        units='%',
        source='IBGE',
        highlight=True,
        metrics=[
            'ma:6',           # 6-month moving average
            'ath',            # All-time high
            'atl',            # All-time low
            'hline:3.0',      # Inflation target
            'band:1.5:4.5'    # Tolerance band
        ]
    )
    .save('cpi_complete_analysis.png')
)
```

---

## Tips and Best Practices

### Series Alignment

Always normalize dates to month-end before combining series from different sources:

```python
from chartkit import to_month_end

selic = to_month_end(selic_raw)
cpi = to_month_end(cpi_raw)
combined = pd.concat([selic, cpi], axis=1)
```

### Choosing Metrics

| Scenario | Recommended Metrics |
|----------|-------------------|
| Inflation vs Target | `hline:target`, `band:floor:ceiling` |
| Volatility | `ma:12`, `ath`, `atl` |
| Trend | `ma:3`, `ma:12` |
| Extreme values | `ath`, `atl` |
| Zero reference | `hline:0` |

### Saving with Quality

```python
# For presentations (higher DPI)
df.chartkit.plot(title="Chart").save('chart.png', dpi=300)

# For web (smaller file size)
df.chartkit.plot(title="Chart").save('chart.png', dpi=100)
```
