# Configuration

Complete guide to the TOML configuration system and paths in chartkit.

## Precedence Order

chartkit loads configuration from multiple sources, merging them in order of precedence (highest to lowest):

| Priority | Source | Description |
|----------|--------|-------------|
| 1 | `configure()` (init_settings) | Programmatic runtime configuration |
| 2 | Environment variables (`CHARTKIT_*`) | Env vars with prefix and nested delimiter `__` |
| 3 | `configure(config_path=...)` | Explicit TOML file |
| 4 | `.charting.toml` / `charting.toml` | File at project root |
| 5 | `pyproject.toml [tool.charting]` | Section in pyproject.toml |
| 6 | `~/.config/charting/config.toml` | User global config (Linux/Mac) |
| 7 | `%APPDATA%/charting/config.toml` | User global config (Windows) |
| 8 | Built-in defaults | Default values from pydantic models |

Higher-priority configurations override lower-priority ones. The merge is deep, allowing you to override only specific fields without losing the rest.

## TOML File

Create a `.charting.toml` or `charting.toml` file at your project root:

```toml
# .charting.toml

[branding]
company_name = "My Company"
default_source = ""  # Default source when source=None in plot()
footer_format = "Fonte: {source}, {company_name}"
footer_format_no_source = "{company_name}"

[colors]
primary = "#00464D"
secondary = "#006B6B"
tertiary = "#008B8B"
quaternary = "#20B2AA"
quinary = "#5F9EA0"
senary = "#2E8B57"
text = "#00464D"
grid = "lightgray"
background = "white"
positive = "#00464D"
negative = "#8B0000"
moving_average = "#888888"

[fonts]
file = "fonts/MyFont.ttf"  # Relative to paths.assets_dir or absolute
fallback = "sans-serif"

[fonts.sizes]
default = 11
title = 18
footer = 9
axis_label = 11

[layout]
figsize = [10.0, 6.0]
dpi = 300
base_style = "seaborn-v0_8-white"  # Base matplotlib style
grid = false                        # Show grid on chart

[layout.spines]
top = false      # Top border
right = false    # Right border
left = true      # Left border
bottom = true    # Bottom border

[layout.footer]
y = 0.01
color = "gray"

[layout.title]
padding = 20
weight = "bold"

[lines]
main_width = 2.0
overlay_width = 1.5
reference_style = "--"
target_style = "-."
moving_avg_min_periods = 1

[bars]
width_default = 0.8
width_monthly = 20
width_annual = 300
auto_margin = 0.1
warning_threshold = 500

[bars.frequency_detection]
monthly_threshold = 25
annual_threshold = 300

[markers]
scatter_size = 30
font_weight = "bold"
label_offset_fraction = 0.015  # Vertical breathing room between label and data point

[formatters.locale]
decimal = ","
thousands = "."
babel_locale = "pt_BR"

[labels]
ath = "ATH"
atl = "ATL"
avg = "AVG"
moving_average_format = "MM{window}"
target_format = "Meta: {value}"
std_band_format = "BB({window}, {num_std})"

[bands]
alpha = 0.15

[collision]
movement = "y"
obstacle_padding_px = 8.0
label_padding_px = 4.0
max_iterations = 50
connector_threshold_px = 30.0
connector_alpha = 0.6
connector_style = "-"
connector_width = 1.0

[transforms]
normalize_base = 100
accum_window = 12

[legend]
loc = "best"
alpha = 0.9
frameon = true

[paths]
charts_subdir = "charts"
outputs_dir = ""    # Empty = auto-discovery
assets_dir = ""     # Empty = auto-discovery
```

chartkit automatically detects the `.charting.toml` or `charting.toml` file at the project root when importing the library.

## Via pyproject.toml

You can integrate the configuration directly into your project's `pyproject.toml` using the `[tool.charting]` section:

```toml
# pyproject.toml

[tool.charting]

[tool.charting.branding]
company_name = "My Company"
footer_format = "Prepared by {company_name} | Data: {source}"

[tool.charting.colors]
primary = "#003366"
secondary = "#0066CC"

[tool.charting.layout]
figsize = [14.0, 8.0]
dpi = 150

[tool.charting.fonts.sizes]
title = 24
default = 14

[tool.charting.paths]
outputs_dir = "data/outputs"
assets_dir = "assets"
```

This option is ideal for keeping all project configuration centralized in a single file.

## Programmatic Configuration

Use the `configure()` function to set configurations at runtime:

```python
from chartkit import configure

# Customize branding
configure(branding={'company_name': 'My Company'})

# Customize colors
configure(colors={'primary': '#FF0000', 'secondary': '#00FF00'})

# Customize layout
configure(layout={'figsize': [12.0, 8.0], 'dpi': 150})

# Combine multiple sections in one call
configure(
    branding={'company_name': 'Bank XYZ'},
    colors={'primary': '#003366'},
    layout={'figsize': [14.0, 8.0]},
)
```

Programmatic configurations have the highest priority and override any value defined in TOML files.

### configure() Function Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `config_path` | `Path` | Path to TOML configuration file |
| `outputs_path` | `Path` | Explicit path to outputs directory |
| `assets_path` | `Path` | Explicit path to assets directory |
| `**overrides` | `dict` | Overrides for specific sections (branding, colors, etc) |

## Explicit Configuration File

To load a specific TOML file, use the `config_path` parameter:

```python
from pathlib import Path
from chartkit import configure

# Load configuration from specific file
configure(config_path=Path('./configs/production.toml'))

# Combine file with overrides
configure(
    config_path=Path('./configs/base.toml'),
    branding={'company_name': 'Specific Override'},
)
```

The specified file will be loaded and merged with the defaults. Programmatic overrides still take priority over the file.

## Environment Variables

chartkit uses pydantic-settings with prefix `CHARTKIT_` and nested delimiter `__`. Any configuration field can be set via env var:

**Examples:**

```bash
# Simple fields
export CHARTKIT_LAYOUT__DPI=72
export CHARTKIT_COLORS__PRIMARY="#FF0000"

# Paths
export CHARTKIT_PATHS__OUTPUTS_DIR="/path/to/outputs"
export CHARTKIT_PATHS__ASSETS_DIR="/path/to/assets"

# Branding
export CHARTKIT_BRANDING__COMPANY_NAME="My Company"
```

**PowerShell:**
```powershell
$env:CHARTKIT_LAYOUT__DPI = "72"
$env:CHARTKIT_PATHS__OUTPUTS_DIR = "C:/path/to/outputs"
```

Env vars take priority over TOML but below `configure()`. Useful for CI/CD or environments where files cannot be modified.

## Inspecting Current Configuration

Use `get_config()` to inspect the active configuration:

```python
from chartkit import get_config, CHARTS_PATH, OUTPUTS_PATH, ASSETS_PATH

# Get full configuration
config = get_config()

# Access specific fields
print(f"Company: {config.branding.company_name}")
print(f"Primary color: {config.colors.primary}")
print(f"Figsize: {config.layout.figsize}")
print(f"DPI: {config.layout.dpi}")
print(f"Title font: {config.fonts.sizes.title}")

# Get color cycle for charts
colors = config.colors.cycle()  # List of 6 primary colors

# Check resolved paths
print(f"Charts: {CHARTS_PATH}")
print(f"Outputs: {OUTPUTS_PATH}")
print(f"Assets: {ASSETS_PATH}")
```

The returned `ChartingConfig` object is a pydantic BaseSettings with structured access to all settings.

## Configuration Reset

To restore settings to their initial state (defaults + auto-discovered files):

```python
from chartkit import reset_config

# Reset all settings
reset_config()

# Now get_config() will return defaults + TOML files
```

The reset clears:
- Programmatic overrides
- Explicit config path
- Explicit outputs/assets paths
- Internal caches

## Path Auto-Discovery

chartkit has an intelligent auto-discovery system to automatically detect where to save charts and where to find assets.

### Path Precedence Chain

1. **Explicit configuration via API**: `configure(outputs_path=..., assets_path=...)`
2. **Configuration via TOML/env**: `[paths].outputs_dir`, `[paths].assets_dir` or `CHARTKIT_PATHS__OUTPUTS_DIR`
3. **Fallback**: `project_root/outputs` and `project_root/assets`

### Project Root Detection

chartkit detects the project root by looking for common markers:

```
.git
pyproject.toml
setup.py
setup.cfg
.project-root
```

The search walks up the directory tree from the current directory until one of these markers is found.

## Manual Path Configuration

To set paths explicitly, without relying on auto-discovery:

```python
from pathlib import Path
from chartkit import configure

# Set custom paths
configure(outputs_path=Path('./my_outputs'))
configure(assets_path=Path('./my_assets'))

# Or in a single call
configure(
    outputs_path=Path('C:/data/charts'),
    assets_path=Path('C:/resources/fonts'),
)
```

**Via TOML:**

```toml
[paths]
outputs_dir = "data/outputs"  # Relative to project root
assets_dir = "assets"

# Or absolute paths:
# outputs_dir = "C:/absolute/path/outputs"
# assets_dir = "D:/resources/assets"
```

Relative paths are resolved from the detected project root.

## Checking Resolved Paths

To see which paths chartkit is using:

```python
from chartkit import CHARTS_PATH, OUTPUTS_PATH, ASSETS_PATH

# Paths are computed dynamically
print(f"Charts: {CHARTS_PATH}")   # Where charts are saved
print(f"Outputs: {OUTPUTS_PATH}")  # Base outputs path
print(f"Assets: {ASSETS_PATH}")    # Base assets path

# Or via explicit functions
from chartkit import get_charts_path, get_outputs_path, get_assets_path

charts = get_charts_path()
outputs = get_outputs_path()
assets = get_assets_path()
```

**Relationship between paths:**
- `OUTPUTS_PATH`: Base directory for project outputs
- `CHARTS_PATH`: Subdirectory of outputs for charts (`OUTPUTS_PATH / charts_subdir`)
- `ASSETS_PATH`: Directory for resources like fonts and images

## Configuration Debugging

To debug configuration issues, enable library logging:

```python
from chartkit import configure_logging

# Enable logging at DEBUG level
configure_logging(level="DEBUG")

# Now all configuration operations will be logged
from chartkit import get_config
config = get_config()
```

The log will show:
- Which configuration files were found
- Configuration merge order
- Which source was used for each path

## Full Examples

### Corporate Setup

```toml
# .charting.toml
[branding]
company_name = "Bank XYZ"
footer_format = "Prepared by {company_name} | Fonte: {source}"

[colors]
primary = "#003366"
secondary = "#0055AA"
text = "#003366"
positive = "#006600"
negative = "#990000"

[fonts]
file = "fonts/ArialNarrow.ttf"

[layout]
figsize = [14.0, 8.0]
dpi = 150
```

### Presentation Configuration

```python
from chartkit import configure

configure(
    layout={
        'figsize': [16.0, 9.0],  # Widescreen
        'dpi': 100,  # Lower DPI for smaller files
    },
    fonts={
        'sizes': {
            'title': 28,
            'default': 16,
            'footer': 14,
        }
    },
)
```

### English Localization

```toml
[formatters.locale]
decimal = "."
thousands = ","
babel_locale = "en_US"

[labels]
ath = "All-Time High"
atl = "All-Time Low"
moving_average_format = "MA{window}"
```
