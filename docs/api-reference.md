# API Reference

Referencia completa da API publica do chartkit.

## Pandas Accessor

### df.chartkit.plot()

Metodo principal para criacao de graficos.

```python
df.chartkit.plot(
    x: str = None,              # Coluna para eixo X (padrao: index)
    y: str | list[str] = None,  # Coluna(s) para eixo Y (padrao: todas numericas)
    kind: str = 'line',         # Tipo: 'line' ou 'bar'
    title: str = None,          # Titulo do grafico
    units: str = None,          # Formatacao do eixo Y
    source: str = None,         # Fonte para rodape
    highlight_last: bool = False,  # Destaca ultimo valor
    y_origin: str = 'zero',     # Origem Y para barras: 'zero' ou 'auto'
    save_path: str = None,      # Caminho para salvar
    moving_avg: int = None,     # Janela da media movel
    show_ath: bool = False,     # Linha no All-Time High
    show_atl: bool = False,     # Linha no All-Time Low
    overlays: dict = None,      # Overlays customizados
    **kwargs                    # Argumentos extras para matplotlib
) -> matplotlib.axes.Axes
```

#### Parametros

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `x` | str | None | Coluna para eixo X. Se None, usa o index |
| `y` | str \| list[str] | None | Coluna(s) para eixo Y. Se None, usa todas as colunas numericas |
| `kind` | str | 'line' | Tipo de grafico: 'line' ou 'bar' |
| `title` | str | None | Titulo do grafico |
| `units` | str | None | Formatacao do eixo Y (ver tabela abaixo) |
| `source` | str | None | Fonte dos dados para rodape |
| `highlight_last` | bool | False | Se True, destaca o ultimo valor |
| `y_origin` | str | 'zero' | Origem do eixo Y para barras: 'zero' ou 'auto' |
| `save_path` | str | None | Caminho para salvar o grafico |
| `moving_avg` | int | None | Janela da media movel (ex: 12 para MM12) |
| `show_ath` | bool | False | Mostra linha no maximo historico |
| `show_atl` | bool | False | Mostra linha no minimo historico |
| `overlays` | dict | None | Overlays customizados (ver [Overlays](overlays.md)) |

#### Retorno

Objeto `matplotlib.axes.Axes` do grafico gerado.

### df.chartkit.save()

Salva o grafico atual em arquivo.

```python
df.chartkit.save(path: str, dpi: int = None)
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `path` | str | - | Caminho do arquivo |
| `dpi` | int | None | Resolucao em DPI (default: config.layout.dpi) |

**Importante:** Requer que `plot()` tenha sido chamado antes.

---

## Formatadores (units)

| Valor | Formato | Exemplo |
|-------|---------|---------|
| `'BRL'` | Real brasileiro | R$ 1.234,56 |
| `'USD'` | Dolar americano | $ 1,234.56 |
| `'%'` | Percentual | 10,5% |
| `'points'` | Inteiros BR | 1.234.567 |
| `'human'` | Notacao compacta | 1,2M |

---

## Graficos

### Grafico de Linhas

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'serie_a': [10, 12, 11, 14, 13],
    'serie_b': [8, 9, 10, 11, 12],
}, index=pd.date_range('2024-01', periods=5, freq='ME'))

# Linha simples
df[['serie_a']].chartkit.plot(title="Serie A", units='%')

# Multiplas series
df.chartkit.plot(title="Comparativo", units='%')
```

### Grafico de Barras

```python
df = pd.DataFrame({
    'saldo': [100, -50, 200, -75, 150]
}, index=pd.date_range('2024-01', periods=5, freq='ME'))

# Barras com origem no zero
df.chartkit.plot(kind='bar', title="Saldo Mensal", units='human')

# Barras com origem automatica (foca nos dados)
df.chartkit.plot(kind='bar', title="Saldo Mensal", y_origin='auto')
```

---

## ChartingPlotter (Uso Avancado)

Para controle total, use a classe ChartingPlotter diretamente.

```python
from chartkit import ChartingPlotter

plotter = ChartingPlotter(df)
ax = plotter.plot(kind='line', title='Titulo', units='%')
plotter.save('grafico.png')
```

### Construtor

```python
ChartingPlotter(df: pd.DataFrame)
```

### Metodos

- `plot(**kwargs)` - Mesmos parametros de `df.chartkit.plot()`
- `save(path: str, dpi: int = None)` - Salva o grafico (dpi default via config)

---

## Configuracao

O sistema de configuracao usa arquivos TOML e permite personalizacao completa.
Veja [Configuration](configuration.md) para o guia completo.

### configure()

Configura o modulo programaticamente.

```python
from chartkit import configure
from pathlib import Path

# Arquivo TOML explicito
configure(config_path=Path('./minha-config.toml'))

# Path de outputs
configure(outputs_path=Path('./meus_outputs'))

# Overrides por secao
configure(branding={'company_name': 'Minha Empresa'})
configure(colors={'primary': '#FF0000'})
configure(layout={'figsize': [12.0, 8.0], 'dpi': 150})

# Multiplos overrides
configure(
    branding={'company_name': 'Empresa'},
    colors={'primary': '#FF0000'},
)
```

### get_config()

Retorna a configuracao atual (dataclass tipada).

```python
from chartkit import get_config

config = get_config()
print(config.branding.company_name)
print(config.colors.primary)
print(config.layout.figsize)
print(config.fonts.sizes.title)
```

### reset_config()

Reseta configuracoes para os defaults.

```python
from chartkit.settings import reset_config

reset_config()
```

### get_assets_path() / get_outputs_path()

Retorna paths resolvidos seguindo a cadeia de precedencia.

```python
from chartkit.settings import get_assets_path, get_outputs_path

# Retorna Path absoluto resolvido
assets = get_assets_path()  # Path para assets (fontes, imagens, etc)
outputs = get_outputs_path()  # Path para outputs

# Cadeia de precedencia:
# 1. configure(assets_path=...) / configure(outputs_path=...)
# 2. TOML: [paths].assets_dir / [paths].outputs_dir
# 3. Auto-discovery via AST (ASSETS_PATH / OUTPUTS_PATH do projeto host)
# 4. Fallback: project_root/assets ou project_root/outputs
```

### reset_project_root_cache()

Limpa o cache de project root. Util para testes.

```python
from chartkit.settings.discovery import reset_project_root_cache

# Em testes que mudam o diretorio de trabalho
reset_project_root_cache()
```

### Variaveis Globais

```python
from chartkit import CHARTS_PATH, OUTPUTS_PATH, ASSETS_PATH

# CHARTS_PATH: Path onde graficos sao salvos (lazy evaluation)
# OUTPUTS_PATH: Path base de outputs (lazy evaluation)
# ASSETS_PATH: Path base de assets como fontes (lazy evaluation)
```

### ChartingConfig

Dataclass tipada com todas as configuracoes:

```python
from chartkit import ChartingConfig, get_config

config: ChartingConfig = get_config()

# Secoes disponiveis
config.branding      # BrandingConfig
config.colors        # ColorsConfig
config.fonts         # FontsConfig
config.layout        # LayoutConfig
config.lines         # LinesConfig
config.bars          # BarsConfig
config.bands         # BandsConfig
config.markers       # MarkersConfig
config.collision     # CollisionConfig
config.transforms    # TransformsConfig
config.formatters    # FormattersConfig
config.labels        # LabelsConfig
config.paths         # PathsConfig
```

---

## Exports do Modulo

```python
from chartkit import (
    # Configuracao
    configure,
    get_config,
    reset_config,
    ChartingConfig,
    # Paths (lazy evaluation via __getattr__)
    CHARTS_PATH,
    OUTPUTS_PATH,
    ASSETS_PATH,
    # Classes
    ChartingAccessor,
    ChartingPlotter,
    theme,
    # Transforms
    yoy,
    mom,
    accum_12m,
    diff,
    normalize,
    annualize_daily,
    compound_rolling,
    real_rate,
    to_month_end,
)
```
