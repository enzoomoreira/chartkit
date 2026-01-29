# Architecture

Documentacao da arquitetura interna para contribuidores.

## Estrutura de Modulos

```
src/agora_charting/
├── __init__.py           # Entry point, exports publicos
├── accessor.py           # Pandas DataFrame accessor (.agora)
├── engine.py             # AgoraPlotter - orquestrador principal
├── config.py             # Sistema de configuracao com auto-discovery
├── transforms.py         # Funcoes de transformacao temporal
├── assets/
│   └── fonts/
│       └── BradescoSans-Light.ttf
├── styling/
│   ├── __init__.py       # Facade
│   ├── theme.py          # AgoraTheme, ColorPalette
│   ├── formatters.py     # Formatadores de eixo Y
│   └── fonts.py          # Carregamento de fontes
├── plots/
│   ├── __init__.py       # Facade
│   ├── line.py           # Grafico de linhas
│   └── bar.py            # Grafico de barras
├── components/
│   ├── __init__.py       # Facade
│   ├── footer.py         # Rodape
│   ├── markers.py        # Highlight de pontos/barras
│   └── collision.py      # Resolucao de colisoes
└── overlays/
    ├── __init__.py       # Facade
    ├── moving_average.py # Media movel
    ├── reference_lines.py # ATH, ATL, hlines
    └── bands.py          # Bandas sombreadas
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
    ├─1─► theme.apply()           # Aplica estilo matplotlib
    │
    ├─2─► Resolve X/Y data        # Index vs coluna, dtypes
    │
    ├─3─► _apply_y_formatter()    # Configura formatador do eixo Y
    │
    ├─4─► plot_line() / plot_bar() # Renderiza dados principais
    │
    ├─5─► _apply_overlays()       # MM, ATH/ATL, hlines, bands
    │
    ├─6─► resolve_collisions()    # Evita sobreposicao de labels
    │
    ├─7─► _apply_title()          # Titulo centralizado
    │
    ├─8─► _apply_decorations()    # Footer
    │
    └─9─► save() (opcional)       # Exporta imagem
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
    def save(self, path, dpi=300): ...
```

Responsabilidades:
- Resolucao de dados X/Y
- Aplicacao de tema e formatadores
- Orquestracao de plots e overlays
- Exportacao de imagens

### AgoraTheme

**Arquivo:** `styling/theme.py`

Gerencia identidade visual.

```python
class AgoraTheme:
    colors: ColorPalette
    font: FontProperties

    def apply(self): ...  # Configura matplotlib
```

### ColorPalette

**Arquivo:** `styling/theme.py`

Dataclass com cores institucionais.

```python
@dataclass
class ColorPalette:
    primary: str = "#00464D"
    secondary: str = "#006B6B"
    # ...

    def cycle(self) -> List[str]: ...
```

---

## Sistema de Configuracao

**Arquivo:** `config.py`

### Auto-Discovery

1. Busca `PROJECT_ROOT_MARKERS` subindo a arvore:
   - `.git`
   - `pyproject.toml`
   - `setup.py`
   - `setup.cfg`
   - `.project-root`

2. Procura `OUTPUT_DIR_CONVENTIONS` no root:
   - `outputs/`
   - `data/outputs/`
   - `output/`
   - `data/output/`

### Precedencia

1. `configure()` - configuracao explicita
2. `AGORA_CHARTING_OUTPUTS_PATH` - env var
3. Auto-discovery
4. Fallback: `cwd/outputs/charts`

### ChartingSettings

Dataclass com lazy evaluation para paths.

```python
@dataclass
class ChartingSettings:
    @property
    def project_root(self) -> Path: ...
    @property
    def outputs_path(self) -> Path: ...
    @property
    def charts_path(self) -> Path: ...

    def configure(self, outputs_path, charts_subdir): ...
    def reset(self): ...
```

---

## Pontos de Extensao

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
