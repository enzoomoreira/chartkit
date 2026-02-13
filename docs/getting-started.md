# Getting Started

Your first chart in 2 minutes.

## Prerequisites

- Python >= 3.12
- pandas >= 2.2.0

## Installation

```bash
uv add chartkit
```

## First Chart

```python
import pandas as pd
import chartkit  # Registers the .chartkit accessor

# Sample data
df = pd.DataFrame({
    'value': [10.5, 11.2, 10.8, 12.1, 11.9, 13.0]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Basic chart
df.chartkit.plot(title="My First Chart")
```

Importing `chartkit` automatically registers the `.chartkit` accessor on all DataFrames and Series.

```python
# Works with both DataFrame and Series
df.chartkit.plot(title="DataFrame")
df["value"].chartkit.plot(title="Series")
```

### Adding Formatting

```python
# With unit format and source
df.chartkit.plot(
    title="Interest Rate",
    units='%',
    source='BCB'
)
```

### Saving the Chart

```python
# Save and show
df.chartkit.plot(title="Chart").save("chart.png").show()

# Save only
df.chartkit.plot(title="Chart").save("chart.png")
```

### Using Transforms

```python
# Calculate annual variation and plot
df.chartkit.variation(horizon='year').plot(title="Annual Variation", units='%')

# Multiple chaining
df.chartkit.annualize().plot(metrics=['ath']).save('chart.png')
```

### Adding Metrics

```python
# All-time high and moving average
df.chartkit.plot(metrics=['ath', 'ma:12'])

# Target band
df.chartkit.plot(metrics=['band:1.5:4.5', 'hline:3.0'])
```

### First Composition (Layers + Compose)

```python
from chartkit import compose

layer_main = df.chartkit.layer(units='%', highlight=True)
layer_yoy = df.chartkit.variation(horizon='year').layer(
    kind='bar',
    units='%',
    axis='right'
)

compose(layer_main, layer_yoy, title="Level and YoY Variation")
```

## Next Steps

- [Plotting](guide/plotting.md) - Chart types and formatting options
- [Composition](guide/composition.md) - Tutorials and snippets for multi-layer charts
- [Metrics](guide/metrics.md) - Declarative metrics system
- [Transforms](guide/transforms.md) - Temporal transformation functions
- [Configuration](guide/configuration.md) - Customization via TOML
