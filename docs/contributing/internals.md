# Internals

Internal implementation details for advanced chartkit developers.

This document covers design decisions, performance mechanisms,
and internal patterns that don't affect the public API but are important
for contributing to the codebase.

---

## Thread-Safety

The library is thread-safe for concurrent usage. All shared caches
use locks to prevent race conditions.

### Locks Used

| Module | Lock | Protects |
|--------|------|----------|
| `loader.py` | `Lock` | `ConfigLoader._config` (double-checked locking in `configure()`, `reset()`, `get_config()`) |
| `discovery.py` | `RLock` | `_project_root_cache` (LRUCache) |

### ConfigLoader Thread-Safety

`ConfigLoader` uses `threading.Lock` with double-checked locking:

```python
class ConfigLoader:
    def __init__(self):
        self._lock = threading.Lock()
        self._config: ChartingConfig | None = None

    def get_config(self) -> ChartingConfig:
        if self._config is not None:       # Fast path (no lock)
            return self._config
        with self._lock:                   # Slow path (lock)
            if self._config is not None:   # Re-check after acquiring lock
                return self._config
            self._config = ChartingConfig(...)
        return self._config
```

`configure()` and `reset()` also acquire the lock before modifying state, ensuring
that concurrent calls to `get_config()` never observe partially-updated state.

### Usage Pattern

We use `RLock` (reentrant lock) for `discovery.py` instead of a simple `Lock` because:
- Allows the same thread to acquire the lock multiple times
- Prevents deadlocks in recursive calls (e.g., `get_config()` -> `find_project_root()`)

```python
from threading import RLock
from cachetools import LRUCache, cached

_lock = RLock()
_cache: LRUCache = LRUCache(maxsize=32)

@cached(cache=_cache, lock=_lock)
def find_project_root(start_path: Path | None = None) -> Path | None:
    ...
```

### Thread-Safe Cache Clearing

The `reset_project_root_cache()` function acquires the lock before clearing:

```python
def reset_project_root_cache() -> None:
    with _project_root_lock:
        _project_root_cache.clear()
```

This prevents race conditions where one thread clears the cache while
another inserts/reads values.

### Testing Thread-Safety

```python
import threading
from chartkit.settings import get_config

def test_concurrent_access():
    errors = []

    def worker():
        try:
            for _ in range(100):
                config = get_config()
                assert config is not None
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
```

---

## Caching System

### Cache Levels

The library uses simple caching with flag-based invalidation:

```
+---------------------------+
|  ConfigLoader._config     |  None flag (invalidates via _invalidate())
+---------------------------+
            |
            v
+---------------------------+
|  _project_root_cache      |  LRUCache (32 entries, thread-safe)
+---------------------------+
            |
            v
+---------------------------+
|  Filesystem               |  Real I/O
+---------------------------+
```

### Project Root Cache

**Type:** `LRUCache(maxsize=32)` with `RLock`

**Key:** Normalized absolute path (start_path or cwd)

**Rationale:**
- Avoids repeated filesystem traversal
- 45-85x gain on repeated calls
- 32 entries sufficient for most cases

```python
# First call: ~1-5ms (filesystem walk)
root = find_project_root()

# Subsequent calls: ~0.01ms (cache hit)
root = find_project_root()
```

### Font Cache

`load_font()` caches `FontProperties` in a module-level dict keyed by the
resolved font path and fallback family. The cache exists because
`fontManager.addfont()` does not deduplicate: reloading the same file on
every chart grows matplotlib's font list for the lifetime of the process.

Because the key is the resolved path, a font change via `configure()` takes
effect on the next plot without explicit invalidation. `clear_font_cache()`
forces a reload when the file itself changed on disk.

### Config Cache

**Type:** Simple flag (`_config: ChartingConfig | None`)

The `ConfigLoader` uses `_config = None` as an invalidation flag. When
`configure()` or `reset()` are called, `_invalidate()` sets `_config = None`
and the next call to `get_config()` rebuilds the pydantic object:

```python
def _invalidate(self) -> None:
    self._config = None
    self._project_root = None
    self._project_root_resolved = False
    ChartingConfig._toml_data = {}
```

### Typical Benchmarks

| Operation | First access | Cached |
|-----------|-------------|--------|
| `find_project_root()` | 1-5ms | 0.01ms |
| `get_config()` | 5-20ms | 0.01ms |
| `get_outputs_path()` | 2-10ms | 0.01ms |

---

## Logging System

### Library: logging (standard library)

chartkit logs through `logging.getLogger(__name__)` in every module, with a
`NullHandler` attached to the `chartkit` root logger. This is the standard
library convention: nothing is emitted until the host application configures
logging, and chartkit never touches logging state it does not own.

An earlier version used `loguru`, which was dropped for two reasons: calling
`logger.disable("chartkit")` at import time mutated the global loguru logger
of whatever application imported us, and it forced an opinionated dependency
on every installation.

### Logging vs Warnings

Logging is for diagnostics. Conditions the caller should act on go through
`chartkit.warnings` instead, so they surface without any opt-in:

| Situation | Channel |
|---|---|
| Dispatch decisions, resolved parameters, cache hits | `logger.debug` |
| Work performed as requested (spikes replaced, file saved) | `logger.info` |
| Outcome differs from the request (column dropped, guessed window, ignored parameter) | `warnings.warn` |

The dividing line is whether the user asked for it. `despike()` replacing
spikes is a log record -- that is the operation. `variation()` quietly
discarding a text column is a warning.

See [Warning Categories](#warning-categories) below.

### Disabled by Default

```python
# In _logging.py (imported by __init__.py)
logging.getLogger("chartkit").addHandler(logging.NullHandler())
```

### Enabling and Disabling Logs

```python
from chartkit import configure_logging, disable_logging

# Enable DEBUG logs on stderr
configure_logging(level="DEBUG")

# Direct to file
configure_logging(level="DEBUG", sink=open("chartkit.log", "w"))

# Remove handlers added by configure_logging()
disable_logging()
```

`configure_logging()` is idempotent: it removes previously added handlers
before attaching a new one, so repeated calls never duplicate output. It
returns the `logging.Handler` it created.

Because these are ordinary stdlib loggers, the host application can also
configure them directly without calling chartkit at all:

```python
import logging
logging.getLogger("chartkit.collision").setLevel(logging.WARNING)
```

### Warning Categories

```
ChartKitWarning(UserWarning)
├── DataMutationWarning   # data altered beyond what was requested
├── InferenceWarning      # a value the caller did not supply was guessed
└── RenderingWarning      # rendered, but not as asked
```

All four are exported from the package root, so they can be filtered,
silenced or escalated with the standard machinery:

```python
import warnings
import chartkit

warnings.simplefilter("error", chartkit.DataMutationWarning)
```

`chartkit.warnings.warn()` walks out of the package before emitting, so the
warning is attributed to the user's call site rather than to a file inside
chartkit.

### %-style Formatting

Log arguments are passed separately rather than pre-formatted, so the string
is only built when a handler is actually going to emit it:

```python
# CORRECT: deferred formatting
logger.debug("find_project_root: found %s", current)

# INCORRECT: always formats, even when DEBUG is disabled
logger.debug(f"find_project_root: found {current}")
```

Warnings are the opposite: `warnings.warn` takes a single string, so those
messages are formatted eagerly with f-strings.

### Log Levels by Module

| Module | DEBUG | WARNING |
|--------|-------|---------|
| `engine.py` | Plot params, chart dispatch, highlight modes | - |
| `extraction.py` | x/y columns selected, row count | - |
| `pipeline.py` | Figure creation (figsize, grid), legend application/skip, finalize steps applied | - |
| `plot_validation.py` | Axis limit coercion (string -> float/datetime) | - |
| `tick_formatting.py` | Locator type and freq, data-aligned tick count, date format applied | - |
| `collision/` | Collision iteration counts, label movements | - |
| `frequency.py` | Inferred frequency (raw and normalized) | - |
| `temporal.py` | Transform resolution (freq, periods) | - |
| `_validation.py` | Auto-detected frequency, non-numeric columns filtered | - |
| `discovery.py` | Cache hits/misses, paths found | - |
| `loader.py` | Config files merged, overrides applied | TOML parsing errors |
| `fonts.py` | - | Font not found |
| `bar.py` / `stacked_bar.py` | - | Empty series, NaN values, data length mismatches |

### Conservative Logging

Excessive logs inside loops were removed to reduce noise:

```python
# BEFORE (excessive)
def dict_to_dataclass(cls, data):
    for field in fields(cls):
        logger.debug("Converting field {}", field.name)  # N logs per call
        ...

# AFTER (conservative)
def dict_to_dataclass(cls, data):
    logger.debug("Converting {} fields", len(fields(cls)))  # 1 log per call
    ...
```

---

## Path Resolution

The `ConfigLoader` resolves paths using an inline 3-tier chain:

1. **Explicit configuration** via `configure(outputs_path=...)`
2. **Config (TOML/env)** (`[paths].outputs_dir` or `CHARTKIT_PATHS__OUTPUTS_DIR`)
3. **Fallback** (`project_root / subdir`)

```python
# In loader.py
@property
def outputs_path(self) -> Path:
    if self._outputs_path is not None:
        return self._outputs_path                    # 1. Explicit
    config = self.get_config()
    if config.paths.outputs_dir:
        return self._resolve_relative(Path(config.paths.outputs_dir))  # 2. Config
    return (find_project_root() or Path.cwd()) / "outputs"  # 3. Fallback
```

Relative paths are resolved against the project root via `_resolve_relative()`.

---

## Babel Formatters

chartkit uses the Babel library for internationalization of
currency and numeric formatters.

### Why Babel?

- Support for any ISO 4217 code (BRL, USD, EUR, GBP, JPY, etc.)
- Correct formatting by locale (separators, symbol position)
- Native compact notation (1k, 1mi, 1bi)

### Available Formatters

| Formatter | Usage | Example |
|-----------|-------|---------|
| `currency_formatter('BRL')` | Monetary values | R$ 1.234,56 |
| `currency_formatter('USD')` | Dollars | US$ 1,234.56 |
| `compact_currency_formatter('BRL')` | Large values | R$ 1,2 mi |
| `percent_formatter()` | Percentages | 10,5% |
| `human_readable_formatter()` | K/M/B notation | 1,5M |
| `points_formatter()` | Numbers with thousands | 1.234.567 |

### Locale Configuration

Locale is configured via settings:

```toml
# .chartkit/config.toml
[formatters.locale]
babel_locale = "pt_BR"
decimal = ","
thousands = "."
```

```python
# Programmatic access
config = get_config()
locale = config.formatters.locale.babel_locale  # "pt_BR"
```

### currency_formatter Implementation

```python
from babel.numbers import format_currency as babel_format_currency
from matplotlib.ticker import FuncFormatter
from ..settings import get_config

def currency_formatter(currency: str = "BRL"):
    """
    Formatter for monetary values using Babel.

    Args:
        currency: ISO 4217 currency code.

    Returns:
        FuncFormatter for use with matplotlib.
    """
    config = get_config()
    locale = config.formatters.locale.babel_locale

    def _format(x: float, pos: int | None) -> str:
        if not math.isfinite(x):
            return ""
        return babel_format_currency(
            x,
            currency,
            locale=locale,
            currency_digits=True,
            group_separator=True,
        )

    return FuncFormatter(_format)
```

### Compact Formatters

For large values (millions, billions), use compact formatters:

```python
from chartkit.styling import compact_currency_formatter

# R$ 1,2 mi (for 1,234,567)
ax.yaxis.set_major_formatter(compact_currency_formatter('BRL'))
```

---

## Design Decisions

### Why cachetools instead of functools.lru_cache?

| Aspect | functools.lru_cache | cachetools |
|--------|---------------------|------------|
| Thread-safety | Not built-in | Lock parameter |
| TTL | Not supported | TTLCache |
| Cache control | Limited | clear(), maxsize, etc |
| Typed keys | No | Yes |

For a library that can be used in multi-threaded contexts
(Jupyter notebooks, web servers), cachetools offers stronger guarantees.

### Why RLock instead of Lock?

`RLock` allows reentrancy - the same thread can acquire the lock
multiple times. Necessary because:

```python
def get_config():
    # May call find_project_root() internally
    # which also uses lock pattern
    ...
```

With a simple `Lock`, this would cause a deadlock.

### Why not the classic singleton pattern?

Instead of:

```python
class ConfigLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

We use a module-level instance:

```python
_loader = ConfigLoader()

def get_config():
    return _loader.get_config()
```

Reasons:
- Simpler and more explicit
- Easier to test (can create isolated instances)
- Avoids inheritance issues

### Why logging stdlib instead of loguru?

A library should not decide how the application logs. loguru required
`logger.disable("chartkit")` at import time, which mutates a global logger
belonging to the host application, and it added a mandatory dependency to
every install. The stdlib pattern -- a per-module `getLogger(__name__)` plus
a `NullHandler` on the package root -- is silent by default without touching
anything the library does not own.

### Why figures are built outside pyplot

`plt.subplots()` registers the figure in pyplot's global manager, which holds
a reference for the lifetime of the process. For an interactive session that
is convenient; for a library generating charts in a loop it is a leak, and it
eventually triggers matplotlib's "more than 20 figures" warning.

`create_figure()` therefore builds `Figure()` directly and attaches a
`FigureCanvasAgg`. Two consequences follow:

- A chart is released as soon as the caller drops its `PlotResult`.
- Owning the canvas means `get_renderer()` always exists, so collision
  resolution and tick rotation work under the pdf, svg and ps backends. See
  `_internal/rendering.py` for the fallback used when a figure arrives on a
  canvas we did not create, which happens after `PlotResult.show()`.

`PlotResult.show()` is the one place pyplot is involved: it borrows a manager
from a throwaway figure so the chart can be displayed. After `show()`, pyplot
holds a reference, so `close()` matters there.

### Why the theme is a context manager

matplotlib reads `rcParams` as each artist is created, not when the figure is
saved. Scoping the theme therefore requires wrapping the entire chart --
figure, render, overlays and decorations -- which is what `theme.context()`
does. The previous `theme.apply()` wrote 24 keys straight into
`plt.rcParams`, so a single chart changed the appearance of every other plot
in the host process.

---

## Import Side Effects

Importing `chartkit` performs three registrations. They are intentional, but
worth knowing about:

| Effect | Where | Why |
|---|---|---|
| Registers the `.chartkit` accessor on `DataFrame` and `Series` | `accessor.py` | This is how pandas extensions work; there is no lazy alternative |
| Registers the 13 chart enhancers | `charts/enhancers/__init__.py` | Populates `ChartRenderer._enhancers` |
| Attaches a `NullHandler` to the `chartkit` logger | `_logging.py` | Silences "no handlers" without configuring anything |

Importing does **not** read configuration files, touch `rcParams`, or create
figures. Config discovery happens on the first `get_config()` call, which is
triggered by the first plot.

---

## Clearing Caches in Tests

Tests that touch config or discovery must isolate state. The test suite uses
autouse fixtures in module-specific `conftest.py` files:

```python
# tests/settings/conftest.py
@pytest.fixture(autouse=True)
def _isolate_config():
    reset_config()
    yield
    reset_config()
```

This runs `reset_config()` before AND after each test, ensuring no test
leaks config state to another.

### When to Clear Caches

- **Tests**: Handled automatically via autouse fixtures (see [Testing](testing.md))
- **Hot reload**: Call `reset_config()` if TOML files change at runtime
- **cwd change**: Call `reset_project_root_cache()`

---

## Performance

### Applied Optimizations

1. **Lazy init**: Nothing is loaded until first use
2. **LRUCache**: `find_project_root()` cached with 32 entries
3. **Simple flag**: `_config = None` avoids unnecessary pydantic object reconstruction
4. **Lazy project_root**: Property in ConfigLoader with `_project_root_resolved` flag
5. **Path-based collision**: `_PathObstacle` creates 1 object per Artist with display-space paths extracted from lines, patches, and collections, using Cython-based `Path.intersects_bbox()` for O(segments) intersection checks

### Tips for Contributors

- Use `get_config()` inside functions, not at module level
- Avoid loops with I/O inside frequently-called functions
- Prefer lazy evaluation for optional values
- Document complexity (O(n)) when relevant
