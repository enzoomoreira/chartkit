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
| **Artist Obstacle** | `register_artist_obstacle(ax, artist, filled, colocate)` | Path-based obstacle that repels moveable labels |
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
all elements have been registered *and* after `finalize_chart()` has set the
axis limits, tick rotation and margins -- the placement is measured in pixels,
so it has to be computed against the geometry the reader will actually see.

### Disabling the Engine

Pass `collision=False` to skip all collision processing:

```python
# No collision resolution -- useful for simple charts or when
# the engine interferes with a specific layout
df.chartkit.plot(title="Simple Chart", highlight=True, collision=False)

# Also available in compose()
compose(layer1, layer2, title="Composed", collision=False)
```

When disabled, legend obstacle registration and label repositioning are
both skipped entirely.

---

## Manual Usage

For advanced scenarios (custom overlays, custom metrics), use the API
directly:

```python
from chartkit import register_artist_obstacle, register_moveable, register_passive

# Create a label that can be moved
text = ax.text(x, y, "My label", ha="left", va="center")
register_moveable(ax, text)

# Create a reference line as an obstacle (unfilled path)
line = ax.axhline(y=100, color="red", linestyle="--")
register_artist_obstacle(ax, line, filled=False)

# Create a background area that is NOT an obstacle
patch = ax.axhspan(50, 150, alpha=0.1, color="gray")
register_passive(ax, patch)

# Register a data line whose path should repel labels (colocate=True
# allows labels that start ON this line to stay without being repelled)
(plot_line,) = ax.plot(x, y, color="blue")
register_artist_obstacle(ax, plot_line, filled=False, colocate=True)
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

The collision engine runs after all elements are created and before
final decorations:

```
0. Theme scope     with theme.context():  (wraps steps 1-9)
1. Figure          create_figure()
2. Data            extract_plot_data()
3. Y Formatter     FORMATTERS[units]()
4. Plot Core       ChartRenderer dispatch + highlights (register_moveable) + area fills (register_passive)
5. Metrics         ATH/ATL/hline (register_artist_obstacle) + MA (register_artist_obstacle) + band (register_passive)
6. Legend          apply_legend()
7. Finalize        finalize_chart() (tick formatting, rotation, limits, labels, decorations)
8. Collisions      if collision=True: register legend obstacle + resolve_collisions(ax)
9. Debug overlay   if debug=True: draw_debug_overlay(ax) (after collision so placements are final)
-> PlotResult
```

For composed charts, `resolve_composed_collisions(axes)` replaces step 8,
merging labels from all axes (left + right) into a single pool. Similarly,
`draw_composed_debug_overlay(axes)` replaces step 9.

The debug overlay is a separate step from collision resolution. It runs after
`finalize_chart()` so the overlay reflects the final axes geometry (after tick
rotation, `subplots_adjust`, etc.).

### Unified Resolution Algorithm

The engine uses a unified algorithm that handles both fixed obstacles and
inter-label collisions in a single iterative pass with cost-based candidate
selection:

1. **Snapshot anchors**: before any movement, capture the original bounding box of each moveable label as its anchor point
2. **For each label**, collect all `_PathObstacle` instances (lines, patches, collections, labels from other axes)
3. **Co-location skip**: if a label starts ON a `colocate=True` obstacle on the same axes, that obstacle is excluded
4. **Identify collisions**: `Path.intersects_bbox()` for path obstacles, bbox overlap for other moveable labels, plus any part of the label that falls outside the data area -- leaving the axes counts as colliding with the chart's own frame
5. **Generate candidates** from three sources:
   - **Proactive**: 8 cardinal directions (N, NE, E, SE, S, SW, W, NW) at multiple distances (`candidate_distances`), positioned relative to the anchor point. Diagonal distances are normalized for uniformity
   - **Reactive**: snap-to-edge displacements per colliding obstacle (up, down, left, right)
   - **Bounds**: for an out-of-bounds label, the exact correction that brings it back inside, landing at the edge margin rather than flush against the border. The proactive steps are multiples of the label height, which is the right scale for separating two labels but arbitrary against a border -- a label hanging 30px past the spine is not helped by offers of 14, 21 and 28px
6. **Validate** each candidate against ALL obstacles (bbox + path) via `_position_is_free()`
7. **Score valid candidates** with a continuous cost function combining three weighted components:
   - **Distance from anchor** (w=1.0): displacement normalized by label height
   - **Axis preference** (w=3.0): penalizes off-axis movement (e.g., X movement when `movement="y"`)
   - **Edge proximity** (w=5.0): linear penalty when label is within `edge_margin_factor` of any axes border
8. **Select lowest-cost candidate** and apply displacement

```
Example with movement="y" (default):

    Label collides with ATH line and another label.

    Proactive: 8 directions x 3 distances = 24 candidates (from anchor)
    Reactive: snap-to-edge from ATH (UP, DOWN) + from label (UP, DOWN)

    Validate all candidates -> 12 are collision-free
    Score each: UP +15px (cost=1.2), UP +20px (cost=1.8), RIGHT +30px (cost=5.1), ...

    Select UP +15px (lowest cost). Apply.
```

Constraints respected:
- **Movement axis**: configurable (`"y"`, `"x"`, or `"xy"`) -- off-axis penalized, not blocked
- **Axes limits**: candidates that would fall outside the data area are discarded when generated, and a label that starts outside it -- as a highlight label on the last point does -- triggers a resolution that brings it back
- **Edge proximity**: labels near axes borders receive increasing penalty
- **Global validation**: each candidate is tested against every obstacle

The outer loop repeats until no label moves or `max_iterations` is reached. In
practice it converges almost immediately -- roughly 1.25 placements per label
on a chart with 36 of them -- so `max_iterations` is a backstop, not a budget.

### Why this algorithm

Label placement is
[NP-hard](https://idl.cs.washington.edu/files/2021-FastLabels-VIS.pdf) in the
number of labels, so every practical implementation trades optimality for
time. The [canonical
survey](https://www.eecs.harvard.edu/~shieber/Biblio/Papers/tog-final.pdf)
(Christensen, Marks & Shieber, 1995) ranks the families by quality against
runtime: random, then greedy, then gradient descent, then simulated
annealing.

This engine is **candidate-based greedy**, the same family as the labeler
behind Vega-Lite and as `textalloc`. That baseline generates candidate
positions from the standard 8-position model and takes the first one that is
unoccupied. Two things here differ:

- Candidates are 8 directions at several distances, a superset of the fixed
  8-position model.
- Every valid candidate is scored and the cheapest wins, rather than taking
  the first that fits.

The second point is why an early exit from the candidate loop was rejected:
stopping at the first free position is precisely the first-fit behaviour that
cost-based selection replaced.

Moving up the staircase to simulated annealing is not planned. It pays off
when many labels compete for scarce space; these charts place a handful, where
greedy and annealing reach the same answer and only the runtime differs.

`adjustText` and `ggrepel` take the other route -- force-directed repulsion,
iterating toward equilibrium. That suits scatter plots with dozens of
free-floating labels better than it suits a chart whose labels are anchored to
specific points and mostly need to avoid one line.

> **On the occupancy grid.** An occupancy grid was implemented, benchmarked and
> removed after it lost even at 10,000 points. That benchmark varied the number
> of *obstacles*; the cost that actually scales here is the number of *labels*
> times candidates. The two are different axes, and the grid was never measured
> on the one where it would compete. Treat the removal as "not justified for
> the case tested" rather than as a settled result.

### Connectors

If a label was displaced beyond `connector_threshold_px` (default: 30px)
from its original position, a guide line is drawn connecting the original data point
to the repositioned label. Connectors are grouped by parent axes to ensure
correct coordinate transforms in composed charts.

### Obstacle Collection

The engine combines multiple obstacle sources:

1. **Auto-detected patches**: `ax.patches` on all sibling axes sharing the X-axis (bars, boxes, etc.) -> `_path_from_patch()`
2. **Auto-detected collections**: `ax.collections` on siblings (scatter, violin, fill_between) -> `_path_from_collection()`
3. **Cross-axis labels**: labels from twinx sibling axes act as obstacles -> `_path_from_extent()`
4. **Registered artist obstacles**: elements registered via `register_artist_obstacle()` (reference lines, data lines, moving averages, legend) -> unified structural dispatch via `_classify_artist()`

All obstacles are converted to `_PathObstacle` instances with display-space `Path` geometry.
Collision detection uses matplotlib's Cython-based `Path.intersects_bbox()` for precise
intersection against all geometries (lines, patches, collections).

Each obstacle precomputes its geometry once, at construction:

- Per-path bounding boxes, taken from the control points rather than from
  `Path.get_extents()`. The exact version solves for the Bezier extrema with a
  polynomial root-find per segment, and a scatter marker is all curves. The
  control-point hull always contains the curve, so the approximation is
  conservative -- an obstacle may read a pixel or two larger than it draws,
  which pushes labels away rather than letting them overlap.
- A single hull over all of them, so one comparison rejects an entire obstacle
  when the label is nowhere near it.

Only the paths whose boxes actually overlap the label reach `intersects_bbox()`.
A 100-point scatter used to take 45 seconds to resolve against 0.37 without the
engine; `tests/collision/test_collision_perf.py` keeps that from coming back.

Auto-detection traverses all sibling axes (via `get_shared_x_axes().get_siblings(ax)`),
enabling cross-axis collision avoidance in composed charts with `twinx()`.

The engine filters:
- Patches registered as moveable (labels are not obstacles to themselves)
- Patches registered as passive (bands, background areas)
- Patches already registered as fixed (avoids duplication)
- Invisible artists (`get_visible() == False`)

---

## Debug Overlay

Pass `debug=True` to `plot()` or `compose()` to visualize collision bounding boxes
directly on the chart:

```python
# Single chart
df.chartkit.plot(
    title="Debug View",
    highlight=True,
    metrics=["ath"],
    debug=True,
)

# Composed chart
compose(layer1, layer2, title="Debug", debug=True)
```

Internally, `debug=True` triggers standalone functions (`draw_debug_overlay(ax)` for
single charts, `draw_composed_debug_overlay(axes)` for composed charts) that run
**after** `finalize_chart()`. This ensures the overlay reflects the final axes
geometry, including tick rotation and layout adjustments.

The overlay draws translucent shapes over the figure:

| Color | Element |
|-------|---------|
| **Red** | Fixed obstacles (patches, cross-axis labels) with padding |
| **Orange** | Line path obstacles (continuous curves) |
| **Purple** | Collection obstacles (scatter, violin, fill_between) |
| **Gray (dashed)** | Passive obstacles -- filled shapes (bands, area fills, stackplot) render with shaded area; unfilled lines render as path outlines |
| **Blue** | Moveable labels with padding |
| **Green** | Axes bounding box |

This is useful for understanding why labels are positioned where they are
and for diagnosing unexpected collision behavior.

---

## Integration with Custom Metrics

When creating custom metrics via `MetricRegistry.register`, use the
registration functions to integrate with the collision engine:

```python
from chartkit import register_artist_obstacle, register_moveable, register_passive
from chartkit.metrics import MetricRegistry

@MetricRegistry.register("target", param_names=["value"])
def metric_target(ax, x_data, y_data, value: float, **kwargs):
    """Line target with label."""
    # Line as path-based obstacle (unfilled for line geometry)
    line = ax.axhline(y=value, color="green", linestyle="--")
    register_artist_obstacle(ax, line, filled=False)

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
label_padding_px = 2.0          # Padding between labels (px)
max_iterations = 50             # Push-apart iteration limit
candidate_distances = [1.0, 1.5, 2.0]  # Distance multipliers for proactive candidates
edge_margin_factor = 1.0               # Edge margin as fraction of label height
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
| `label_padding_px` | `2.0` | Minimum space between two labels in pixels |
| `max_iterations` | `50` | Maximum number of push-apart iterations between labels |
| `candidate_distances` | `(1.0, 1.5, 2.0)` | Distance multipliers (in label heights) for proactive candidate generation in 8 cardinal directions |
| `edge_margin_factor` | `1.0` | Edge margin as fraction of label height. Labels closer than this to the axes border receive an increasing cost penalty, and it is also the clearance a label rescued from outside the axes is placed at |
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

### Why continuous path intersection instead of Line2D bboxes?

A Line2D's bounding box spans the entire data area (from min to max X and Y).
Using it as a collision obstacle would push labels far away from the chart,
even when the line is nowhere near the label. `_PathObstacle` extracts the
actual display-coordinate path from any Artist and uses `Path.intersects_bbox()`
(Cython/C) for exact segment-level collision detection. This unified approach
handles lines, patches, and collections with a single class, replacing the
previous dual system of bbox obstacles and `_LinePathObstacle`.

### Why isn't `resolve_collisions` public?

Resolution is orchestrated by the `engine.py` pipeline. Custom metrics
register elements and the engine resolves automatically. Exposing
`resolve_collisions` in the public API would encourage manual calls at the wrong
moments in the pipeline (before all elements are registered, for example).

`register_moveable`, `register_artist_obstacle`, and `register_passive` are public because
custom metrics need to register their elements. Resolution itself is the
orchestrator's responsibility.

### Why unified resolution instead of separate phases?

The previous 3-phase design (fixed vs moveables, moveables vs moveables, connectors)
could produce cascading collisions: resolving against a fixed obstacle could push
a label into another label that was already resolved. The unified approach evaluates
each displacement candidate against ALL obstacles simultaneously, producing better
placements in fewer iterations.
