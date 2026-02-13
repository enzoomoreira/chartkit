# Composition Guide (Layers + Compose)

Practical guide for building multi-layer charts with `df.chartkit.layer()` and `compose()`.

Use composition when you need:
- different chart kinds in the same figure (`line` + `bar`)
- dual y-axis (`left` + `right`)
- independent transforms per series before rendering

---

## Mental Model

`plot()` renders immediately.

`layer()` does not render. It captures intent (data + options) and returns a `Layer`.

`compose(*layers)` renders all layers together and returns a `PlotResult`.

```python
from chartkit import compose

left = df_a.chartkit.layer(...)
right = df_b.chartkit.layer(axis='right', ...)

compose(left, right, title="Composed Chart").save("composed.png")
```

---

## Quick Start: Line + Bar

```python
import pandas as pd
import chartkit
from chartkit import compose

dates = pd.date_range("2024-01", periods=6, freq="ME")

price = pd.DataFrame({"close": [100, 105, 102, 108, 111, 115]}, index=dates)
volume = pd.DataFrame({"vol": [1.1e6, 1.4e6, 1.0e6, 1.8e6, 1.6e6, 2.0e6]}, index=dates)

layer_price = price.chartkit.layer(kind="line", units="USD", highlight=True)
layer_volume = volume.chartkit.layer(kind="bar", units="human", axis="right")

compose(
    layer_price,
    layer_volume,
    title="Price and Volume",
    source="Exchange Feed",
).save("price_volume.png")
```

---

## Dual Axis Rules

- At least one layer must be on `axis='left'`.
- Put only comparable units on the same axis.
- If units conflict on the same axis, chartkit emits a warning.

Recommended pattern:

```python
selic_layer = selic.chartkit.layer(units="%", axis="left", highlight=["last", "max"])
dollar_layer = dollar.chartkit.layer(units="BRL", axis="right", highlight=True)

compose(selic_layer, dollar_layer, title="Selic vs Dollar").save("selic_dollar.png")
```

---

## Composition with Transforms

Build each layer from its own transform chain, then compose.

```python
from chartkit import compose

yoy_layer = cpi.chartkit.variation(horizon="year").layer(
    units="%",
    metrics=["ath", "atl"],
    axis="left",
)

accum_layer = cpi.chartkit.accum().layer(
    units="%",
    metrics=["ma:6"],
    axis="right",
)

compose(
    yoy_layer,
    accum_layer,
    title="CPI YoY vs Accumulated",
    source="IBGE",
).save("cpi_compose.png")
```

---

## Snippet Patterns

### 1. Multiple Left-Axis Layers

```python
from chartkit import compose

s1 = df1.chartkit.layer(units="points", highlight=True)
s2 = df2.chartkit.layer(units="points", metrics=["ma:3"])
s3 = df3.chartkit.layer(units="points", kind="line")

compose(s1, s2, s3, title="Three Series, One Axis")
```

### 2. Area + Reference Layer

```python
from chartkit import compose

spread_layer = spread_df.chartkit.layer(
    units="%",
    fill_between=("upper", "lower"),
    highlight="last",
)
target_layer = target_df.chartkit.layer(units="%", metrics=["hline:3.0"], axis="left")

compose(spread_layer, target_layer, title="Spread vs Target")
```

### 3. Collision Debug

```python
from chartkit import compose

compose(layer_a, layer_b, title="Debug Layout", debug=True).show()
```

---

## Common Pitfalls

### All layers on right axis

Invalid:

```python
compose(
    a.chartkit.layer(axis="right"),
    b.chartkit.layer(axis="right"),
)
```

Fix: keep at least one layer on the left axis.

### Mixing unrelated units on one axis

Avoid `%` and `BRL` on the same side unless intentionally normalized first.

### Expecting `layer()` to render

`layer()` only prepares configuration. Rendering happens in `compose()`.

---

## API Pointers

- Full signatures: [API Reference](../reference/api.md#chart-composition)
- Parameter details and general plotting options: [Plotting Guide](plotting.md)
