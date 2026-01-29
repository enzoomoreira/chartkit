# API Reference

Referencia completa da API publica do agora-charting.

## Pandas Accessor

### df.agora.plot()

Metodo principal para criacao de graficos.

```python
df.agora.plot(
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

### df.agora.save()

Salva o grafico atual em arquivo.

```python
df.agora.save(path: str, dpi: int = None)
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
import agora_charting

df = pd.DataFrame({
    'serie_a': [10, 12, 11, 14, 13],
    'serie_b': [8, 9, 10, 11, 12],
}, index=pd.date_range('2024-01', periods=5, freq='ME'))

# Linha simples
df[['serie_a']].agora.plot(title="Serie A", units='%')

# Multiplas series
df.agora.plot(title="Comparativo", units='%')
```

### Grafico de Barras

```python
df = pd.DataFrame({
    'saldo': [100, -50, 200, -75, 150]
}, index=pd.date_range('2024-01', periods=5, freq='ME'))

# Barras com origem no zero
df.agora.plot(kind='bar', title="Saldo Mensal", units='human')

# Barras com origem automatica (foca nos dados)
df.agora.plot(kind='bar', title="Saldo Mensal", y_origin='auto')
```

---

## AgoraPlotter (Uso Avancado)

Para controle total, use a classe AgoraPlotter diretamente.

```python
from agora_charting import AgoraPlotter

plotter = AgoraPlotter(df)
ax = plotter.plot(kind='line', title='Titulo', units='%')
plotter.save('grafico.png')
```

### Construtor

```python
AgoraPlotter(df: pd.DataFrame)
```

### Metodos

- `plot(**kwargs)` - Mesmos parametros de `df.agora.plot()`
- `save(path: str, dpi: int = None)` - Salva o grafico (dpi default via config)

---

## Configuracao

O sistema de configuracao usa arquivos TOML e permite personalizacao completa.
Veja [Configuration](configuration.md) para o guia completo.

### configure()

Configura o modulo programaticamente.

```python
from agora_charting import configure
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
from agora_charting import get_config

config = get_config()
print(config.branding.company_name)
print(config.colors.primary)
print(config.layout.figsize)
print(config.fonts.sizes.title)
```

### get_settings()

**Deprecated:** Use `get_config()` ao inves.

```python
from agora_charting import get_settings

settings = get_settings()  # Retorna ChartingConfig
```

### reset_config()

Reseta configuracoes para os defaults.

```python
from agora_charting.settings import reset_config

reset_config()
```

### Variaveis Globais

```python
from agora_charting import CHARTS_PATH, OUTPUTS_PATH

# CHARTS_PATH: Path onde graficos sao salvos (lazy evaluation)
# OUTPUTS_PATH: Path base de outputs (lazy evaluation)
```

### ChartingConfig

Dataclass tipada com todas as configuracoes:

```python
from agora_charting import ChartingConfig, get_config

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
from agora_charting import (
    # Configuracao
    configure,
    get_config,
    get_settings,      # Deprecated, use get_config()
    reset_config,
    ChartingConfig,
    CHARTS_PATH,
    OUTPUTS_PATH,
    # Classes
    AgoraAccessor,
    AgoraPlotter,
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
