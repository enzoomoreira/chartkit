# Configuracao

Guia completo do sistema de configuracao TOML e paths do chartkit.

## Ordem de Precedencia

O chartkit carrega configuracoes de multiplas fontes, mesclando-as em ordem de precedencia (maior para menor):

| Prioridade | Fonte | Descricao |
|------------|-------|-----------|
| 1 | `configure()` | Configuracao programatica em runtime |
| 2 | `configure(config_path=...)` | Arquivo TOML explicito |
| 3 | `.charting.toml` / `charting.toml` | Arquivo na raiz do projeto |
| 4 | `pyproject.toml [tool.charting]` | Secao no pyproject.toml |
| 5 | `~/.config/charting/config.toml` | Config global do usuario (Linux/Mac) |
| 6 | `%APPDATA%/charting/config.toml` | Config global do usuario (Windows) |
| 7 | Defaults built-in | Valores neutros da biblioteca |

Configuracoes de maior prioridade sobrescrevem as de menor prioridade. O merge e profundo, permitindo sobrescrever apenas campos especificos sem perder o restante.

## Arquivo TOML

Crie um arquivo `.charting.toml` ou `charting.toml` na raiz do seu projeto:

```toml
# .charting.toml

[branding]
company_name = "Minha Empresa"
footer_format = "Fonte: {source}, {company_name}"
footer_format_no_source = "{company_name}"

[colors]
primary = "#003366"
secondary = "#0066CC"
tertiary = "#3399FF"
quaternary = "#66CCFF"
quinary = "#99DDFF"
senary = "#CCEEFF"
text = "#003366"
grid = "lightgray"
background = "white"
positive = "#008800"
negative = "#CC0000"
moving_average = "#888888"

[fonts]
file = "fonts/MeuFont.ttf"  # Relativo a assets_path ou absoluto
fallback = "sans-serif"
assets_path = ""  # Vazio = auto-discovery

[fonts.sizes]
default = 11
title = 18
footer = 9
axis_label = 11

[layout]
figsize = [12.0, 8.0]
dpi = 150

[layout.footer]
x = 0.01
y = 0.01
color = "gray"

[layout.title]
padding = 20
weight = "bold"

[lines]
main_width = 2.0
overlay_width = 1.5
reference_style = "--"

[bars]
width_default = 0.8
width_monthly = 20
width_annual = 300

[formatters.currency]
BRL = "R$ "
USD = "$ "

[formatters.locale]
decimal = ","
thousands = "."
babel_locale = "pt_BR"

[labels]
ath = "ATH"
atl = "ATL"
moving_average_format = "MM{window}"

[paths]
charts_subdir = "charts"
outputs_dir = ""    # Vazio = auto-discovery
assets_dir = ""     # Vazio = auto-discovery
```

O chartkit detecta automaticamente o arquivo `.charting.toml` ou `charting.toml` na raiz do projeto ao importar a biblioteca.

## Via pyproject.toml

Voce pode integrar a configuracao diretamente no `pyproject.toml` do seu projeto usando a secao `[tool.charting]`:

```toml
# pyproject.toml

[tool.charting]

[tool.charting.branding]
company_name = "Minha Empresa"
footer_format = "Elaborado por {company_name} | Dados: {source}"

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

Esta opcao e ideal para manter toda a configuracao do projeto centralizada em um unico arquivo.

## Configuracao Programatica

Use a funcao `configure()` para definir configuracoes em tempo de execucao:

```python
from chartkit import configure

# Customiza branding
configure(branding={'company_name': 'Minha Empresa'})

# Customiza cores
configure(colors={'primary': '#FF0000', 'secondary': '#00FF00'})

# Customiza layout
configure(layout={'figsize': [12.0, 8.0], 'dpi': 150})

# Combina multiplas secoes em uma chamada
configure(
    branding={'company_name': 'Banco XYZ'},
    colors={'primary': '#003366'},
    layout={'figsize': [14.0, 8.0]},
)
```

Configuracoes programaticas tem a maior prioridade e sobrescrevem qualquer valor definido em arquivos TOML.

### Parametros da Funcao configure()

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `config_path` | `Path` | Caminho para arquivo TOML de configuracao |
| `outputs_path` | `Path` | Caminho explicito para diretorio de outputs |
| `assets_path` | `Path` | Caminho explicito para diretorio de assets |
| `**overrides` | `dict` | Overrides para secoes especificas (branding, colors, etc) |

## Arquivo de Configuracao Explicito

Para carregar um arquivo TOML especifico, use o parametro `config_path`:

```python
from pathlib import Path
from chartkit import configure

# Carrega configuracao de arquivo especifico
configure(config_path=Path('./configs/producao.toml'))

# Combina arquivo com overrides
configure(
    config_path=Path('./configs/base.toml'),
    branding={'company_name': 'Override Especifico'},
)
```

O arquivo especificado sera carregado e mesclado com os defaults. Overrides programaticos ainda tem prioridade sobre o arquivo.

## Variavel de Ambiente

O chartkit suporta a variavel de ambiente `CHARTING_OUTPUTS_PATH` para definir o diretorio de outputs:

**PowerShell:**
```powershell
$env:CHARTING_OUTPUTS_PATH = "C:/caminho/para/outputs"
```

**Bash:**
```bash
export CHARTING_OUTPUTS_PATH="/caminho/para/outputs"
```

Esta variavel e util para ambientes de CI/CD ou quando voce precisa sobrescrever o path sem modificar o codigo.

## Verificar Configuracao Atual

Use `get_config()` para inspecionar a configuracao ativa:

```python
from chartkit import get_config, CHARTS_PATH, OUTPUTS_PATH, ASSETS_PATH

# Obtem configuracao completa
config = get_config()

# Acessa campos especificos
print(f"Company: {config.branding.company_name}")
print(f"Cor primaria: {config.colors.primary}")
print(f"Figsize: {config.layout.figsize}")
print(f"DPI: {config.layout.dpi}")
print(f"Fonte title: {config.fonts.sizes.title}")

# Obtem ciclo de cores para graficos
cores = config.colors.cycle()  # Lista das 6 cores primarias

# Verifica paths resolvidos
print(f"Charts: {CHARTS_PATH}")
print(f"Outputs: {OUTPUTS_PATH}")
print(f"Assets: {ASSETS_PATH}")
```

O objeto `ChartingConfig` retornado e uma dataclass tipada com acesso estruturado a todas as configuracoes.

## Reset de Configuracao

Para voltar as configuracoes para o estado inicial (defaults + arquivos auto-descobertos):

```python
from chartkit import reset_config

# Reseta todas as configuracoes
reset_config()

# Agora get_config() retornara defaults + arquivos TOML
```

O reset limpa:
- Overrides programaticos
- Path de config explicito
- Paths de outputs/assets explicitos
- Caches internos

## Auto-Discovery de Paths

O chartkit possui um sistema inteligente de auto-discovery para detectar automaticamente onde salvar graficos e onde encontrar assets.

### Cadeia de Precedencia para Paths

1. **Configuracao explicita via API**: `configure(outputs_path=..., assets_path=...)`
2. **Configuracao no TOML**: `[paths].outputs_dir`, `[paths].assets_dir`
3. **Runtime discovery via sys.modules**: Busca em modulos ja importados
4. **Auto-discovery via AST**: Analisa arquivos `config.py` do projeto host
5. **Fallback**: `project_root/outputs` e `project_root/assets`

### Runtime Discovery (Prioridade 3)

O runtime discovery busca `OUTPUTS_PATH` e `ASSETS_PATH` em modulos que ja foram importados pelo processo Python. Isso permite que bibliotecas host exponham seus paths automaticamente ao serem importadas.

**Como funciona:**

```python
# Em sua biblioteca host (ex: adb/__init__.py)
from adb.config import OUTPUTS_PATH, ASSETS_PATH  # Expoe no namespace

# Em qualquer script
import adb          # OUTPUTS_PATH ja esta em sys.modules['adb']
import chartkit     # chartkit.OUTPUTS_PATH pega de adb automaticamente
```

Esta abordagem e mais rapida que AST discovery pois nao requer I/O - os modulos ja estao carregados em memoria.

**Modulos ignorados:**
- Stdlib do Python (os, sys, pathlib, etc.)
- Pacotes de terceiros comuns (numpy, pandas, matplotlib, etc.)
- O proprio chartkit

### Auto-Discovery via AST (Prioridade 4)

Se runtime discovery nao encontrar os paths, o sistema usa parsing AST para buscar arquivos `config.py` recursivamente no projeto.

**Busca recursiva:**
- Busca `config.py` em todo o projeto usando `rglob()`
- Ordena por profundidade (arquivos mais proximos da raiz primeiro)
- Ignora diretorios comuns: `.venv`, `node_modules`, `__pycache__`, `build`, etc.

Usando AST (Abstract Syntax Tree), extrai as variaveis `OUTPUTS_PATH` e `ASSETS_PATH` sem importar o modulo. Isso evita side effects e dependencias pesadas.

**Padroes de codigo suportados:**

```python
# Padrao 1: Path com divisao
OUTPUTS_PATH = PROJECT_ROOT / 'data' / 'outputs'
ASSETS_PATH = PROJECT_ROOT / 'assets'

# Padrao 2: Variaveis intermediarias
DATA_PATH = PROJECT_ROOT / 'data'
OUTPUTS_PATH = DATA_PATH / 'outputs'

# Padrao 3: Path direto
OUTPUTS_PATH = Path('data/outputs')

# Padrao 4: Path relativo ao arquivo
ASSETS_PATH = Path(__file__).parent / 'assets'
```

**Variaveis reconhecidas como project root:**
- `PROJECT_ROOT`
- `ROOT`
- `BASE_DIR`
- `BASE_PATH`
- `ROOT_DIR`
- `ROOT_PATH`

### Deteccao do Project Root

O chartkit detecta a raiz do projeto buscando markers comuns:

```
.git
pyproject.toml
setup.py
setup.cfg
.project-root
```

A busca sobe a arvore de diretorios a partir do diretorio atual ate encontrar um desses markers.

## Configuracao Manual de Paths

Para definir paths explicitamente, sem depender de auto-discovery:

```python
from pathlib import Path
from chartkit import configure

# Define paths customizados
configure(outputs_path=Path('./meus_outputs'))
configure(assets_path=Path('./meus_assets'))

# Ou em uma unica chamada
configure(
    outputs_path=Path('C:/dados/graficos'),
    assets_path=Path('C:/recursos/fontes'),
)
```

**Via TOML:**

```toml
[paths]
outputs_dir = "data/outputs"  # Relativo ao project root
assets_dir = "assets"

# Ou caminhos absolutos:
# outputs_dir = "C:/caminho/absoluto/outputs"
# assets_dir = "D:/recursos/assets"
```

Paths relativos sao resolvidos a partir do project root detectado.

## Verificar Paths Resolvidos

Para ver quais paths o chartkit esta usando:

```python
from chartkit import CHARTS_PATH, OUTPUTS_PATH, ASSETS_PATH

# Paths sao calculados dinamicamente
print(f"Charts: {CHARTS_PATH}")   # Onde graficos sao salvos
print(f"Outputs: {OUTPUTS_PATH}")  # Path base de outputs
print(f"Assets: {ASSETS_PATH}")    # Path base de assets

# Ou via funcoes explicitas
from chartkit import get_charts_path, get_outputs_path, get_assets_path

charts = get_charts_path()
outputs = get_outputs_path()
assets = get_assets_path()
```

**Relacao entre os paths:**
- `OUTPUTS_PATH`: Diretorio base para outputs do projeto
- `CHARTS_PATH`: Subdiretorio de outputs para graficos (`OUTPUTS_PATH / charts_subdir`)
- `ASSETS_PATH`: Diretorio para recursos como fontes e imagens

## Debug de Configuracao

Para depurar problemas de configuracao, ative o logging da biblioteca:

```python
from chartkit import configure_logging

# Ativa logging em nivel DEBUG
configure_logging(level="DEBUG")

# Agora todas as operacoes de configuracao serao logadas
from chartkit import get_config
config = get_config()
```

O log mostrara:
- Quais arquivos de configuracao foram encontrados
- Ordem de merge das configuracoes
- Qual fonte foi usada para cada path
- Falhas na descoberta de paths via AST

## Exemplos Completos

### Setup Corporativo

```toml
# .charting.toml
[branding]
company_name = "Banco XYZ"
footer_format = "Elaborado por {company_name} | Fonte: {source}"

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

### Configuracao para Apresentacoes

```python
from chartkit import configure

configure(
    layout={
        'figsize': [16.0, 9.0],  # Widescreen
        'dpi': 100,  # Menor DPI para arquivos menores
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
