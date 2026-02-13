# Extending chartkit

Guide for developers who want to extend chartkit's functionality.

---

## MetricRegistry - Metrics System

chartkit uses a declarative metrics system that allows adding visual
elements to charts via simple strings:

```python
df.chartkit.plot(metrics=['ath', 'atl', 'ma:12', 'hline:5.0'])
```

### Registering Custom Metrics

Use the `@MetricRegistry.register()` decorator to create new metrics:

```python
from chartkit.metrics import MetricRegistry

@MetricRegistry.register('my_metric', param_names=['threshold'])
def my_metric(ax, x_data, y_data, threshold: float):
    """
    Adds a custom horizontal line.

    Args:
        ax: Matplotlib Axes.
        x_data: X-axis data.
        y_data: Y-axis data (Series or DataFrame).
        threshold: Value where the line will be drawn.
    """
    ax.axhline(threshold, color='purple', linestyle='--', linewidth=1.5)

# Usage:
df.chartkit.plot(metrics=['my_metric:10.0'])
```

### Decorator Anatomy

```python
@MetricRegistry.register(
    name='metric_name',                  # Name used in the spec string
    param_names=['param1', 'param2'],    # Names of positional parameters
    uses_series=True,                    # Whether it receives 'series' for multi-column DataFrames
)
def function(ax, x_data, y_data, param1, param2, **kwargs):
    ...
```

**Required function parameters:**
- `ax`: Matplotlib Axes to draw on
- `x_data`: X-axis data (DataFrame index)
- `y_data`: Y-axis data (Series or DataFrame)

**Additional parameters:**
- Defined in `param_names`, extracted from the spec string
- String format: `'name:value1:value2'`
- Values are automatically converted to numbers when possible
- Parameters without a default in the function are treated as required; `parse()` raises `ValueError` if absent

**`uses_series`:**
- Default `True`: the metric receives `series=col` via kwargs when the user
  uses `@` syntax (e.g., `'ath@revenue'`)
- Use `False` for metrics that don't depend on data (e.g., `hline`, `band`)

### Complex Metric Examples

**Metric with multiple parameters:**

```python
@MetricRegistry.register('range', param_names=['min_val', 'max_val', 'color'])
def range_metric(ax, x_data, y_data, min_val: float, max_val: float, color: str = 'gray'):
    """Adds a band between two values."""
    ax.axhspan(min_val, max_val, alpha=0.2, color=color)

# Usage:
df.chartkit.plot(metrics=['range:1.5:4.5:blue'])
```

**Metric that calculates values dynamically:**

```python
@MetricRegistry.register('percentile', param_names=['p'])
def percentile_metric(ax, x_data, y_data, p: int):
    """Adds a line at the specified percentile."""
    import numpy as np

    if hasattr(y_data, 'values'):
        values = y_data.values.flatten()
    else:
        values = y_data.values

    percentile_value = np.nanpercentile(values, p)
    ax.axhline(percentile_value, color='orange', linestyle=':', label=f'P{p}')

# Usage:
df.chartkit.plot(metrics=['percentile:90', 'percentile:10'])
```

### MetricRegistry API

```python
from chartkit.metrics import MetricRegistry, MetricSpec

# List available metrics
MetricRegistry.available()  # ['ath', 'atl', 'band', 'hline', 'ma', ...]

# Manual spec parsing
spec = MetricRegistry.parse('ma:12')
print(spec.name)    # 'ma'
print(spec.params)  # {'window': 12}

# Apply metrics manually (accepts a single string or a list)
MetricRegistry.apply(ax, x_data, y_data, 'ath')
MetricRegistry.apply(ax, x_data, y_data, ['ath', 'ma:12'])

# Clear registry (useful for tests)
MetricRegistry.clear()
```

---

## Creating Custom Transforms

Transforms are functions that transform DataFrames/Series and can be
chained via the accessor.

### Standalone Function

Create a function that accepts DataFrame/Series and returns the same type:

```python
# In src/chartkit/transforms/my_transform.py

import pandas as pd

def my_transform(
    df: pd.DataFrame | pd.Series,
    param1: int = 10
) -> pd.DataFrame | pd.Series:
    """
    Transform description.

    Args:
        df: DataFrame or Series with temporal index.
        param1: Parameter description.

    Returns:
        Transformed DataFrame/Series.

    Example:
        >>> df_transformed = my_transform(df)
    """
    # Your logic here
    return df.rolling(param1).mean()
```

### Integrating with TransformAccessor

To enable chaining via `.chartkit.my_transform()`:

**1. Add the import in `transforms/__init__.py`:**

```python
from .temporal import (
    # ... existing ...
)
from .my_transform import my_transform

__all__ = [
    # ... existing ...
    "my_transform",
]
```

**2. Add the method in `transforms/accessor.py`:**

```python
from .my_transform import my_transform

class TransformAccessor:
    # ... existing methods ...

    def my_transform(self, param1: int = 10) -> TransformAccessor:
        """
        Transform description.

        Args:
            param1: Parameter description.

        Returns:
            New TransformAccessor with transformed data.

        Example:
            >>> df.chartkit.my_transform().plot()
        """
        return TransformAccessor(my_transform(self._df, param1))
```

**3. Optional - Expose in ChartingAccessor (`accessor.py`):**

```python
def my_transform(self, param1: int = 10) -> TransformAccessor:
    """..."""
    return TransformAccessor(self._obj).my_transform(param1)
```

Now you can use:

```python
# Standalone
from chartkit import my_transform
df_new = my_transform(df)

# Chained
df.chartkit.my_transform().plot()
df.chartkit.my_transform().variation(horizon='year').plot()
```

---

## Creating New Chart Types

New chart types are registered via `@ChartRegistry.register()`. The engine
dispatches automatically via `ChartRegistry.get(kind)` -- no need to
modify `engine.py`.

### 1. Create the chart file

The function must follow the `ChartFunc` protocol:

```python
# In src/chartkit/charts/scatter.py

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
from matplotlib.axes import Axes

from ..settings import get_config
from ..styling.theme import theme
from .registry import ChartRegistry

if TYPE_CHECKING:
    from ..overlays.markers import HighlightMode


@ChartRegistry.register("scatter")
def plot_scatter(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.DataFrame | pd.Series,
    highlight: list[HighlightMode] | None = None,
    size: int = 50,
    alpha: float = 0.7,
    **kwargs,
) -> None:
    config = get_config()

    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()

    colors = theme.colors.cycle()

    for i, col in enumerate(y_data.columns):
        color = colors[i % len(colors)]
        ax.scatter(
            x,
            y_data[col],
            s=size,
            alpha=alpha,
            color=color,
            label=col,
            **kwargs,
        )

    if len(y_data.columns) > 1:
        ax.legend()
```

### 2. Import in `charts/__init__.py`

The import triggers automatic registration via decorator:

```python
from .registry import ChartRegistry
from .bar import plot_bar
from .line import plot_line
from .scatter import plot_scatter  # Import triggers @ChartRegistry.register("scatter")

__all__ = ["ChartRegistry", "plot_bar", "plot_line", "plot_scatter"]
```

No need to modify `engine.py`. Dispatch is automatic:

```python
# engine.py (already existing)
chart_fn = ChartRegistry.get(kind)
chart_fn(ax, x_data, y_data, highlight=highlight, **kwargs)
```

Usage:

```python
df.chartkit.plot(kind='scatter', size=100, alpha=0.5)
```

---

## Creating New Overlays

Overlays are secondary visual elements (moving averages, reference lines, etc.).

### 1. Create the overlay file

```python
# In src/chartkit/overlays/trend_line.py

import numpy as np
from ..settings import get_config

def add_trend_line(
    ax,
    x_data,
    y_data,
    color: str = None,
    linestyle: str = '--',
    **kwargs
) -> None:
    """
    Adds a linear trend line.

    Args:
        ax: Matplotlib Axes.
        x_data: X-axis data.
        y_data: Y-axis data.
        color: Line color.
        linestyle: Line style.
    """
    config = get_config()
    color = color or config.colors.secondary

    # Convert x to numeric if needed
    x_numeric = np.arange(len(x_data))
    y_values = y_data.values.flatten() if hasattr(y_data, 'values') else y_data

    # Remove NaNs for fit
    mask = ~np.isnan(y_values)
    coeffs = np.polyfit(x_numeric[mask], y_values[mask], 1)
    trend = np.poly1d(coeffs)(x_numeric)

    ax.plot(
        x_data,
        trend,
        color=color,
        linestyle=linestyle,
        zorder=2,
        label='Trend',
        **kwargs
    )
```

### 2. Export in `overlays/__init__.py`

```python
from .trend_line import add_trend_line  # New

__all__ = [
    # ... existing ...
    "add_trend_line",
]
```

### 3. Integrate with the Collision Engine

Overlays that create visual elements should register them with the collision engine
so that labels are automatically repositioned. Use the appropriate category:

```python
from .._internal.collision import register_fixed, register_moveable, register_passive

# Reference lines: obstacles that labels must avoid
line = ax.axhline(y=value, ...)
register_fixed(ax, line)

# Text labels: can be repositioned
text = ax.text(x, y, "Label", ...)
register_moveable(ax, text)

# Background areas: exist visually but are not obstacles
patch = ax.axhspan(lower, upper, alpha=0.1, ...)
register_passive(ax, patch)
```

Overlays that exist visually but shouldn't block labels (like moving averages)
should be registered as passive:

```python
lines = ax.plot(x, ma_values, color=line_color, ...)
register_passive(ax, lines[0])
```

For more details, see the [collision engine guide](../guide/collision.md).

### 4. Optional - Create a metric for the overlay

```python
# In src/chartkit/metrics/builtin.py (or new file)

from ..overlays import add_trend_line

@MetricRegistry.register("trend")
def metric_trend(ax, x_data, y_data, **kwargs) -> None:
    """
    Adds a trend line.

    Usage: metrics=['trend']
    """
    add_trend_line(ax, x_data, y_data, **kwargs)
```

Now you can use:

```python
# Via direct API
from chartkit.overlays import add_trend_line
add_trend_line(ax, x_data, y_data)

# Via metrics
df.chartkit.plot(metrics=['ath', 'trend'])
```

---

## Configuration Hooks

### Adding New Config Sections

**1. Define the model in `settings/schema.py`:**

```python
from pydantic import BaseModel, Field

class MyConfig(BaseModel):
    enabled: bool = True
    threshold: float = 0.5
    color: str = "#FF0000"
```

**2. Add to `ChartingConfig`:**

```python
class ChartingConfig(BaseSettings):
    # ... existing ...
    my_config: MyConfig = Field(default_factory=MyConfig)
```

Defaults are defined in the pydantic model fields themselves -- there is no
separate `defaults.py` file.

**3. Use via `get_config()`:**

```python
from chartkit.settings import get_config

def my_function():
    config = get_config()
    if config.my_config.enabled:
        threshold = config.my_config.threshold
        # ...
```

**4. Configure via TOML:**

```toml
# .charting.toml
[my_config]
enabled = true
threshold = 0.75
color = "#00FF00"
```

### Adding New Formatters

**1. Implement in `styling/formatters.py`:**

```python
def my_formatter(prefix: str = ""):
    """
    Custom formatter.

    Args:
        prefix: Prefix for values.

    Returns:
        FuncFormatter for use with matplotlib.
    """
    config = get_config()
    locale = config.formatters.locale

    def _format(x, pos):
        formatted = f"{x:,.2f}"
        formatted = formatted.replace(",", locale.thousands)
        return f"{prefix}{formatted}"

    return FuncFormatter(_format)
```

**2. Add to the dispatch table in `_internal/formatting.py`:**

```python
from ..styling import my_formatter

FORMATTERS = {
    # ... existing ...
    'custom': my_formatter,
    'prefix_R': lambda: my_formatter('R '),
}
```

Usage:

```python
df.chartkit.plot(units='custom')
df.chartkit.plot(units='prefix_R')
```

---

## Best Practices

### Imports

- Use relative imports within the package (`from ..settings import get_config`)
- Avoid circular imports (consult the dependency graph in architecture.md)

### Documentation

- Docstrings in Google format
- Type hints on all functions
- Usage examples in docstrings

### Tests

- The test suite uses autouse fixtures for state isolation (see [Testing](testing.md))
- Group tests by category using classes (`TestCorrectness`, `TestEdgeCases`, `TestErrors`)
- Use known-value fixtures with pre-calculated expected results
- Use `pytest.approx()` for float comparisons
- Use `pytest.raises(ExceptionType, match="pattern")` for error tests

### Parameter Defaults

When a parameter can come from config, use `None` as default:

```python
def my_function(alpha=None):
    config = get_config()
    alpha = alpha if alpha is not None else config.my_section.alpha
```
