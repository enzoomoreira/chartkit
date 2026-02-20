# Architecture

Internal architecture documentation for chartkit contributors.

---

## Component Diagram

```
                    +-------------------+
                    |    DataFrame      |
                    +-------------------+
                            |
                            v
                    +-------------------+
                    | ChartingAccessor  |  (df.chartkit)
                    +-------------------+
                      |       |       |
          +-----------+       |       +-----------+
          v                   v                   v
  +-------------------+ +-----------+ +-------------------+
  | TransformAccessor | |  .layer() | |  ChartingPlotter  |
  +-------------------+ +-----------+ +-------------------+
          |                   |               |
          v                   v               v
  +-------------------+ +-----------+ +-------------------+
  |   Transforms      | |   Layer   | |     PlotResult    |
  +-------------------+ +-----------+ +-------------------+
                              |               ^
                              v               |
                        +-----------+         |
                        | compose() |---------+
                        +-----------+
                              |
                    +---------+---------+
                    v                   v
            +------------+      +------------+
            | ax (left)  |      | ax (right) |
            +------------+      +------------+
```

---

## Data Flow

The main data flow follows the chain:

```
DataFrame -> Accessor -> Plotter -> PlotResult
```

### Detailed Description

1. **DataFrame**: Input data (pandas DataFrame with DatetimeIndex)

2. **ChartingAccessor**: Registered via `@pd.api.extensions.register_dataframe_accessor("chartkit")` and `@pd.api.extensions.register_series_accessor("chartkit")`. Works as the entry point for all operations. Series are converted to DataFrame internally.

3. **TransformAccessor** (optional): When the user calls transforms like `.variation()`, `.accum()`, etc., a TransformAccessor is returned. Each transform returns a new TransformAccessor, enabling chaining.

4. **Two rendering paths**:

   - **Direct** (`plot()`): `ChartingPlotter` orchestrates single-chart creation on one axes
   - **Composed** (`layer()` + `compose()`): `Layer` captures intent without rendering; `compose()` orchestrates multi-layer rendering with optional dual axes via `twinx()`

5. **ChartingPlotter**: Main engine for direct plotting:
   - Applies theme via `theme.apply()`
   - Extracts data via `extract_plot_data()`
   - Applies axis formatters via `FORMATTERS` dispatch table
   - Dispatches via `ChartRenderer.render(ax, kind, ...)` (enhancer or generic `ax.{kind}()`)
   - Applies metrics via `MetricRegistry.apply()`
   - Applies tick formatting via `apply_tick_formatting()` (data-aligned ticks, auto-inference, phantom tick clipping)
   - Applies tick rotation via `apply_tick_rotation()` (auto-detect overlap or fixed angle)
   - Applies legend
   - Resolves label collisions via `resolve_collisions(ax)` (when `collision=True`)
   - Adds decorations via `add_title(ax)` and `add_footer(fig)`

6. **compose()**: Orchestrator for multi-layer charts:
   - Creates figure with optional twinx for right axis
   - Renders each layer on its target axes
   - Consolidates legend from both axes
   - Resolves cross-axis collisions via `resolve_composed_collisions(axes)`
   - Returns `PlotResult` with `_ComposePlotter` (satisfies `Saveable` Protocol)

7. **PlotResult**: Encapsulated result with:
   - Reference to Figure and Axes
   - `plotter: Saveable` (Protocol-based, works with both ChartingPlotter and _ComposePlotter)
   - `.save()` and `.show()` methods for chaining
   - `.axes` and `.figure` properties for direct access

### Detailed Visual Flow

```mermaid
flowchart TD
    A[DataFrame] --> B["df.chartkit.plot()"]
    B --> C["ChartingAccessor.plot()"]
    C --> D["ChartingPlotter.plot()"]

    D --> D1["1. get_config()"]
    D1 --> D2["2. theme.apply()"]
    D2 --> D3["3. extract_plot_data()"]
    D3 --> D4["4. FORMATTERS[units]()"]
    D4 --> D5["5. ChartRenderer.render(kind)"]
    D5 --> D6["6. MetricRegistry.apply()"]
    D6 --> D6c["7. apply_tick_formatting(x_data)"]
    D6c --> D6d["8. apply_tick_rotation()"]
    D6d --> D6b["9. _apply_legend()"]
    D6b --> D7["10. resolve_collisions() (if collision=True)"]
    D7 --> D7a["11. set xlim/ylim (coerce_axis_limits)"]
    D7a --> D7b["12. set xlabel/ylabel (if provided)"]
    D7b --> D8["13. add_title()"]
    D8 --> D9["14. add_footer()"]
    D9 --> E["PlotResult"]
```

---

## Folder Structure

```
src/chartkit/
├── __init__.py           # Entry point, public exports, __getattr__ lazy paths
├── _logging.py           # Logging setup (loguru disable + configure_logging)
├── accessor.py           # Pandas DataFrame/Series accessor (.chartkit)
├── engine.py             # ChartingPlotter - main orchestrator
├── result.py             # PlotResult - chainable result
├── exceptions.py         # ChartKitError (base) and TransformError
│
├── settings/             # Configuration system (pydantic-settings)
│   ├── __init__.py       # Exports: configure, get_config, ChartingConfig
│   ├── schema.py         # Pydantic BaseModel sub-configs + BaseSettings root
│   ├── loader.py         # ConfigLoader singleton + TOML loading + path resolution
│   └── discovery.py      # find_project_root (cached) + find_config_files
│
├── styling/              # Theme and formatters
│   ├── __init__.py       # Facade
│   ├── theme.py          # ChartingTheme (uses settings)
│   ├── formatters.py     # Y-axis formatters (Babel i18n)
│   └── fonts.py          # Custom font loading
│
├── charts/               # Generic rendering + enhancers
│   ├── __init__.py       # Enhancer imports trigger automatic registration
│   ├── renderer.py       # ChartRenderer - generic rendering (ax.{kind}()) + enhancer dispatch
│   ├── _helpers.py       # Shared utilities (detect_bar_width, is_categorical_index, prepare_categorical_axis, apply_y_origin, validate_y_origin)
│   └── enhancers/        # Specialized handlers for complex chart types
│       ├── __init__.py   # Auto-imports all enhancers (triggers registration)
│       ├── area.py       # Area chart enhancer (fill_between semantics)
│       ├── bar.py        # Bar + barh enhancer (grouped bars, sort, color='cycle')
│       ├── ecdf.py       # Empirical CDF enhancer
│       ├── eventplot.py  # Event position enhancer
│       ├── hist.py       # Histogram enhancer
│       ├── pie.py        # Pie chart enhancer
│       ├── stackplot.py  # Stacked area enhancer
│       ├── stacked_bar.py # Stacked bar enhancer (categorical support)
│       ├── stairs.py     # Step function enhancer
│       ├── statistical.py # Boxplot + violinplot enhancer
│       └── stem.py       # Stem plot enhancer
│
├── composing/            # Multi-layer chart composition
│   ├── __init__.py       # Facade: compose, Layer, AxisSide, create_layer
│   ├── layer.py          # Layer (frozen dataclass) + AxisSide + create_layer()
│   └── compose.py        # compose() orchestrator + _ComposePlotter (Saveable)
│
├── overlays/             # Secondary visual elements
│   ├── __init__.py       # Facade
│   ├── moving_average.py # Moving average
│   ├── reference_lines.py# ATH, ATL, AVG, hlines, target
│   ├── bands.py          # Shaded bands
│   ├── std_band.py       # Standard deviation band (Bollinger Band)
│   ├── vband.py          # Vertical band between dates
│   └── markers.py        # HighlightStyle + unified add_highlight (last/max/min/all)
│
├── decorations/          # Visual decorations
│   ├── __init__.py       # Facade: add_footer, add_title
│   ├── footer.py         # Footer with branding
│   └── title.py          # Styled title on axes
│
├── metrics/              # Declarative metrics system
│   ├── __init__.py       # Exports, registers builtin metrics
│   ├── registry.py       # MetricRegistry - registration and application
│   └── builtin.py        # Standard metrics (ath, atl, ma, hline, band, target, std_band, vband)
│
├── transforms/           # Temporal transformations
│   ├── __init__.py       # Facade: variation, accum, drawdown, zscore, etc.
│   ├── temporal.py       # Transformation function implementations
│   ├── _validation.py    # Validation, coercion, and frequency resolution
│   └── accessor.py       # TransformAccessor for chaining
│
└── _internal/            # Private utilities (shared between engine and compose)
    ├── __init__.py       # Facade: collision, extraction, formatting, highlight, saving, validation
    ├── collision/        # Collision engine (modularized package)
    │   ├── __init__.py   # Re-exports public API (register_*, resolve_*)
    │   ├── _registry.py  # Global state and artist registration (WeakKeyDictionary)
    │   ├── _obstacles.py # _PathObstacle and obstacle collection
    │   ├── _engine.py    # Collision resolution algorithm
    │   └── _debug.py     # Debug overlay rendering
    ├── extraction.py     # extract_plot_data(), should_show_legend(), resolve_series()
    ├── formatting.py     # FORMATTERS dispatch table for Y-axis
    ├── highlight.py      # normalize_highlight()
    ├── plot_validation.py # validate_plot_params(), PlotParamsModel, UnitFormat
    ├── saving.py         # save_figure() with path resolution
    ├── tick_formatting.py # apply_tick_formatting(x_data) - data-aware date locator/formatter for X-axis
    └── tick_rotation.py  # apply_tick_rotation() - auto/fixed X-axis label rotation

tests/                    # Test suite (357 tests)
├── conftest.py           # Shared fixtures (financial DataFrames, edge cases, Agg backend)
├── charts/               # Chart rendering tests (67)
├── collision/            # Collision engine tests (9)
├── composing/            # Composition system tests (29)
├── formatting/           # Formatters and highlight tests (41)
├── integration/          # End-to-end tests (18)
├── metrics/              # MetricRegistry tests (28)
├── settings/             # Configuration system tests (23)
└── transforms/           # Transform function tests (142)
```

---

## Module Responsibilities

### Core

| Module | Responsibility |
|--------|---------------|
| `_logging.py` | loguru setup (`logger.disable`) + `configure_logging()` |
| `accessor.py` | Registers `.chartkit` on DataFrames and Series; delegates to TransformAccessor, ChartingPlotter, or create_layer |
| `engine.py` | Orchestrates single-chart creation; delegates to `_internal` and `decorations` |
| `result.py` | Encapsulates result (`Saveable` Protocol); enables chaining with `.save()` and `.show()` |

### Settings

| Module | Responsibility |
|--------|---------------|
| `schema.py` | Pydantic BaseModel sub-configs + ChartingConfig (BaseSettings) + _DictSource |
| `loader.py` | ConfigLoader singleton; TOML loading + deep merge; 3-tier path resolution |
| `discovery.py` | find_project_root (LRUCache) + find_config_files + get_user_config_dir |

### Styling

| Module | Responsibility |
|--------|---------------|
| `theme.py` | ChartingTheme; configures matplotlib with colors/fonts from settings |
| `formatters.py` | Y-axis formatters (BRL, USD, %, human, points) using Babel |
| `fonts.py` | Loads custom fonts from assets_path |

### Charts and Overlays

| Module | Responsibility |
|--------|---------------|
| `charts/renderer.py` | ChartRenderer: generic rendering via `ax.{kind}()` + enhancer dispatch + line obstacle registration |
| `charts/_helpers.py` | Shared utilities (detect_bar_width, is_categorical_index, prepare_categorical_axis, apply_y_origin, validate_y_origin) |
| `charts/enhancers/*.py` | 13 enhancers: bar, barh, stacked_bar, area, hist, pie, stackplot, stem, stairs, boxplot, violinplot, ecdf, eventplot |
| `composing/layer.py` | Layer (frozen dataclass) + AxisSide + create_layer() with eager validation |
| `composing/compose.py` | compose() orchestrator; dual-axis, cross-axis collisions, _ComposePlotter |
| `overlays/*` | Adds secondary elements (MA, ATH/ATL/AVG, bands, markers, std_band, vband) |
| `decorations/footer.py` | Adds footer with branding and source |
| `decorations/title.py` | Adds styled title on axes |

### Metrics

| Module | Responsibility |
|--------|---------------|
| `registry.py` | MetricRegistry for registering and applying metrics |
| `builtin.py` | Registers standard metrics as overlay wrappers (ath, atl, avg, ma, hline, band, target, std_band, vband) |

### Transforms

| Module | Responsibility |
|--------|---------------|
| `temporal.py` | Pure transformation functions (variation, accum, drawdown, zscore, etc.) |
| `accessor.py` | TransformAccessor for transform chaining |

---

## Configuration Precedence Order

Configuration is loaded from multiple sources with merge:

1. `configure()` init_settings - Programmatic overrides (highest priority)
2. Env vars (`CHARTKIT_*`, nested `__`)
3. TOML files (`.charting.toml` > `pyproject.toml [tool.charting]` > user config)
4. Field defaults from pydantic models (lowest priority)

---

## Code Conventions

### Accessing Configuration

Always use `get_config()` inside functions, never cache globally:

```python
# CORRECT
def my_function():
    config = get_config()
    color = config.colors.primary

# INCORRECT (doesn't reflect changes via configure())
config = get_config()  # Global
def my_function():
    color = config.colors.primary
```

### zorder (Rendering Layers)

| Layer | zorder | Elements |
|-------|--------|----------|
| Background | 0 | Shaded bands |
| Reference | 1 | ATH, ATL, hlines |
| Secondary | 2 | Moving average |
| Data | 3+ | Lines, bars |

### Function Returns

- `plot_*()`: No return (modifies ax in-place)
- `add_*()`: No return (modifies ax/fig in-place)
- `ChartingPlotter.plot()`: Returns `PlotResult`
- Transforms: Return `TransformAccessor` (chainable)

---

## Internal Dependency Graph (Settings)

```
__init__.py
    <- loader.py
        <- discovery.py
        <- schema.py
    <- schema.py
```

**Important:** Avoid circular imports. `loader.py` is the central hub.
New modules should import from `schema.py`, never from `loader.py`.
