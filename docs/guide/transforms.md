# Transforms

Funcoes de transformacao para series temporais financeiras.

## Resumo

| Funcao | Descricao | Uso tipico |
|--------|-----------|------------|
| `mom()` | Variacao mes contra mes | IPCA mensal |
| `yoy()` | Variacao ano contra ano | Crescimento anual |
| `accum_12m()` | Acumulado 12 meses | IPCA 12m |
| `diff()` | Diferenca absoluta | Variacao em p.p. |
| `normalize()` | Normaliza para base | Comparar escalas |
| `annualize_daily()` | Anualiza taxa diaria | CDI anual |
| `compound_rolling()` | Retorno composto | Selic 12m |
| `to_month_end()` | Normaliza para fim do mes | Alinhar series |

## Import

```python
from chartkit import (
    yoy, mom, accum_12m, diff, normalize,
    annualize_daily, compound_rolling, to_month_end
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

---

## Transformacoes Basicas

### mom() - Variacao Mensal

Calcula variacao percentual mes contra mes (Month-over-Month).

```python
def mom(df, periods: int = 1) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Dados com indice temporal |
| `periods` | int | 1 | Periodos para comparacao |

**Exemplo:**

```python
import pandas as pd
from chartkit import mom

# Dados mensais
df = pd.DataFrame({
    'valor': [100, 102, 101, 105]
}, index=pd.date_range('2024-01', periods=4, freq='ME'))

# Variacao mensal em %
df_mom = mom(df)
# Resultado: [NaN, 2.0, -0.98, 3.96]

# Via accessor
df.chartkit.mom().plot(title="Variacao Mensal")
```

---

### yoy() - Variacao Anual

Calcula variacao percentual ano contra ano (Year-over-Year).

```python
def yoy(df, periods: int = 12) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Dados com indice temporal |
| `periods` | int | 12 | Periodos para comparacao (12 para mensal) |

**Exemplo:**

```python
from chartkit import yoy

# Dados mensais (12 periodos = 1 ano)
df_yoy = yoy(df)

# Dados trimestrais (4 periodos = 1 ano)
df_yoy = yoy(df, periods=4)

# Via accessor
df.chartkit.yoy().plot(title="Variacao Anual")
df.chartkit.yoy(periods=4).plot()  # Trimestral
```

---

### accum_12m() - Acumulado 12 Meses

Calcula variacao acumulada em 12 meses usando produto composto.

**Formula:** `(Produto(1 + x/100) - 1) * 100`

```python
def accum_12m(df) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Variacoes mensais em % |

**Exemplo:**

```python
from chartkit import accum_12m

# IPCA mensal -> IPCA acumulado 12 meses
ipca_12m = accum_12m(ipca_mensal)

# Via accessor com plotagem
ipca_mensal.chartkit.accum_12m().plot(
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

Normaliza serie para um valor base em data especifica. Util para comparar series com escalas diferentes.

```python
def normalize(df, base: int = 100, base_date: str = None) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Dados com indice temporal |
| `base` | int | 100 | Valor base para normalizacao |
| `base_date` | str | None | Data base. Se None, usa primeira data |

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

Calcula retorno composto em janela movel. Multiplica os fatores (1 + taxa) ao longo da janela.

**Formula:** `Produto(1 + taxa/100) - 1`

```python
def compound_rolling(df, window: int = 12) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Taxas em % |
| `window` | int | 12 | Janela em periodos |

**Exemplo:**

```python
from chartkit import compound_rolling

# Selic mensal -> Selic acumulada 12 meses
selic_12m = compound_rolling(selic_mensal)

# Janela de 6 meses
selic_6m = compound_rolling(selic_mensal, window=6)

# Via accessor
selic_mensal.chartkit.compound_rolling(12).plot(
    title="Selic Acumulada 12 Meses",
    units='%'
)
```

---

### to_month_end() - Normalizar para Fim do Mes

Normaliza indice temporal para ultimo dia do mes. Util para alinhar series com frequencias diferentes antes de operacoes.

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
ipca_mensal.chartkit.accum_12m().plot(
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
from chartkit import to_month_end, compound_rolling, accum_12m

# Alinhar frequencias
selic = to_month_end(selic_mensal)
ipca = to_month_end(ipca_mensal)

# Calcular acumulados 12 meses
selic_12m = compound_rolling(selic)
ipca_12m = accum_12m(ipca)

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
