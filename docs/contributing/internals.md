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
| `discovery.py` | `RLock` | `_project_root_cache` (LRUCache) |

### Usage Pattern

We use `RLock` (reentrant lock) instead of a simple `Lock` because:
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

### Library: loguru

We use `loguru` instead of `logging` stdlib because:
- Simpler API (`logger.debug()` vs `logging.getLogger().debug()`)
- Built-in lazy evaluation (avoids unnecessary formatting)
- Better Unicode and terminal color support

### Disabled by Default

Following best practices for Python libraries, logging is
disabled by default:

```python
# In _logging.py (imported by __init__.py)
from loguru import logger
logger.disable("chartkit")
```

### Enabling and Disabling Logs

```python
from chartkit import configure_logging, disable_logging

# Enable DEBUG logs
configure_logging(level="DEBUG")

# Enable INFO logs to stderr
configure_logging(level="INFO")

# Direct to file
configure_logging(level="DEBUG", sink=open("chartkit.log", "w"))

# Disable logging and remove handlers
disable_logging()
```

`configure_logging()` is idempotent: repeated calls remove the previous handler before adding a new one, avoiding log duplication.

### configure_logging() Implementation

```python
_handler_ids: list[int] = []

def configure_logging(level: str = "DEBUG", sink: TextIO | None = None) -> int:
    # Remove previous handlers
    for hid in _handler_ids:
        try:
            logger.remove(hid)
        except ValueError:
            pass
    _handler_ids.clear()

    logger.enable("chartkit")
    target = sink if sink is not None else sys.stderr
    handler_id = logger.add(target, level=level, filter="chartkit")
    _handler_ids.append(handler_id)
    return handler_id


def disable_logging() -> None:
    logger.disable("chartkit")
    for hid in _handler_ids:
        try:
            logger.remove(hid)
        except ValueError:
            pass
    _handler_ids.clear()
```

### Lazy Evaluation

We use `{}` placeholders instead of f-strings to avoid unnecessary
formatting when logging is disabled:

```python
# CORRECT: lazy evaluation
logger.debug("find_project_root: found {}", current)

# INCORRECT: always formats, even if DEBUG is disabled
logger.debug(f"find_project_root: found {current}")
```

### Log Levels by Module

| Module | DEBUG | WARNING |
|--------|-------|---------|
| `engine.py` | Plot params, chart dispatch, highlight modes | - |
| `collision.py` | Collision iteration counts, label movements | - |
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
# .charting.toml
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

### Why loguru instead of logging stdlib?

- Less boilerplate (one import, ready to use)
- Native lazy evaluation with `{}`
- Better default formatting
- Easy to disable (`logger.disable()`)

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

### Tips for Contributors

- Use `get_config()` inside functions, not at module level
- Avoid loops with I/O inside frequently-called functions
- Prefer lazy evaluation for optional values
- Document complexity (O(n)) when relevant
