# Testing

Test suite for chartkit with 357 tests covering all modules with business logic.

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
├── charts/                        # Chart rendering (67 tests)
│   ├── test_area_enhancer.py      # Area chart enhancer (fill_between semantics)
│   ├── test_bar_enhancer.py       # Bar chart enhancer (grouped, sort, color='cycle', barh)
│   ├── test_bar_width.py          # detect_bar_width, categorical helpers, y_origin
│   ├── test_renderer.py          # ChartRenderer generic rendering + unsupported kinds
│   └── test_stacked_bar_enhancer.py # Stacked bar chart enhancer
├── collision/                     # Collision engine (9 tests)
│   └── test_collision_engine.py   # Obstacle collection, path detection, resolution
├── composing/                     # Composition system (29 tests)
│   ├── test_compose_pipeline.py   # compose() orchestration, legend, extract_data, formatters
│   └── test_layer_validation.py   # Layer creation and validation
├── formatting/                    # Formatters and highlight (41 tests)
│   ├── test_axis_formatters.py    # Currency, percent, human, points, multiplier formatters
│   └── test_highlight.py         # Highlight mode normalization
├── integration/                   # End-to-end tests (18 tests)
│   ├── test_accessor_pipeline.py  # Accessor .plot() and .layer() integration
│   └── test_end_to_end.py        # Full pipeline validation
├── metrics/                       # Metric registry (28 tests)
│   ├── conftest.py                # Registry snapshot/restore
│   ├── test_spec_parsing.py       # MetricRegistry.parse() spec parsing
│   └── test_registry.py          # Registration, lifecycle, available(), apply()
├── settings/                      # Configuration system (23 tests)
│   ├── conftest.py                # Config isolation (autouse reset)
│   ├── test_config_precedence.py  # Config loading, deep merge, schema, env vars
│   └── test_discovery.py         # find_project_root, find_config_files
└── transforms/                    # Time series transforms (142 tests)
    ├── conftest.py                # Known-value fixtures (pre-calculated results)
    ├── test_accum.py              # Accumulated returns
    ├── test_annualize.py          # Annualization
    ├── test_diff.py               # First difference
    ├── test_drawdown.py           # Drawdown from peak
    ├── test_freq_resolution.py    # Frequency resolution and period detection
    ├── test_input_pipeline.py     # Input coercion, sanitization, numeric validation
    ├── test_normalize.py          # Base-100 normalization
    ├── test_to_month_end.py       # Date alignment
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

### Financial Edge Cases

| Fixture | Description |
|---------|-------------|
| `irregular_daily_prices` | Irregular dates where `infer_freq` fails |
| `quarterly_rates` | Quarterly data (QE freq, 8 periods) |
| `gapped_prices` | Monthly prices with NaN gaps (real-world scenario) |

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
    ...
```

Also provides `tmp_project` -- a temporary directory with a `pyproject.toml` marker for discovery tests.

### metrics/conftest.py

```python
@pytest.fixture(autouse=True)
def _preserve_registry():
    """Snapshots and restores MetricRegistry._metrics around each test."""
    ...
```

---

## Testing Patterns

### Class-Based Organization

Tests are grouped by business domain within each file, focusing on behavior and correctness:

```python
class TestVariationKnownValues:
    """Known-value tests with pre-calculated expected results."""
    def test_month_over_month_known(self, known_variation_data): ...
    def test_year_over_year_monthly_data(self, monthly_rates): ...

class TestVariationMultiColumn:
    """Multi-column and mixed dtype handling."""
    def test_multi_column_preserves_shape(self, monthly_rates): ...
    def test_mixed_dtypes_drops_non_numeric(self, multi_series_monthly): ...

class TestVariationEdgeCases:
    """Boundary conditions, financial edge cases, NaN handling."""
    def test_quarterly_data_month_horizon(self, quarterly_rates): ...
    def test_irregular_timeseries(self, irregular_daily_prices): ...

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
| A new chart enhancer | `tests/charts/test_<kind>_enhancer.py` |
| ChartRenderer generic behavior | `tests/charts/test_renderer.py` |
| Bar width / detection helpers | `tests/charts/test_bar_width.py` |
| A new transform function | `tests/transforms/test_<name>.py` |
| Input coercion / sanitization | `tests/transforms/test_input_pipeline.py` |
| Frequency resolution | `tests/transforms/test_freq_resolution.py` |
| MetricRegistry behavior | `tests/metrics/test_registry.py` or `test_spec_parsing.py` |
| A new formatter | `tests/formatting/test_axis_formatters.py` |
| Highlight normalization | `tests/formatting/test_highlight.py` |
| Config loading / schema / merge | `tests/settings/test_config_precedence.py` |
| Project root / config discovery | `tests/settings/test_discovery.py` |
| Collision engine | `tests/collision/test_collision_engine.py` |
| Composition pipeline | `tests/composing/test_compose_pipeline.py` |
| Layer creation / validation | `tests/composing/test_layer_validation.py` |
| Accessor / end-to-end flow | `tests/integration/` |

### Checklist for New Test Files

1. Use shared fixtures from root `conftest.py` for data
2. Create known-value fixtures in module `conftest.py` if needed
3. Group tests by category using classes
4. Type-hint all test functions (return `-> None`)
5. Use `pytest.approx()` for float comparisons
6. Use `pytest.raises(ExceptionType, match="pattern")` for error tests
7. Mark slow tests with `@pytest.mark.slow`
