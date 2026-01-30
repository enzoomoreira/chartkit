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
file = "fonts/MeuFont.ttf"  # Relativo a assets_path ou absoluto
fallback = "sans-serif"
assets_path = ""  # Vazio = auto-discovery

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

[layout.zorder]
bands = 0
reference_lines = 1
moving_average = 2
data = 3
markers = 5

# Linhas
[lines]
main_width = 2.0
overlay_width = 1.5
reference_style = "--"
moving_avg_min_periods = 1

[lines.legend]
alpha = 0.9
frameon = true

# Barras
[bars]
width_default = 0.8
width_monthly = 20
width_annual = 300
auto_margin = 0.1

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
babel_locale = "pt_BR"

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
outputs_dir = ""  # Vazio = auto-discovery de OUTPUTS_PATH
assets_dir = ""   # Vazio = auto-discovery de ASSETS_PATH
project_root_markers = [".git", "pyproject.toml", "setup.py", "setup.cfg", ".project-root"]
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
| `file` | str | "" (vazio) | Arquivo da fonte (relativo a assets_path ou absoluto) |
| `fallback` | str | "sans-serif" | Fonte de fallback |
| `assets_path` | str | "" (auto) | Caminho base para assets |

O `file` pode ser:
- Relativo ao `assets_path` (ex: `"fonts/MeuFont.ttf"`)
- Caminho absoluto (ex: `"/usr/share/fonts/custom.ttf"`)

O `assets_path` segue a ordem de precedencia:
1. Valor explicito no TOML
2. Auto-discovery via AST do projeto host (procura por `ASSETS_PATH` em config.py)
3. Fallback: `project_root/assets` (com warning)

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
| `zorder.bands` | int | 0 | Camada visual das bandas |
| `zorder.reference_lines` | int | 1 | Camada visual das linhas de referencia |
| `zorder.moving_average` | int | 2 | Camada visual da media movel |
| `zorder.data` | int | 3 | Camada visual dos dados principais |
| `zorder.markers` | int | 5 | Camada visual dos marcadores |

### Lines

Configuracao de graficos de linha.

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `main_width` | float | 2.0 | Espessura da linha principal |
| `overlay_width` | float | 1.5 | Espessura de overlays |
| `reference_style` | str | "--" | Estilo de linhas de referencia |
| `moving_avg_min_periods` | int | 1 | Minimo de periodos para media movel |
| `legend.alpha` | float | 0.9 | Transparencia da legenda |
| `legend.frameon` | bool | true | Borda da legenda |

### Bars

Configuracao de graficos de barra.

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `width_default` | float | 0.8 | Largura padrao |
| `width_monthly` | int | 20 | Largura para dados mensais |
| `width_annual` | int | 300 | Largura para dados anuais |
| `auto_margin` | float | 0.1 | Margem (%) para y_origin='auto' |
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
babel_locale = "pt_BR"

[formatters.magnitude]
suffixes = ["", "k", "M", "B", "T"]
```

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `locale.decimal` | str | "," | Separador decimal (para formatadores manuais) |
| `locale.thousands` | str | "." | Separador de milhar (para formatadores manuais) |
| `locale.babel_locale` | str | "pt_BR" | Locale para Babel (moedas ISO 4217) |
| `magnitude.suffixes` | list[str] | ["", "k", "M", "B", "T"] | Sufixos para notacao compacta |

O `babel_locale` controla a formatacao de moedas via Babel, suportando qualquer
codigo ISO 4217 (BRL, USD, EUR, GBP, JPY, etc.). Exemplos de locales:
- `pt_BR` - Portugues Brasil (R$ 1.234,56)
- `en_US` - Ingles EUA ($1,234.56)
- `de_DE` - Alemao (1.234,56 EUR)

### Labels

Rotulos padrao para overlays.

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `ath` | str | "ATH" | Label do All-Time High |
| `atl` | str | "ATL" | Label do All-Time Low |
| `moving_average_format` | str | "MM{window}" | Formato da legenda MM |

### Paths

Configuracao de caminhos e diretorios.

| Campo | Tipo | Default | Descricao |
|-------|------|---------|-----------|
| `charts_subdir` | str | "charts" | Subdiretorio para graficos dentro de outputs |
| `outputs_dir` | str | "" (auto) | Diretorio de outputs (vazio = auto-discovery) |
| `assets_dir` | str | "" (auto) | Diretorio de assets (vazio = auto-discovery) |
| `project_root_markers` | list[str] | [".git", ...] | Markers para detectar raiz do projeto |

#### Auto-Discovery de Paths

Quando `outputs_dir` ou `assets_dir` nao sao especificados, o chartkit tenta detectar
automaticamente os paths do projeto que o utiliza como dependencia.

**Estrategia de Auto-Discovery:**

1. Procura por arquivos `config.py` em locais comuns:
   - `src/*/core/config.py`
   - `src/*/config.py`
   - `*/core/config.py`
   - `*/config.py`
   - `config.py`

2. Usa AST (Abstract Syntax Tree) para extrair as variaveis `OUTPUTS_PATH` e `ASSETS_PATH`
   sem importar o modulo (evita side effects e dependencias pesadas).

3. Suporta padroes comuns:
   - `OUTPUTS_PATH = PROJECT_ROOT / 'data' / 'outputs'`
   - `ASSETS_PATH = Path('assets')`

4. Se nao encontrar, usa fallback com warning:
   - `outputs_dir`: `project_root/outputs`
   - `assets_dir`: `project_root/assets`

**Exemplo de configuracao explicita:**

```toml
[paths]
outputs_dir = "data/outputs"  # Relativo ao project root
assets_dir = "assets"         # Relativo ao project root
# ou caminhos absolutos:
# outputs_dir = "C:/caminho/absoluto/outputs"
```

## API Python

### configure()

```python
from chartkit import configure

# Arquivo explicito
configure(config_path=Path('./config.toml'))

# Paths explicitos
configure(outputs_path=Path('./data/outputs'))
configure(assets_path=Path('./assets'))

# Overrides por secao
configure(branding={'company_name': 'Empresa'})
configure(colors={'primary': '#FF0000'})
configure(layout={'figsize': [12.0, 8.0]})

# Multiplos overrides
configure(
    branding={'company_name': 'Empresa'},
    colors={'primary': '#FF0000'},
    outputs_path=Path('./outputs'),
)
```

### get_assets_path() / get_outputs_path()

```python
from chartkit.settings import get_assets_path, get_outputs_path

# Retorna Path resolvido (seguindo ordem de precedencia)
assets = get_assets_path()  # Path para assets
outputs = get_outputs_path()  # Path para outputs
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
babel_locale = "en_US"

[labels]
ath = "All-Time High"
atl = "All-Time Low"
moving_average_format = "MA{window}"
```
