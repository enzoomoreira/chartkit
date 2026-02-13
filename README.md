# chartkit

Standardized charting library for financial data visualization.

Generate professional charts via Pandas Accessor with a single line of code.

## Installation

```bash
uv add chartkit
```

## Quick Start

```python
import pandas as pd
import chartkit  # Registers the .chartkit accessor

# Sample data
df = pd.DataFrame({
    'rate': [10.5, 11.2, 10.8, 12.1, 11.9, 13.0]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Line chart
df.chartkit.plot(title="Interest Rate", units='%', source='BCB')

# Bar chart
df.chartkit.variation().plot(kind='bar', title="Monthly Variation", units='%', highlight=['last'])

# Chart with metrics (ATH, moving average, etc)
df.chartkit.plot(title="Analysis", metrics=['ath|Maximum', 'atl|Minimum', 'ma:12|Moving Average'])

# Full chaining
df.chartkit.variation().plot(title="Monthly Variation").show()
```

### Composition Quick Example

```python
from chartkit import compose

layer_rate = df.chartkit.layer(units='%', highlight=True)
layer_variation = df.chartkit.variation().layer(kind='bar', units='%', axis='right')

compose(layer_rate, layer_variation, title="Rate and Monthly Variation", source="BCB")
```

## Features

- **Pandas Accessor**: Use `df.chartkit.plot()` directly on any DataFrame
- **Charts**: Line, bar, and stacked bar charts with professional styling
- **Chart Composition**: Combine multiple layers with dual-axis support via `compose()` for complex multi-series charts
- **Formatters**: BRL, USD, BRL_compact, USD_compact, %, points, human-readable notation (1k, 1M)
- **Declarative Metrics**: `metrics=['ath', 'atl', 'ma:12', 'hline:3.0', 'band:1.5:4.5', 'target:1000', 'std_band:20:2', 'vband:2020-03:2020-06']`
- **Chained Transforms**: `df.chartkit.variation(horizon='year').drawdown().plot()` with method chaining and frequency auto-detection
- **Overlays**: Area between series (`fill_between`), standard deviation bands, vertical bands
- **ChartRegistry**: Pluggable chart type system via decorator
- **TOML + Env Var Configuration**: Customize via TOML file or environment variables (`CHARTKIT_*`)

## Documentation

### Getting Started

- [Getting Started](docs/getting-started.md) - Your first chart in 2 minutes
- [Cookbook](docs/cookbook.md) - Practical recipes for financial data

### Guides

| Guide | Description |
|-------|-------------|
| [Plotting](docs/guide/plotting.md) | Chart types, formatting, composition, and PlotResult |
| [Composition](docs/guide/composition.md) | Tutorials and snippets for `layer()` + `compose()` |
| [Metrics](docs/guide/metrics.md) | Declarative metrics system |
| [Transforms](docs/guide/transforms.md) | Temporal transformations and chaining |
| [Configuration](docs/guide/configuration.md) | TOML, paths, and auto-discovery |

### Reference

- [API Reference](docs/reference/api.md) - Signatures, types, and parameters

### For Contributors

| Document | Description |
|----------|-------------|
| [Architecture](docs/contributing/architecture.md) | Overview and data flow |
| [Extending](docs/contributing/extending.md) | MetricRegistry and extensibility |
| [Internals](docs/contributing/internals.md) | Thread-safety, caching, and logging |
| [Testing](docs/contributing/testing.md) | Test suite, fixtures, and patterns |

## Requirements

- Python >= 3.12
- pandas >= 2.2.0
- matplotlib >= 3.10.0
- numpy >= 2.0.0
- pydantic-settings >= 2.12.0
- Babel >= 2.17.0
- loguru >= 0.7.3
- cachetools >= 6.2.6
