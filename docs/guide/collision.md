# Collision Engine

Automatic collision resolution engine for chart visual elements.

When a chart has multiple labels, reference lines, and bars, these
elements compete for the same visual space. The collision engine repositions
labels automatically to eliminate overlaps, producing readable charts
without manual intervention.

---

## Concept

The engine is **type-agnostic**. It doesn't know what a "label", a "bar",
or an "ATH line" is. It only sees rectangles (bounding boxes) in screen pixels
and three participation categories:

| Category | Function | Meaning |
|----------|----------|---------|
| **Moveable** | `register_moveable(ax, artist)` | Can be repositioned to resolve collisions |
| **Fixed** | `register_fixed(ax, artist)` | Immutable obstacle that others must avoid |
| **Passive** | `register_passive(ax, artist)` | Exists visually but doesn't participate in collision |

Each external module decides how to classify its own elements. The engine
provides the building blocks; modules handle the integration.

---

## Automatic Usage

In most cases, the collision engine works automatically. Just use
metrics and highlights:

```python
# Labels and lines are registered automatically
df.chartkit.plot(
    metrics=["ath", "atl", "hline:3.0", "band:1.5:4.5"],
    highlight=True,
)
```

Internally, the `engine.py` pipeline calls `resolve_collisions(ax)` after
all elements have been registered.

---

## Manual Usage

For advanced scenarios (custom overlays, custom metrics), use the API
directly:

```python
from chartkit import register_moveable, register_fixed, register_passive

# Create a label that can be moved
text = ax.text(x, y, "My label", ha="left", va="center")
register_moveable(ax, text)

# Create a reference line as an obstacle
line = ax.axhline(y=100, color="red", linestyle="--")
register_fixed(ax, line)

# Create a background area that is NOT an obstacle
patch = ax.axhspan(50, 150, alpha=0.1, color="gray")
register_passive(ax, patch)
```

> **Important**: Use `ax.text()`, not `ax.annotate()`. `ax.text()` natively uses
> `transData`, allowing programmatic repositioning via
> `get_position()`/`set_position()`. `ax.annotate(textcoords="offset points")`
> uses custom transforms incompatible with the engine.

---

## How It Works

### Internal State

The collision state (which artists are moveable, fixed, passive) is stored
in module-level `WeakKeyDictionary` indexed by `Axes`. This means:

- **Automatic cleanup**: when an `Axes` is destroyed by the GC, its entries
  are automatically removed. There is no risk of memory leak.
- **No namespace pollution**: no private attribute is added to
  matplotlib objects (previously used `ax._charting_labels`, etc.).

### Rendering Pipeline

The collision engine runs at step 6 of the pipeline, after all elements
are created and before final decorations:

```
1. Style           theme.apply()
2. Data            resolve x_data, y_data
3. Y Formatter     ax.yaxis.set_major_formatter(...)
4. Plot Core       ChartRegistry dispatch + highlights (register_moveable)
5. Metrics         ATH/ATL/hline (register_fixed) + MA (register_passive) + band (register_passive)
6. Collisions      resolve_collisions(ax)
7. Title/Footer    ax.set_title(), fig.text()
8. Output          PlotResult
```

### 3-Phase Algorithm

#### Phase 1: Moveables vs Fixed

For each moveable, checks collision against all fixed obstacles.
If there's a collision, calculates the **smallest possible displacement** among up to 4 directions:

```
Example with movement="y" (default):

    Label collides with ATH line.

    UP:   move label above the line   -> 15px
    DOWN: move label below the line   -> 42px

    Smallest: UP (15px). Label moves up 15px.
```

Constraints respected:
- **Movement axis**: configurable (`"y"`, `"x"`, or `"xy"`)
- **Axes limits**: label never leaves the visible chart area

If no direction is valid (label trapped between obstacles and axes border),
the label remains at its original position.

#### Phase 2: Moveables vs Moveables

Iterative push-apart between label pairs. When two labels collide, both
are pushed in opposite directions by half the overlap + padding:

```
    Label A and Label B overlapping on Y by 20px:

    shift = 20/2 + padding/2 = 12px

    Label A (higher): moves up 12px
    Label B (lower): moves down 12px
```

Repeats until convergence (no pair collides) or `max_iterations` is reached.

#### Phase 3: Connectors

If a label was displaced beyond `connector_threshold_px` (default: 30px)
from its original position, a guide line is drawn connecting the original data point
to the repositioned label. Preserves the data-label visual association.

### Obstacle Collection

The engine combines two obstacle sources:

1. **Explicit**: elements registered via `register_fixed()` (ATH, ATL, hline lines)
2. **Auto-detected**: all `ax.patches` (bar chart bars)

Auto-detection exists so that bars are automatically obstacles without
manual registration. However, not every patch is an obstacle - shaded bands
(`ax.axhspan`) also create patches, but are transparent background elements.

To exclude a patch from auto-detection, use `register_passive()`. The engine
filters:
- Patches registered as moveable (labels are not obstacles to themselves)
- Patches registered as passive (bands, background areas)
- Patches already registered as fixed (avoids duplication)

---

## Integration with Custom Metrics

When creating custom metrics via `MetricRegistry.register`, use the
registration functions to integrate with the collision engine:

```python
from chartkit import register_fixed, register_moveable, register_passive
from chartkit.metrics import MetricRegistry

@MetricRegistry.register("target", param_names=["value"])
def metric_target(ax, x_data, y_data, value: float, **kwargs):
    """Line target with label."""
    # Line as fixed obstacle
    line = ax.axhline(y=value, color="green", linestyle="--")
    register_fixed(ax, line)

    # Label as moveable
    text = ax.text(
        x_data[-1], value, f"  Meta: {value}",
        ha="left", va="center", color="green",
    )
    register_moveable(ax, text)

# Usage:
df.chartkit.plot(metrics=["target:100", "ath"], highlight=True)
# The engine resolves collisions between the "Target: 100" label, the
# highlight label, the ATH line, and the target line automatically.
```

If your metric creates a background area that shouldn't be an obstacle:

```python
@MetricRegistry.register("zone", param_names=["lower", "upper"], uses_series=False)
def metric_zone(ax, x_data, y_data, lower: float, upper: float, **kwargs):
    """Shaded zone (non-obstacle)."""
    patch = ax.axhspan(lower, upper, alpha=0.1, color="blue")
    register_passive(ax, patch)
```

---

## Configuration

All engine parameters are configurable via TOML:

```toml
[collision]
movement = "y"                  # Displacement axis: "y", "x", or "xy"
obstacle_padding_px = 8.0       # Padding between label and obstacle (px)
label_padding_px = 4.0          # Padding between labels (px)
max_iterations = 50             # Push-apart iteration limit
connector_threshold_px = 30.0   # Minimum distance to draw connector (px)
connector_alpha = 0.6           # Connector line transparency
connector_style = "-"           # Connector line style ("-", "--", ":", "-.")
connector_width = 1.0           # Connector line width
```

Or via `configure()`:

```python
from chartkit import configure

configure(collision={
    "movement": "xy",
    "connector_threshold_px": 50.0,
})
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `movement` | `"y"` | Allowed displacement axis. `"y"` is recommended for time series (preserves temporal position on X-axis) |
| `obstacle_padding_px` | `8.0` | Minimum space between label and obstacle in pixels |
| `label_padding_px` | `4.0` | Minimum space between two labels in pixels |
| `max_iterations` | `50` | Maximum number of push-apart iterations between labels |
| `connector_threshold_px` | `30.0` | Minimum displacement distance (px) to draw guide line |
| `connector_alpha` | `0.6` | Guide line transparency (0.0 = invisible, 1.0 = opaque) |
| `connector_style` | `"-"` | Matplotlib style for guide line |
| `connector_width` | `1.0` | Guide line width in points |

---

## Design Decisions

### Why type-agnostic?

The engine never does `isinstance(artist, Text)` or `isinstance(patch, Rectangle)`.
For moveables, it uses a `PositionableArtist` Protocol (`runtime_checkable`) that
structurally verifies whether the artist has `get_position()`, `set_position()`, and
`get_window_extent()`. For obstacles, it works exclusively with
`Artist.get_window_extent(renderer)`, which returns a `Bbox` in display pixels.

If tomorrow we add a new type of overlay (e.g., annotations, arrows, boxes),
it works with the engine without modifying a single line of it -- it just needs
to implement the Protocol methods. The classification responsibility belongs to
the module that creates the element.

### Why display pixels?

Data coordinates can be dates, percentages, currencies - incomparable units
between X and Y. Display pixels are uniform and allow:
- Direct comparison between bboxes of elements on different axes
- Consistent visual padding regardless of zoom or scale
- Direct use of matplotlib's `Bbox.overlaps()`

### Why `movement="y"` as default?

In time series (primary use case), the X-axis represents time. Displacing
a label horizontally would break the temporal association - the "December" label
would appear over "November". Restricting movement to the Y-axis preserves the
temporal position and produces intuitive results.

### Why 3 categories (moveable/fixed/passive)?

Two categories (moveable/fixed) are not sufficient. Auto-detection of
`ax.patches` as obstacles is necessary for bars, but `ax.axhspan()` also
creates patches. Without the third category, semi-transparent background bands would
be treated as giant obstacles, pushing labels outside the band area.

The alternative would be for the engine to check types (`isinstance(patch, Polygon)`) or
properties (`alpha < 0.5`), but this would break agnosticism. The correct solution:
the module that creates the element knows what it is and self-classifies.

### Why isn't `resolve_collisions` public?

Resolution is orchestrated by the `engine.py` pipeline. Custom metrics
register elements and the engine resolves automatically at step 6. Exposing
`resolve_collisions` in the public API would encourage manual calls at the wrong
moments in the pipeline (before all elements are registered, for example).

`register_moveable`, `register_fixed`, and `register_passive` are public because
custom metrics need to register their elements. Resolution itself is the
orchestrator's responsibility.
