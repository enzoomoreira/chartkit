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
| **Line Obstacle** | `register_line_obstacle(ax, line)` | Line2D whose data path repels labels via point sampling |

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
from chartkit._internal.collision import register_line_obstacle

# Create a label that can be moved
text = ax.text(x, y, "My label", ha="left", va="center")
register_moveable(ax, text)

# Create a reference line as an obstacle
line = ax.axhline(y=100, color="red", linestyle="--")
register_fixed(ax, line)

# Create a background area that is NOT an obstacle
patch = ax.axhspan(50, 150, alpha=0.1, color="gray")
register_passive(ax, patch)

# Register a line whose visible path should repel labels
(plot_line,) = ax.plot(x, y, color="blue")
register_line_obstacle(ax, plot_line)
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

The collision engine runs at step 7 of the pipeline, after all elements
are created and before final decorations:

```
1. Style           theme.apply()
2. Data            extract_plot_data()
3. Y Formatter     FORMATTERS[units]()
4. Plot Core       ChartRegistry dispatch + highlights (register_moveable)
5. Metrics         ATH/ATL/hline (register_fixed) + MA (register_passive) + band (register_passive)
6. Legend           _apply_legend() + register_fixed(ax, legend_artist)
7. Collisions      resolve_collisions(ax) or resolve_composed_collisions(axes)
8. Decorations     add_title(ax), add_footer(fig)
9. Output          PlotResult
```

For composed charts, `resolve_composed_collisions(axes)` replaces step 7,
merging labels from all axes (left + right) into a single pool.

### Unified Resolution Algorithm

The engine uses a unified algorithm that handles both fixed obstacles and
inter-label collisions in a single iterative pass:

1. **For each label**, build the full obstacle list: all fixed obstacles (padded)
   plus all other labels (padded)
2. **Identify collisions** between the label's padded bbox and each obstacle
3. **Generate displacement candidates** from each colliding obstacle (up, down, left, right)
4. **Sort candidates** by preference: Y-only first, X-only second, diagonal last (by distance within each group)
5. **Filter by movement preference** (`"y"`, `"x"`, or `"xy"`)
6. **Validate** each candidate against ALL obstacles (not just the colliding one)
7. **Fallback**: if no single-axis solution exists, try diagonal combinations (best Y + best X)

```
Example with movement="y" (default):

    Label collides with ATH line and another label.

    Candidates from ATH: UP +15px, DOWN -42px
    Candidates from label: UP +8px, DOWN -20px

    Sorted: UP +8px, UP +15px, DOWN -20px, DOWN -42px

    Validate +8px against ALL obstacles -> still collides with ATH
    Validate +15px against ALL obstacles -> free! Apply.
```

Constraints respected:
- **Movement axis**: configurable (`"y"`, `"x"`, or `"xy"`)
- **Axes limits**: label never leaves the visible chart area
- **Global validation**: each candidate is tested against every obstacle

The outer loop repeats until no label moves or `max_iterations` is reached.

### Connectors

If a label was displaced beyond `connector_threshold_px` (default: 30px)
from its original position, a guide line is drawn connecting the original data point
to the repositioned label. Connectors are grouped by parent axes to ensure
correct coordinate transforms in composed charts.

### Obstacle Collection

The engine combines multiple obstacle sources:

1. **Explicit**: elements registered via `register_fixed()` (ATH, ATL, hline lines, legend)
2. **Auto-detected patches**: `ax.patches` on all sibling axes sharing the X-axis (bars, boxes, etc.)
3. **Cross-axis labels**: labels from twinx sibling axes act as obstacles for each other
4. **Line path samples**: registered lines (`register_line_obstacle()`) are sampled at each data point, creating point-sized virtual obstacles along the visible path

Line2D bounding boxes span the entire data area and are useless as collision targets.
Instead, `_LineSampleObstacle` creates small obstacles at each data point so labels
can be pushed away from the visible line path.

Auto-detection traverses all sibling axes (via `get_shared_x_axes().get_siblings(ax)`),
enabling cross-axis collision avoidance in composed charts with `twinx()`.

The engine filters:
- Patches registered as moveable (labels are not obstacles to themselves)
- Patches registered as passive (bands, background areas)
- Patches already registered as fixed (avoids duplication)
- Invisible artists (`get_visible() == False`)

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

### Why line path sampling instead of Line2D bboxes?

A Line2D's bounding box spans the entire data area (from min to max X and Y).
Using it as a collision obstacle would push labels far away from the chart,
even when the line is nowhere near the label. Sampling at each data point
creates precise, localized obstacles that only repel labels near the actual
visible path.

### Why isn't `resolve_collisions` public?

Resolution is orchestrated by the `engine.py` pipeline. Custom metrics
register elements and the engine resolves automatically at step 7. Exposing
`resolve_collisions` in the public API would encourage manual calls at the wrong
moments in the pipeline (before all elements are registered, for example).

`register_moveable`, `register_fixed`, and `register_passive` are public because
custom metrics need to register their elements. Resolution itself is the
orchestrator's responsibility.

### Why unified resolution instead of separate phases?

The previous 3-phase design (fixed vs moveables, moveables vs moveables, connectors)
could produce cascading collisions: resolving against a fixed obstacle could push
a label into another label that was already resolved. The unified approach evaluates
each displacement candidate against ALL obstacles simultaneously, producing better
placements in fewer iterations.
