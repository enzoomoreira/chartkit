# Testing

Test suite for chartkit with 371 tests covering all modules with business logic.

---

## Running Tests

```bash
uv run pytest
uv run pytest tests/transforms/          # Single module
uv run pytest tests/transforms/test_variation.py  # Single file
uv run pytest -k "test_month_over_month"  # By name pattern
uv run pytest -m slow                     # Only slow-marked tests
```

---

## Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures (financial DataFrames, edge cases, Agg backend)
├── test_formatters.py             # Currency, percent, human, points formatters (15 tests)
├── test_accessor_layer.py         # Accessor .layer() integration (9 tests)
├── charts/                        # Chart rendering (31 tests)
│   ├── test_bar.py                # Bar chart (grouped, sort, color='cycle', categorical)
│   └── test_helpers.py            # detect_bar_width, categorical helpers, y_origin
├── collision/                     # Collision engine (5 tests)
│   ├── test_collect_obstacles.py  # Obstacle collection and path-based detection
│   └── test_pos_to_numeric.py     # Position type coercion
├── composing/                     # Composition system (47 tests)
│   ├── test_compose.py            # compose() orchestration
│   ├── test_composed_legend.py    # Consolidated legend from dual axes
│   ├── test_extract_data.py       # extract_plot_data() for composed layers
│   ├── test_layer.py              # Layer creation and validation
│   ├── test_validate.py           # Compose-level validation
│   └── test_axis_formatter.py     # Axis formatter application
├── decorations/                   # Decorations (4 tests)
│   └── test_title.py              # add_title() decoration
├── engine/                        # Chart engine (13 tests)
│   ├── test_normalize_highlight.py  # Highlight modes (bool, string, list)
│   └── test_validate_params.py      # PlotParamsModel pydantic validation
├── internal/                      # _internal module (8 tests)
│   ├── test_formatting.py         # FORMATTERS dispatch table
│   └── test_saving.py             # save_figure() path resolution
├── metrics/                       # Metric registry (30 tests)
│   ├── conftest.py                # Registry snapshot/restore
│   ├── test_parse.py              # MetricRegistry.parse() spec parsing
│   └── test_registry.py           # Registration, lifecycle, available()
├── settings/                      # Configuration system (39 tests)
│   ├── conftest.py                # Config isolation (autouse reset)
│   ├── test_deep_merge.py         # _deep_merge dict utility
│   ├── test_discovery.py          # find_project_root, find_config_files
│   ├── test_loader.py             # ConfigLoader (cache, reset, TOML, paths)
│   └── test_schema.py             # ChartingConfig defaults, env vars
└── transforms/                    # Time series transforms (170 tests)
    ├── conftest.py                # Known-value fixtures (pre-calculated results)
    ├── test_accessor.py           # TransformAccessor delegation
    ├── test_accum.py              # Accumulated returns
    ├── test_annualize.py          # Annualization
    ├── test_coerce_input.py       # Input coercion (dict, list, ndarray)
    ├── test_diff.py               # First difference
    ├── test_drawdown.py           # Drawdown from peak
    ├── test_normalize.py          # Base-100 normalization
    ├── test_resolve_periods.py    # Frequency resolution
    ├── test_sanitize_result.py    # inf/NaN sanitization
    ├── test_to_month_end.py       # Date alignment
    ├── test_validate_numeric.py   # Numeric column validation
    ├── test_validate_params.py    # Pydantic parameter models
    ├── test_variation.py          # Month/year variation
    └── test_zscore.py             # Z-score (global and rolling)
```

---

## Shared Fixtures

The root `conftest.py` provides reproducible financial data using a fixed seed (`rng = np.random.default_rng(42)`).

### DatetimeIndex Helpers

| Fixture | Description |
|---------|-------------|
| `daily_index` | 252 business days (1 year) from 2023-01-02 |
| `monthly_index` | 24 months from 2023-01-31 (ME freq) |

### Financial DataFrames

| Fixture | Columns | Index | Description |
|---------|---------|-------|-------------|
| `daily_prices` | `price` | daily | Geometric random walk from 100 |
| `monthly_rates` | `cdi`, `ipca` | monthly | Normal-distributed rates |
| `multi_series_monthly` | `fund_a`, `fund_b`, `fund_c`, `category` | monthly | 3 numeric + 1 string column |
| `single_series` | (Series) | monthly | Single numeric series named "rate" |

### Edge Cases

| Fixture | Description |
|---------|-------------|
| `empty_df` | Empty DataFrame |
| `empty_series` | Empty Series (float dtype) |
| `all_nan_series` | Series filled with NaN |
| `constant_series` | All values = 5.0 (std = 0) |
| `non_datetime_index_df` | DataFrame with integer index |

---

## Module-Specific Fixtures

### transforms/conftest.py

Known-value fixtures with pre-calculated expected results for exact validation:

```python
@pytest.fixture
def known_variation_data() -> pd.DataFrame:
    """[100, 110, 99, 108] -- expected MoM: [NaN, 10.0, -10.0, 9.09...]"""
    ...

@pytest.fixture
def known_accum_data() -> pd.DataFrame:
    """[1%, 2%, 3%] -- expected accum(window=3): 1.01 * 1.02 * 1.03 - 1"""
    ...
```

Other known-value fixtures: `known_normalize_data`, `known_drawdown_data`, `known_zscore_data`.

### settings/conftest.py

```python
@pytest.fixture(autouse=True)
def _isolate_config():
    """Resets config state before AND after each test."""
    reset_config()
    yield
    reset_config()
```

Also provides `tmp_project` -- a temporary directory with a `pyproject.toml` marker for discovery tests.

### metrics/conftest.py

```python
@pytest.fixture(autouse=True)
def _preserve_registry():
    """Snapshots and restores MetricRegistry._metrics around each test."""
    snapshot = dict(MetricRegistry._metrics)
    yield
    MetricRegistry._metrics.clear()
    MetricRegistry._metrics.update(snapshot)
```

---

## Testing Patterns

### Class-Based Organization

Tests are grouped by semantic category within each file:

```python
class TestVariationCorrectness:
    """Known-value tests with pre-calculated expected results."""
    def test_month_over_month_known(self, known_variation_data): ...
    def test_year_over_year_known(self, monthly_rates): ...

class TestVariationInputTypes:
    """Verify all accepted input types produce valid output."""
    def test_accepts_series(self, single_series): ...
    def test_accepts_dataframe(self, monthly_rates): ...

class TestVariationEdgeCases:
    """Boundary conditions, empty data, NaN handling."""
    def test_empty_returns_empty(self, empty_df): ...
    def test_all_nan_returns_nan(self, all_nan_series): ...

class TestVariationErrors:
    """Invalid inputs raise appropriate exceptions."""
    def test_invalid_horizon_raises(self, monthly_rates): ...
```

### Known-Value Testing

Transform tests use pre-calculated expected values instead of relying on library internals:

```python
def test_month_over_month_known(self, known_variation_data: pd.DataFrame) -> None:
    result = variation(known_variation_data, horizon="month")
    vals = result["price"].to_list()
    assert vals[1] == pytest.approx(10.0)   # (110 - 100) / 100 * 100
    assert vals[2] == pytest.approx(-10.0)  # (99 - 110) / 110 * 100
```

### Float Comparison

Always use `pytest.approx()` for floating-point equality:

```python
assert result.iloc[0] == pytest.approx(1.0, abs=1e-10)
```

### Exception Testing

Use `pytest.raises` with `match` to verify both exception type and message:

```python
def test_invalid_horizon_raises(self, monthly_rates: pd.DataFrame) -> None:
    with pytest.raises(TransformError, match="Invalid horizon"):
        variation(monthly_rates, horizon="week")
```

### Pydantic Validation Testing

For internal pydantic models, test that invalid inputs are rejected:

```python
from pydantic import ValidationError as PydanticValidationError

def test_invalid_units_raises(self) -> None:
    with pytest.raises(PydanticValidationError):
        PlotParamsModel(units="EUR")
```

---

## Pytest Configuration

Defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = ["-ra", "--strict-markers", "--strict-config", "--tb=short", "-q"]
markers = ["slow: marks slower tests (e.g. config loading with real files)"]
filterwarnings = ["error", "ignore::UserWarning:matplotlib"]
```

| Option | Purpose |
|--------|---------|
| `testpaths = ["tests"]` | Only discover tests in `tests/` |
| `pythonpath = ["src"]` | Add `src/` to Python path for `import chartkit` |
| `--strict-markers` | Fail on undefined markers |
| `--strict-config` | Fail on invalid pytest config |
| `--tb=short` | Short tracebacks |
| `-q` | Quiet output |
| `filterwarnings: error` | Treat all warnings as errors |
| `ignore::UserWarning:matplotlib` | Except matplotlib UserWarnings |

---

## State Isolation

Each module that touches shared state uses autouse fixtures to guarantee test independence:

| Module | Fixture | What it resets |
|--------|---------|---------------|
| `settings/` | `_isolate_config` | `reset_config()` before and after each test |
| `metrics/` | `_preserve_registry` | Snapshots and restores `MetricRegistry._metrics` |

Transforms and collision tests don't need isolation -- they operate on fixture data without modifying global state.

---

## Writing New Tests

### Choosing Where to Put Tests

| Testing... | Location |
|-----------|----------|
| A new transform function | `tests/transforms/test_<name>.py` |
| MetricRegistry behavior | `tests/metrics/test_registry.py` or `test_parse.py` |
| A new formatter | `tests/test_formatters.py` |
| Config loading / schema | `tests/settings/test_loader.py` or `test_schema.py` |
| Collision engine | `tests/collision/test_<function>.py` |
| Engine internals | `tests/engine/test_<function>.py` |

### Checklist for New Test Files

1. Use shared fixtures from root `conftest.py` for data
2. Create known-value fixtures in module `conftest.py` if needed
3. Group tests by category using classes
4. Type-hint all test functions (return `-> None`)
5. Use `pytest.approx()` for float comparisons
6. Use `pytest.raises(ExceptionType, match="pattern")` for error tests
7. Mark slow tests with `@pytest.mark.slow`
