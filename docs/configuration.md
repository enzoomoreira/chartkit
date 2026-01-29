# Configuration

Guia completo do sistema de configuracao TOML.

## Visao Geral

Esta biblioteca usa um sistema de configuracao flexivel que permite personalizar
todos os aspectos visuais da biblioteca. A configuracao pode vir de:

1. **Arquivos TOML** - Para configuracao persistente
2. **`pyproject.toml`** - Integrado ao projeto Python
3. **`configure()`** - Para ajustes programaticos em runtime

## Locais de Busca

A configuracao e carregada automaticamente dos seguintes locais (em ordem de precedencia):

| Prioridade | Local | Descricao |
|------------|-------|-----------|
| 1 | `configure(config_path=...)` | Caminho explicito |
| 2 | `.charting.toml` / `charting.toml` | Projeto local |
| 3 | `pyproject.toml [tool.charting]` | Secao no pyproject |
| 4 | `~/.config/charting/config.toml` | Usuario global (Linux/Mac) |
| 5 | `%APPDATA%/charting/config.toml` | Usuario global (Windows) |
| 6 | Defaults built-in | Valores neutros |

## Uso Basico

### Sem Configuracao

```python
import chartkit  # Usa defaults

df.chartkit.plot(title="Grafico")  # Usa cores e branding dos defaults
```

### Com Arquivo TOML

Crie `.charting.toml` na raiz do projeto:

```toml
[branding]
company_name = "Banco XYZ"

[colors]
primary = "#003366"
```

```python
import chartkit  # Carrega .charting.toml automaticamente

df.chartkit.plot(title="Grafico")  # Usa cores e branding do TOML
```

### Programaticamente

```python
from chartkit import configure

configure(branding={'company_name': 'Minha Empresa'})
configure(colors={'primary': '#FF0000'})
```

## Estrutura Completa do TOML

```toml
# Branding - Personalizacao de marca
[branding]
company_name = "Sua Empresa"
footer_format = "Fonte: {source}, {company_name}"
footer_format_no_source = "{company_name}"

# Cores - Paleta completa
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

# Fontes
[fonts]
file = "fonts/MeuFont.ttf"  # Relativo a assets/ ou absoluto
fallback = "sans-serif"

[fonts.sizes]
default = 11
title = 18
footer = 9
axis_label = 11

# Layout
[layout]
figsize = [10.0, 6.0]
dpi = 300

[layout.footer]
x = 0.01
y = 0.01
color = "gray"

[layout.title]
padding = 20
weight = "bold"

# Linhas
[lines]
main_width = 2.0
overlay_width = 1.5
reference_style = "--"

[lines.legend]
alpha = 0.9
frameon = true

# Barras
[bars]
width_default = 0.8
width_monthly = 20
width_annual = 300

[bars.frequency_detection]
monthly_threshold = 25
annual_threshold = 300

# Bandas
[bands]
alpha = 0.15

# Marcadores
[markers]
scatter_size = 30
label_offset_x = 5
label_offset_y = 8

# Colisao de labels
[collision]
margin_px = 5
guide_threshold_px = 30
extra_padding_px = 15
px_to_points_ratio = 0.75

# Transforms
[transforms]
mom_periods = 1
yoy_periods = 12
trading_days_per_year = 252
normalize_base = 100
rolling_window = 12

# Formatadores
[formatters.currency]
BRL = "R$ "
USD = "$ "

[formatters.locale]
decimal = ","
thousands = "."

[formatters.magnitude]
suffixes = ["", "k", "M", "B", "T"]

# Labels
[labels]
ath = "ATH"
atl = "ATL"
moving_average_format = "MM{window}"

# Paths
[paths]
charts_subdir = "charts"
default_output_dir = "outputs"
project_root_markers = [".git", "pyproject.toml", "setup.py", "setup.cfg", ".project-root"]
output_conventions = ["outputs", "data/outputs", "output", "data/output"]
```

## Secoes de Configuracao

### Branding

Controla o texto do rodape e identificacao da empresa.

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `company_name` | str | "" | Nome da empresa |
| `footer_format` | str | "Fonte: {source}, {company_name}" | Formato com fonte |
| `footer_format_no_source` | str | "{company_name}" | Formato sem fonte |

Placeholders disponiveis:
- `{source}` - Fonte dos dados (parametro `source` do plot)
- `{company_name}` - Nome da empresa configurado

### Colors

Paleta de cores para graficos.

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `primary` - `senary` | str | Gradiente verde | Cores para series |
| `text` | str | "#00464D" | Cor do texto |
| `grid` | str | "lightgray" | Cor da grade |
| `background` | str | "white" | Cor de fundo |
| `positive` | str | "#00464D" | Cor para ATH |
| `negative` | str | "#8B0000" | Cor para ATL |
| `moving_average` | str | "#888888" | Cor da media movel |

O metodo `colors.cycle()` retorna lista ordenada das 6 cores primarias.

### Fonts

Configuracao de tipografia.

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `file` | str | "" (vazio) | Arquivo da fonte (relativo a assets/ ou absoluto) |
| `fallback` | str | "sans-serif" | Fonte de fallback |

O `file` pode ser:
- Relativo a `assets/` (ex: `"fonts/MeuFont.ttf"`)
- Caminho absoluto (ex: `"/usr/share/fonts/custom.ttf"`)

### Layout

Dimensoes e posicionamento do grafico.

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `figsize` | [float, float] | [10.0, 6.0] | Largura x Altura (polegadas) |
| `dpi` | int | 300 | Resolucao para exportacao |
| `footer.x/y` | float | 0.01 | Posicao do rodape (0-1) |
| `footer.color` | str | "gray" | Cor do rodape |
| `title.padding` | int | 20 | Espacamento do titulo |
| `title.weight` | str | "bold" | Peso da fonte do titulo |

### Lines

Configuracao de graficos de linha.

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `main_width` | float | 2.0 | Espessura da linha principal |
| `overlay_width` | float | 1.5 | Espessura de overlays |
| `reference_style` | str | "--" | Estilo de linhas de referencia |
| `legend.alpha` | float | 0.9 | Transparencia da legenda |
| `legend.frameon` | bool | true | Borda da legenda |

### Bars

Configuracao de graficos de barra.

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `width_default` | float | 0.8 | Largura padrao |
| `width_monthly` | int | 20 | Largura para dados mensais |
| `width_annual` | int | 300 | Largura para dados anuais |
| `frequency_detection.monthly_threshold` | int | 25 | Dias para detectar mensal |
| `frequency_detection.annual_threshold` | int | 300 | Dias para detectar anual |

### Formatters

Configuracao de formatadores de texto.

```toml
[formatters.currency]
BRL = "R$ "
USD = "$ "

[formatters.locale]
decimal = ","
thousands = "."

[formatters.magnitude]
suffixes = ["", "k", "M", "B", "T"]
```

### Labels

Rotulos padrao para overlays.

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `ath` | str | "ATH" | Label do All-Time High |
| `atl` | str | "ATL" | Label do All-Time Low |
| `moving_average_format` | str | "MM{window}" | Formato da legenda MM |

## API Python

### configure()

```python
from chartkit import configure

# Arquivo explicito
configure(config_path=Path('./config.toml'))

# Path de outputs
configure(outputs_path=Path('./outputs'))

# Overrides por secao
configure(branding={'company_name': 'Empresa'})
configure(colors={'primary': '#FF0000'})
configure(layout={'figsize': [12.0, 8.0]})

# Multiplos overrides
configure(
    branding={'company_name': 'Empresa'},
    colors={'primary': '#FF0000'},
)
```

### get_config()

```python
from chartkit import get_config

config = get_config()
print(config.branding.company_name)
print(config.colors.primary)
print(config.layout.figsize)
```

### reset_config()

```python
from chartkit.settings import reset_config

reset_config()  # Volta para defaults
```

### ChartingConfig

Dataclass com todos os campos de configuracao:

```python
from chartkit import ChartingConfig, get_config

config: ChartingConfig = get_config()

# Acesso tipado
config.branding.company_name  # str
config.colors.cycle()         # list[str]
config.layout.figsize         # tuple[float, float]
config.fonts.sizes.title      # int
```

## Exemplos de Uso

### Personalizacao de Marca

```toml
# charting.toml
[branding]
company_name = "Banco XYZ"
footer_format = "Elaborado por {company_name} | Dados: {source}"
```

### Paleta de Cores Corporativa

```toml
[colors]
primary = "#003366"
secondary = "#0066CC"
tertiary = "#3399FF"
quaternary = "#66CCFF"
quinary = "#99DDFF"
senary = "#CCEEFF"
text = "#003366"
positive = "#008800"
negative = "#CC0000"
```

### Layout para Apresentacoes

```toml
[layout]
figsize = [14.0, 8.0]
dpi = 150

[fonts.sizes]
title = 24
default = 14
footer = 12
```

### Localizacao para Ingles

```toml
[formatters.locale]
decimal = "."
thousands = ","

[labels]
ath = "All-Time High"
atl = "All-Time Low"
moving_average_format = "MA{window}"
```
