# Architecture

Documentacao da arquitetura interna para contribuidores.

## Estrutura de Modulos

```
src/agora_charting/
├── __init__.py           # Entry point, exports publicos
├── accessor.py           # Pandas DataFrame accessor (.agora)
├── engine.py             # AgoraPlotter - orquestrador principal
├── transforms.py         # Funcoes de transformacao temporal
├── settings/             # Sistema de configuracao TOML
│   ├── __init__.py       # Exports: configure, get_config, ChartingConfig
│   ├── schema.py         # Dataclasses tipadas para configuracao
│   ├── defaults.py       # Valores default (Agora Investimentos)
│   └── loader.py         # Carregamento TOML e merge
├── assets/
│   └── fonts/
│       └── BradescoSans-Light.ttf
├── styling/
│   ├── __init__.py       # Facade
│   ├── theme.py          # ChartingTheme (usa settings)
│   ├── formatters.py     # Formatadores de eixo Y (usa settings)
│   └── fonts.py          # Carregamento de fontes (usa settings)
├── plots/
│   ├── __init__.py       # Facade
│   ├── line.py           # Grafico de linhas
│   └── bar.py            # Grafico de barras
├── components/
│   ├── __init__.py       # Facade
│   ├── footer.py         # Rodape (usa settings.branding)
│   ├── markers.py        # Highlight de pontos/barras
│   └── collision.py      # Resolucao de colisoes
└── overlays/
    ├── __init__.py       # Facade
    ├── moving_average.py # Media movel
    ├── reference_lines.py # ATH, ATL, hlines
    └── bands.py          # Bandas sombreadas
```

---

## Sistema de Configuracao

### Visao Geral

O sistema de configuracao usa TOML e dataclasses tipadas para permitir
personalizacao completa da biblioteca. Todos os valores hardcoded foram
movidos para configuracoes.

### Modulos

#### settings/schema.py

Define dataclasses tipadas para cada secao de configuracao:

```python
@dataclass
class BrandingConfig:
    company_name: str
    footer_format: str
    footer_format_no_source: str

@dataclass
class ColorsConfig:
    primary: str
    secondary: str
    # ...
    def cycle(self) -> list[str]: ...

@dataclass
class ChartingConfig:
    branding: BrandingConfig
    colors: ColorsConfig
    fonts: FontsConfig
    layout: LayoutConfig
    # ... todas as subsecoes
```

#### settings/defaults.py

Instancia `DEFAULT_CONFIG` com valores da Agora Investimentos:

```python
DEFAULT_CONFIG = ChartingConfig(
    branding=BrandingConfig(
        company_name="Agora Investimentos",
        # ...
    ),
    colors=ColorsConfig(
        primary="#00464D",
        # ...
    ),
    # ...
)
```

#### settings/loader.py

Carrega e faz merge de configuracoes de multiplas fontes:

```python
class ConfigLoader:
    def configure(self, config_path=None, **overrides): ...
    def get_config(self) -> ChartingConfig: ...
    def reset(self): ...

# Funcoes publicas
def configure(**kwargs) -> ConfigLoader: ...
def get_config() -> ChartingConfig: ...
def reset_config() -> ConfigLoader: ...
```

### Ordem de Precedencia

1. `configure()` - Overrides programaticos
2. `configure(config_path=...)` - Arquivo explicito
3. `.charting.toml` / `charting.toml` - Projeto local
4. `pyproject.toml [tool.charting]` - Secao no pyproject
5. `~/.config/charting/config.toml` - Usuario global
6. Defaults built-in

### Merge de Configuracoes

O loader faz deep merge de dicionarios:

```python
base = {'colors': {'primary': '#000'}, 'layout': {'dpi': 100}}
override = {'colors': {'primary': '#FFF'}}
# Resultado: {'colors': {'primary': '#FFF'}, 'layout': {'dpi': 100}}
```

### Como Usar Configuracoes

Todos os modulos acessam configuracoes via `get_config()`:

```python
from ..settings import get_config

def add_footer(fig, source=None):
    config = get_config()
    branding = config.branding

    if source:
        text = branding.footer_format.format(
            source=source,
            company_name=branding.company_name,
        )
    # ...
```

---

## Fluxo de Plotagem

```
DataFrame
    │
    ▼
df.agora.plot()
    │
    ▼
AgoraAccessor.plot()
    │
    ▼
AgoraPlotter.plot()
    │
    ├─1─► get_config()            # Carrega configuracao
    │
    ├─2─► theme.apply()           # Aplica estilo matplotlib
    │
    ├─3─► Resolve X/Y data        # Index vs coluna, dtypes
    │
    ├─4─► _apply_y_formatter()    # Configura formatador do eixo Y
    │
    ├─5─► plot_line() / plot_bar() # Renderiza dados principais
    │
    ├─6─► _apply_overlays()       # MM, ATH/ATL, hlines, bands
    │
    ├─7─► resolve_collisions()    # Evita sobreposicao de labels
    │
    ├─8─► _apply_title()          # Titulo centralizado
    │
    ├─9─► _apply_decorations()    # Footer
    │
    └─10─► save() (opcional)      # Exporta imagem
    │
    ▼
matplotlib.axes.Axes
```

---

## Classes Principais

### AgoraAccessor

**Arquivo:** `accessor.py`

Registra o accessor `.agora` em todos os DataFrames pandas.

```python
@pd.api.extensions.register_dataframe_accessor("agora")
class AgoraAccessor:
    def __init__(self, pandas_obj): ...
    def plot(self, **kwargs): ...
    def save(self, path): ...
```

- Instancia um `AgoraPlotter` lazy (criado no primeiro uso)
- Delega todas as chamadas para o plotter

### AgoraPlotter

**Arquivo:** `engine.py`

Orquestrador principal da construcao de graficos.

```python
class AgoraPlotter:
    def __init__(self, df: pd.DataFrame): ...
    def plot(self, x, y, kind, title, units, ...) -> Axes: ...
    def save(self, path, dpi=None): ...
```

Responsabilidades:
- Resolucao de dados X/Y
- Aplicacao de tema e formatadores
- Orquestracao de plots e overlays
- Exportacao de imagens

### ChartingTheme

**Arquivo:** `styling/theme.py`

Gerencia identidade visual com lazy loading de configuracoes.

```python
class ChartingTheme:
    @property
    def colors(self) -> ColorsConfig: ...
    @property
    def font(self) -> FontProperties: ...

    def apply(self) -> self: ...  # Configura matplotlib
```

### ChartingConfig

**Arquivo:** `settings/schema.py`

Dataclass principal com todas as configuracoes:

```python
@dataclass
class ChartingConfig:
    branding: BrandingConfig
    colors: ColorsConfig
    fonts: FontsConfig
    layout: LayoutConfig
    lines: LinesConfig
    bars: BarsConfig
    bands: BandsConfig
    markers: MarkersConfig
    collision: CollisionConfig
    transforms: TransformsConfig
    formatters: FormattersConfig
    labels: LabelsConfig
    paths: PathsConfig
```

---

## Pontos de Extensao

### Novas Configuracoes

1. Adicionar dataclass em `settings/schema.py`
2. Adicionar campo em `ChartingConfig`
3. Adicionar default em `settings/defaults.py`
4. Usar via `get_config().nova_secao.campo`

### Novos Formatadores

Adicionar ao dicionario `_FORMATTERS` em `engine.py`:

```python
_FORMATTERS = {
    'BRL': lambda: currency_formatter('BRL'),
    'USD': lambda: currency_formatter('USD'),
    '%': percent_formatter,
    'human': human_readable_formatter,
    'points': points_formatter,
    # Adicionar aqui:
    'EUR': lambda: currency_formatter('EUR'),
}
```

E implementar em `styling/formatters.py`.

### Novos Tipos de Grafico

1. Criar arquivo em `plots/` (ex: `scatter.py`)
2. Implementar funcao `plot_scatter(ax, x, y_data, **kwargs)`
3. Adicionar ao switch em `AgoraPlotter.plot()`:

```python
if kind == 'scatter':
    plot_scatter(ax, x_data, y_data, **kwargs)
```

### Novos Overlays

1. Criar arquivo em `overlays/` (ex: `trend_line.py`)
2. Implementar funcao `add_trend_line(ax, x, y_data, **kwargs)`
3. Exportar em `overlays/__init__.py`
4. Chamar em `AgoraPlotter._apply_overlays()`

### Novos Componentes

1. Criar arquivo em `components/`
2. Implementar funcao `add_*(ax_or_fig, ...)`
3. Exportar em `components/__init__.py`

---

## Convencoes

### Acesso a Configuracoes

Sempre usar `get_config()` dentro das funcoes, nunca cachear globalmente:

```python
# CORRETO
def minha_funcao():
    config = get_config()
    cor = config.colors.primary

# ERRADO (nao reflete mudancas via configure())
config = get_config()  # Global
def minha_funcao():
    cor = config.colors.primary
```

### zorder (Camadas)

| Camada | zorder | Elementos |
|--------|--------|-----------|
| Fundo | 0 | Bandas sombreadas |
| Referencia | 1 | ATH, ATL, hlines |
| Secundario | 2 | Media movel |
| Dados | 3+ | Linhas, barras |

### Retorno de Funcoes

- `plot_*()`: Nao retorna (modifica ax in-place)
- `add_*()`: Nao retorna (modifica ax/fig in-place)
- `AgoraPlotter.plot()`: Retorna `Axes`

### Tratamento de Series vs DataFrame

Todas as funcoes de plot aceitam ambos:

```python
if isinstance(y_data, pd.Series):
    y_data = y_data.to_frame()
# Continua com logica unificada para DataFrame
```

### Cores

- Usar `theme.colors.*` para cores semanticas
- Usar `theme.colors.cycle()` para multiplas series
- Permitir override via parametro `color`

### Defaults de Parametros

Quando um parametro pode vir da config, usar `None` como default:

```python
def add_band(ax, lower, upper, alpha=None):
    config = get_config()
    band_alpha = alpha if alpha is not None else config.bands.alpha
```
