# Arquitetura

Documentacao da arquitetura interna do chartkit para contribuidores.

---

## Diagrama de Componentes

```
                    +-------------------+
                    |    DataFrame      |
                    +-------------------+
                            |
                            v
                    +-------------------+
                    | ChartingAccessor  |  (df.chartkit)
                    +-------------------+
                        |         |
            +-----------+         +-----------+
            v                                 v
    +-------------------+           +-------------------+
    | TransformAccessor |           |  ChartingPlotter  |
    +-------------------+           +-------------------+
            |                               |
            v                               v
    +-------------------+           +-------------------+
    |   Transforms      |           |     PlotResult    |
    +-------------------+           +-------------------+
                                            |
                    +-----------------------+
                    v
        +-------------------+
        |    matplotlib     |
        |  (Figure/Axes)    |
        +-------------------+
```

---

## Fluxo de Dados

O fluxo principal de dados segue a cadeia:

```
DataFrame -> Accessor -> Plotter -> PlotResult
```

### Descricao Detalhada

1. **DataFrame**: Dados de entrada (pandas DataFrame com DatetimeIndex)

2. **ChartingAccessor**: Registrado via `@pd.api.extensions.register_dataframe_accessor("chartkit")`. Funciona como ponto de entrada para todas as operacoes.

3. **TransformAccessor** (opcional): Quando o usuario chama transforms como `.yoy()`, `.mom()`, etc., um TransformAccessor e retornado. Cada transform retorna um novo TransformAccessor, permitindo encadeamento.

4. **ChartingPlotter**: Motor principal que orquestra a criacao do grafico:
   - Aplica tema via `theme.apply()`
   - Resolve dados X/Y
   - Aplica formatadores de eixo
   - Delega para `plot_line()` ou `plot_bar()`
   - Aplica metricas via `MetricRegistry.apply()`
   - Resolve colisoes de labels
   - Adiciona decoracoes (footer)

5. **PlotResult**: Resultado encapsulado com:
   - Referencia ao Figure e Axes
   - Metodos `.save()` e `.show()` para encadeamento
   - Properties `.axes` e `.figure` para acesso direto

### Fluxo Visual Detalhado

```mermaid
flowchart TD
    A[DataFrame] --> B["df.chartkit.plot()"]
    B --> C["ChartingAccessor.plot()"]
    C --> D["ChartingPlotter.plot()"]

    D --> D1["1. get_config()"]
    D1 --> D2["2. theme.apply()"]
    D2 --> D3["3. Resolve X/Y data"]
    D3 --> D4["4. _apply_y_formatter()"]
    D4 --> D5["5. plot_line() / plot_bar()"]
    D5 --> D6["6. MetricRegistry.apply()"]
    D6 --> D7["7. resolve_collisions()"]
    D7 --> D8["8. _apply_title()"]
    D8 --> D9["9. _apply_decorations()"]
    D9 --> D10["10. save() (opcional)"]
    D10 --> E["PlotResult"]
```

---

## Estrutura de Pastas

```
src/chartkit/
├── __init__.py           # Entry point, exports publicos, configure_logging()
├── accessor.py           # Pandas DataFrame accessor (.chartkit)
├── engine.py             # ChartingPlotter - orquestrador principal
├── result.py             # PlotResult - resultado encadeavel
│
├── settings/             # Sistema de configuracao TOML
│   ├── __init__.py       # Exports: configure, get_config, ChartingConfig
│   ├── schema.py         # Dataclasses tipadas para configuracao
│   ├── defaults.py       # Valores default neutros
│   ├── loader.py         # ConfigLoader - carregamento e cache
│   ├── toml.py           # Parsing TOML e deep merge
│   ├── converters.py     # Conversao dataclass <-> dict
│   ├── discovery.py      # Descoberta de project root e config files
│   ├── paths.py          # PathResolver - resolucao unificada de paths
│   └── ast_discovery.py  # Auto-discovery de paths via AST parsing
│
├── styling/              # Tema e formatadores
│   ├── __init__.py       # Facade
│   ├── theme.py          # ChartingTheme (usa settings)
│   ├── formatters.py     # Formatadores de eixo Y (Babel i18n)
│   └── fonts.py          # Carregamento de fontes customizadas
│
├── charts/               # Tipos de graficos
│   ├── __init__.py       # Facade: plot_line, plot_bar
│   ├── line.py           # Grafico de linhas
│   └── bar.py            # Grafico de barras
│
├── overlays/             # Elementos visuais secundarios
│   ├── __init__.py       # Facade
│   ├── moving_average.py # Media movel
│   ├── reference_lines.py# ATH, ATL, hlines
│   ├── bands.py          # Bandas sombreadas
│   └── markers.py        # Highlight de pontos/barras
│
├── decorations/          # Decoracoes visuais
│   ├── __init__.py       # Facade: add_footer
│   └── footer.py         # Rodape com branding
│
├── metrics/              # Sistema de metricas declarativas
│   ├── __init__.py       # Exports, registra metricas builtin
│   ├── registry.py       # MetricRegistry - registro e aplicacao
│   └── builtin.py        # Metricas padrao (ath, atl, ma, hline, band)
│
├── transforms/           # Transformacoes temporais
│   ├── __init__.py       # Facade: yoy, mom, accum_12m, etc.
│   ├── temporal.py       # Implementacoes das funcoes de transformacao
│   └── accessor.py       # TransformAccessor para encadeamento
│
└── _internal/            # Utilitarios privados
    ├── __init__.py       # Facade: register_moveable, register_fixed, register_passive, resolve_collisions
    └── collision.py      # Engine generica de resolucao de colisao (bbox-based)
```

---

## Responsabilidades de Cada Modulo

### Core

| Modulo | Responsabilidade |
|--------|-----------------|
| `accessor.py` | Registra `.chartkit` em DataFrames; delega para TransformAccessor ou ChartingPlotter |
| `engine.py` | Orquestra criacao de graficos; gerencia Figure/Axes; aplica componentes |
| `result.py` | Encapsula resultado; permite encadeamento com `.save()` e `.show()` |

### Settings

| Modulo | Responsabilidade |
|--------|-----------------|
| `schema.py` | Define dataclasses tipadas para todas as secoes de config |
| `defaults.py` | Valores default neutros (nao assumem contexto especifico) |
| `loader.py` | ConfigLoader singleton; carrega e faz merge de configs; gerencia caches |
| `toml.py` | Parsing de arquivos TOML; funcao `deep_merge()` para dicionarios |
| `converters.py` | Converte entre dataclasses e dicionarios |
| `discovery.py` | Encontra project root e arquivos de config |
| `paths.py` | PathResolver com cadeia de precedencia |
| `ast_discovery.py` | Descobre OUTPUTS_PATH/ASSETS_PATH via analise AST |

### Styling

| Modulo | Responsabilidade |
|--------|-----------------|
| `theme.py` | ChartingTheme; configura matplotlib com cores/fontes do settings |
| `formatters.py` | Formatadores de eixo Y (BRL, USD, %, human, points) usando Babel |
| `fonts.py` | Carrega fontes customizadas do assets_path |

### Charts e Overlays

| Modulo | Responsabilidade |
|--------|-----------------|
| `charts/line.py` | Renderiza grafico de linhas |
| `charts/bar.py` | Renderiza grafico de barras |
| `overlays/*` | Adiciona elementos secundarios (MA, ATH/ATL, bandas, markers) |
| `decorations/footer.py` | Adiciona rodape com branding e fonte |

### Metrics

| Modulo | Responsabilidade |
|--------|-----------------|
| `registry.py` | MetricRegistry para registrar e aplicar metricas |
| `builtin.py` | Registra metricas padrao como wrappers dos overlays |

### Transforms

| Modulo | Responsabilidade |
|--------|-----------------|
| `temporal.py` | Funcoes puras de transformacao (yoy, mom, accum_12m, etc.) |
| `accessor.py` | TransformAccessor para encadeamento de transforms |

---

## Ordem de Precedencia de Configuracao

A configuracao e carregada de multiplas fontes com merge:

1. `configure()` - Overrides programaticos (maior prioridade)
2. `configure(config_path=...)` - Arquivo TOML explicito
3. `.charting.toml` / `charting.toml` - Projeto local
4. `pyproject.toml [tool.charting]` - Secao no pyproject
5. `~/.config/charting/config.toml` - Usuario global
6. Defaults built-in (menor prioridade)

---

## Convencoes de Codigo

### Acesso a Configuracoes

Sempre usar `get_config()` dentro de funcoes, nunca cachear globalmente:

```python
# CORRETO
def minha_funcao():
    config = get_config()
    cor = config.colors.primary

# INCORRETO (nao reflete mudancas via configure())
config = get_config()  # Global
def minha_funcao():
    cor = config.colors.primary
```

### zorder (Camadas de Renderizacao)

| Camada | zorder | Elementos |
|--------|--------|-----------|
| Fundo | 0 | Bandas sombreadas |
| Referencia | 1 | ATH, ATL, hlines |
| Secundario | 2 | Media movel |
| Dados | 3+ | Linhas, barras |

### Retornos de Funcao

- `plot_*()`: Nao retorna (modifica ax in-place)
- `add_*()`: Nao retorna (modifica ax/fig in-place)
- `ChartingPlotter.plot()`: Retorna `PlotResult`
- Transforms: Retornam `TransformAccessor` (encadeavel)

---

## Grafo de Dependencias Internas (Settings)

```
__init__.py
    <- loader.py
        <- ast_discovery.py
        <- converters.py
        <- defaults.py <- schema.py
        <- discovery.py <- defaults.py
        <- paths.py <- discovery.py
        <- toml.py
    <- schema.py
```

**Importante:** Evitar imports circulares. `loader.py` e o hub central.
Novos modulos devem importar de `schema.py` ou `defaults.py`, nunca de `loader.py`.
