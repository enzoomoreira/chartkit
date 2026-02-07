# Transforms

Funcoes de transformacao para series temporais financeiras.

## Resumo

| Funcao | Descricao | Uso tipico |
|--------|-----------|------------|
| `mom()` | Variacao mes contra mes | IPCA mensal |
| `yoy()` | Variacao ano contra ano | Crescimento anual |
| `accum()` | Acumulado em janela movel | IPCA 12m |
| `diff()` | Diferenca absoluta | Variacao em p.p. |
| `normalize()` | Normaliza para base | Comparar escalas |
| `drawdown()` | Distancia percentual do pico | Queda de ativos |
| `zscore()` | Padronizacao estatistica | Comparar series |
| `annualize_daily()` | Anualiza taxa diaria | CDI anual |
| `compound_rolling()` | Retorno composto | Selic 12m |
| `to_month_end()` | Normaliza para fim do mes | Alinhar series |

## Import

```python
from chartkit import (
    yoy, mom, accum, diff, normalize,
    drawdown, zscore,
    annualize_daily, compound_rolling, to_month_end,
)
```

## Uso Encadeado via Accessor

Todos os transforms podem ser encadeados diretamente no DataFrame usando o accessor `.chartkit`:

```python
import pandas as pd

# Carregar dados
df = pd.read_csv('dados.csv', index_col=0, parse_dates=True)

# Encadeamento simples
df.chartkit.yoy().plot(title="Variacao YoY")

# Multiplos transforms em cadeia
df.chartkit.yoy().mom().plot()

# Com metricas e salvamento
df.chartkit.annualize_daily().plot(metrics=['ath']).save('chart.png')

# Acesso ao DataFrame transformado (sem plotar)
df_transformed = df.chartkit.yoy().df
```

O accessor retorna um `TransformAccessor` que permite encadear quantas transformacoes forem necessarias antes de finalizar com `.plot()` ou acessar o DataFrame via `.df`.

## Contrato Unificado de Entrada

Todas as funcoes de transformacao aceitam multiplos tipos de entrada:

- `pd.DataFrame` e `pd.Series` (tipos primarios)
- `dict`, `list` e `np.ndarray` (convertidos automaticamente)

A coercao e feita internamente. Colunas nao-numericas sao filtradas com warning, e valores `inf`/`-inf` no resultado sao substituidos por `NaN`.

## Auto-Deteccao de Frequencia

As funcoes `mom`, `yoy`, `accum` e `compound_rolling` detectam automaticamente a frequencia dos dados via `pd.infer_freq`, resolvendo o numero de periodos adequado (ex: 12 para dados mensais, 252 para diarios).

Voce pode usar o parametro `freq=` como alternativa a `periods=`/`window=`:

```python
# Auto-detect (usa pd.infer_freq)
df_yoy = yoy(df)

# Frequencia explicita
df_yoy = yoy(df, freq='M')    # Mensal: 12 periodos
df_yoy = yoy(df, freq='Q')    # Trimestral: 4 periodos

# Periodos explicitos (mutuamente exclusivo com freq)
df_yoy = yoy(df, periods=4)   # Override direto
```

Frequencias suportadas: `D`, `B`, `W`, `M`, `Q`, `Y` (incluindo aliases e freq codes ancorados do pandas).

---

## Transformacoes Basicas

### mom() - Variacao Mensal

Calcula variacao percentual mes contra mes (Month-over-Month). A frequencia e detectada automaticamente; use `freq=` ou `periods=` para override.

```python
def mom(df, periods: int | None = None, freq: str | None = None) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Dados de entrada |
| `periods` | int \| None | None | Periodos para comparacao. Mutuamente exclusivo com `freq` |
| `freq` | str \| None | None | Frequencia dos dados (`'D'`, `'M'`, `'Q'`, etc.). Mutuamente exclusivo com `periods` |

**Exemplo:**

```python
import pandas as pd
from chartkit import mom

# Dados mensais
df = pd.DataFrame({
    'valor': [100, 102, 101, 105]
}, index=pd.date_range('2024-01', periods=4, freq='ME'))

# Variacao mensal em % (auto-detect: dados mensais -> periods=1)
df_mom = mom(df)
# Resultado: [NaN, 2.0, -0.98, 3.96]

# Frequencia explicita
df_mom = mom(df, freq='M')

# Via accessor
df.chartkit.mom().plot(title="Variacao Mensal")
```

---

### yoy() - Variacao Anual

Calcula variacao percentual ano contra ano (Year-over-Year). A frequencia e detectada automaticamente; use `freq=` ou `periods=` para override.

```python
def yoy(df, periods: int | None = None, freq: str | None = None) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Dados de entrada |
| `periods` | int \| None | None | Periodos para comparacao. Mutuamente exclusivo com `freq` |
| `freq` | str \| None | None | Frequencia dos dados (`'D'`, `'M'`, `'Q'`, etc.). Mutuamente exclusivo com `periods` |

**Exemplo:**

```python
from chartkit import yoy

# Dados mensais (auto-detect: mensal -> 12 periodos)
df_yoy = yoy(df)

# Dados trimestrais (auto-detect: trimestral -> 4 periodos)
df_yoy = yoy(df_trimestral)

# Frequencia explicita
df_yoy = yoy(df, freq='Q')  # Trimestral: 4 periodos

# Periodos explicitos
df_yoy = yoy(df, periods=4)

# Via accessor
df.chartkit.yoy().plot(title="Variacao Anual")
df.chartkit.yoy(freq='Q').plot()  # Trimestral
```

---

### accum() - Acumulado em Janela Movel

Calcula variacao acumulada via produto composto em janela movel. A janela e resolvida automaticamente pela frequencia dos dados (ex: 12 para mensal, 252 para diario).

**Formula:** `(Produto(1 + x/100) - 1) * 100`

```python
def accum(df, window: int | None = None, freq: str | None = None) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Taxas em percentual |
| `window` | int \| None | None | Tamanho da janela em periodos. Mutuamente exclusivo com `freq` |
| `freq` | str \| None | None | Frequencia dos dados (`'D'`, `'M'`, `'Q'`, etc.). Mutuamente exclusivo com `window` |

**Exemplo:**

```python
from chartkit import accum

# IPCA mensal -> IPCA acumulado 12 meses (auto-detect: mensal -> 12)
ipca_12m = accum(ipca_mensal)

# Janela explicita de 6 meses
ipca_6m = accum(ipca_mensal, window=6)

# Frequencia explicita
ipca_12m = accum(ipca_mensal, freq='M')

# Via accessor com plotagem
ipca_mensal.chartkit.accum().plot(
    title="IPCA Acumulado 12 Meses",
    units='%'
)
```

---

### diff() - Diferenca Absoluta

Calcula diferenca absoluta entre periodos.

```python
def diff(df, periods: int = 1) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Dados com indice temporal |
| `periods` | int | 1 | Periodos para diferenca |

**Exemplo:**

```python
from chartkit import diff

# Variacao em pontos percentuais
df_diff = diff(selic)  # Diferenca para periodo anterior

# Diferenca de 12 meses
df_diff_12m = diff(selic, periods=12)

# Via accessor
selic.chartkit.diff().plot(title="Variacao da Selic (p.p.)")
```

---

### normalize() - Normalizacao

Normaliza serie para um valor base em data especifica. Util para comparar series com escalas diferentes. Usa o primeiro valor nao-NaN como referencia; `base_date` busca a data mais proxima (nearest) se a data exata nao existir no indice.

```python
def normalize(df, base: int | None = None, base_date: str | None = None) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Dados com indice temporal |
| `base` | int \| None | None | Valor base para normalizacao (default: `config.transforms.normalize_base`) |
| `base_date` | str \| None | None | Data base. Se None, usa primeiro valor nao-NaN. Busca nearest se data exata nao existir |

**Exemplo:**

```python
from chartkit import normalize
import pandas as pd

# Base 100 na primeira data
df_norm = normalize(df)

# Base 100 em data especifica
df_norm = normalize(df, base_date='2020-01-01')

# Comparar duas series com escalas diferentes
series_a = normalize(df['ibovespa'])
series_b = normalize(df['sp500'])

comparativo = pd.concat([series_a, series_b], axis=1)
comparativo.chartkit.plot(title="Comparativo Base 100")

# Via accessor
df.chartkit.normalize(base_date='2020-01-01').plot(
    title="Indices Normalizados (Base 100 = Jan/2020)"
)
```

---

## Analise Estatistica

### drawdown() - Distancia do Pico

Calcula a distancia percentual do pico historico (cumulative maximum). Retorna valores <= 0, onde 0 indica que o valor esta no pico e valores negativos indicam a magnitude da queda.

**Formula:** `(data / cummax - 1) * 100`

Requer valores estritamente positivos. Raises `TransformError` se os dados contiverem zero ou negativos.

```python
def drawdown(df) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Dados com valores positivos (precos, indices) |

**Exemplo:**

```python
from chartkit import drawdown

# Queda em relacao ao pico
dd = drawdown(ibovespa)
# Resultado: [0, -2.3, -5.1, 0, -1.2, ...]

# Via accessor
ibovespa.chartkit.drawdown().plot(
    title="Drawdown do Ibovespa",
    units='%'
)
```

---

### zscore() - Padronizacao Estatistica

Transforma a serie em unidades de desvio padrao em relacao a media. Permite comparar series com unidades completamente diferentes no mesmo grafico.

- **Global** (sem `window`): `(data - mean) / std`
- **Rolling** (com `window`): `(data - rolling_mean) / rolling_std`

```python
def zscore(df, window: int | None = None) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Dados de entrada |
| `window` | int \| None | None | Janela rolling. Se None, calcula z-score global |

**Exemplo:**

```python
from chartkit import zscore

# Z-score global
df_z = zscore(df)

# Z-score rolling (janela de 12 periodos)
df_z = zscore(df, window=12)

# Comparar series com escalas diferentes
import pandas as pd

df = pd.DataFrame({
    'ibovespa': ibov_values,
    'sp500': sp_values,
})

# Z-score elimina escala, permite comparacao direta
df.chartkit.zscore().plot(title="Ibovespa vs S&P 500 (Z-Score)")
```

---

## Transformacoes de Juros

### annualize_daily() - Anualizar Taxa Diaria

Anualiza taxa diaria para taxa anual usando juros compostos.

**Formula:** `((1 + r_diaria) ^ dias_uteis - 1) * 100`

```python
def annualize_daily(df, trading_days: int = 252) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Taxas diarias em % |
| `trading_days` | int | 252 | Dias uteis no ano |

**Exemplo:**

```python
from chartkit import annualize_daily

# CDI diario -> CDI anualizado
cdi_anual = annualize_daily(cdi_diario)

# Usando 250 dias uteis
cdi_anual = annualize_daily(cdi_diario, trading_days=250)

# Via accessor
cdi_diario.chartkit.annualize_daily().plot(
    title="CDI Anualizado",
    units='%'
)
```

---

### compound_rolling() - Retorno Composto

Calcula retorno composto em janela movel. Multiplica os fatores (1 + taxa) ao longo da janela. Suporta auto-deteccao de frequencia.

**Formula:** `Produto(1 + taxa/100) - 1`

```python
def compound_rolling(df, window: int | None = None, freq: str | None = None) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Taxas em % |
| `window` | int \| None | None | Janela em periodos. Mutuamente exclusivo com `freq` |
| `freq` | str \| None | None | Frequencia dos dados (`'D'`, `'M'`, `'Q'`, etc.). Mutuamente exclusivo com `window` |

**Exemplo:**

```python
from chartkit import compound_rolling

# Selic mensal -> Selic acumulada 12 meses (auto-detect)
selic_12m = compound_rolling(selic_mensal)

# Janela de 6 meses
selic_6m = compound_rolling(selic_mensal, window=6)

# Frequencia explicita
selic_12m = compound_rolling(selic_mensal, freq='M')

# Via accessor
selic_mensal.chartkit.compound_rolling().plot(
    title="Selic Acumulada 12 Meses",
    units='%'
)
```

---

### to_month_end() - Normalizar para Fim do Mes

Normaliza indice temporal para ultimo dia do mes. Util para alinhar series com frequencias diferentes antes de operacoes. Raises `TypeError` se o indice nao for `DatetimeIndex`.

```python
def to_month_end(df) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Dados com DatetimeIndex |

**Exemplo:**

```python
from chartkit import to_month_end

# Alinhar series antes de operacoes
selic = to_month_end(selic)
ipca = to_month_end(ipca)

# Agora podem ser operadas juntas
spread = selic - ipca

# Via accessor
selic.chartkit.to_month_end().plot()
```

---

## Casos de Uso Compostos

### Comparacao de Indices Base 100

Comparar performance de ativos com escalas diferentes:

```python
import pandas as pd
from chartkit import normalize

# Duas series com escalas diferentes
df = pd.DataFrame({
    'ibovespa': [100000, 105000, 102000, 110000],
    'sp500': [4000, 4200, 4100, 4400],
}, index=pd.date_range('2024-01', periods=4, freq='ME'))

# Normaliza para base 100
df_norm = normalize(df)

# Compara evolucao
df_norm.chartkit.plot(title="Ibovespa vs S&P500 (Base 100)")
```

### IPCA Mensal para 12 Meses

Transformar variacao mensal em acumulado anualizado:

```python
# IPCA mensal (ex: 0.5, 0.3, 0.8, ...)
ipca_mensal.chartkit.accum().plot(
    title="IPCA Acumulado 12 Meses",
    units='%'
)
```

### Selic Diaria para Taxa Anual

Converter taxa diaria do CDI/Selic para equivalente anual:

```python
# CDI diario (ex: 0.0398, 0.0399, ...)
cdi.chartkit.annualize_daily().plot(
    title="CDI - Taxa Anual Equivalente",
    units='%'
)
```

### Juro Real (Selic - IPCA)

Calcular spread entre taxa nominal e inflacao:

```python
from chartkit import to_month_end, compound_rolling, accum

# Alinhar frequencias
selic = to_month_end(selic_mensal)
ipca = to_month_end(ipca_mensal)

# Calcular acumulados 12 meses
selic_12m = compound_rolling(selic)
ipca_12m = accum(ipca)

# Spread (aproximacao simplificada)
juro_real = selic_12m - ipca_12m
juro_real.chartkit.plot(
    title="Juro Real (Selic - IPCA)",
    units='p.p.'
)
```

### Variacao YoY com Destaque de Metricas

Analisar variacao anual com metricas automaticas:

```python
# PIB ou outro indicador economico
pib.chartkit.yoy().plot(
    title="Crescimento do PIB (YoY)",
    metrics=['ath', 'atl', 'last'],
    units='%'
)
```

### Encadeamento Complexo

Multiplas transformacoes em sequencia:

```python
# Taxa diaria -> anualizada -> variacao YoY
cdi_diario.chartkit \
    .annualize_daily() \
    .yoy() \
    .plot(title="CDI Anualizado - Variacao YoY")

# Acessar dados transformados sem plotar
df_final = cdi_diario.chartkit \
    .annualize_daily() \
    .to_month_end() \
    .df

# Usar DataFrame transformado em outras operacoes
df_final.describe()
```
