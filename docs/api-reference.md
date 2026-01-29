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
df.agora.save(path: str, dpi: int = 300)
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `path` | str | - | Caminho do arquivo |
| `dpi` | int | 300 | Resolucao em DPI |

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
- `save(path: str, dpi: int = 300)` - Salva o grafico

---

## Configuracao

### configure()

Configura paths do modulo.

```python
from agora_charting import configure
from pathlib import Path

configure(
    outputs_path: Path = None,    # Path base para outputs
    charts_subdir: str = None,    # Subdir para charts (default: 'charts')
) -> ChartingSettings
```

### get_settings()

Retorna a instancia global de configuracoes.

```python
from agora_charting import get_settings

settings = get_settings()
print(settings.charts_path)
print(settings.outputs_path)
print(settings.project_root)
```

### Variaveis Globais

```python
from agora_charting import CHARTS_PATH, OUTPUTS_PATH

# CHARTS_PATH: Path onde graficos sao salvos
# OUTPUTS_PATH: Path base de outputs
```

---

## Exports do Modulo

```python
from agora_charting import (
    # Configuracao
    configure,
    get_settings,
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
