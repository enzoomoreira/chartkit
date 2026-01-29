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
| `real_rate()` | Juros real (Fisher) | Selic - IPCA |
| `to_month_end()` | Normaliza para fim do mes | Alinhar series |

## Import

```python
from agora_charting import (
    yoy, mom, accum_12m, diff, normalize,
    annualize_daily, compound_rolling, real_rate, to_month_end
)
```

---

## Transformacoes Basicas

### mom() - Variacao Mensal

Calcula variacao percentual mes contra mes.

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
from agora_charting import mom

df = pd.DataFrame({'valor': [100, 102, 101, 105]})
df_mom = mom(df)  # Variacao mensal em %
```

---

### yoy() - Variacao Anual

Calcula variacao percentual ano contra ano.

```python
def yoy(df, periods: int = 12) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Dados com indice temporal |
| `periods` | int | 12 | Periodos para comparacao (12 para mensal) |

**Exemplo:**

```python
from agora_charting import yoy

# Dados mensais (12 periodos = 1 ano)
df_yoy = yoy(df)

# Dados trimestrais (4 periodos = 1 ano)
df_yoy = yoy(df, periods=4)
```

---

### accum_12m() - Acumulado 12 Meses

Calcula variacao acumulada em 12 meses usando produto.

Formula: `(Produto(1 + x/100) - 1) * 100`

```python
def accum_12m(df) -> DataFrame | Series
```

**Exemplo:**

```python
from agora_charting import accum_12m

# IPCA mensal -> IPCA acumulado 12 meses
ipca_12m = accum_12m(ipca_mensal)
ipca_12m.agora.plot(title="IPCA 12m", units='%')
```

---

### diff() - Diferenca Absoluta

Calcula diferenca absoluta entre periodos.

```python
def diff(df, periods: int = 1) -> DataFrame | Series
```

**Exemplo:**

```python
from agora_charting import diff

# Variacao em pontos percentuais
df_diff = diff(selic)  # Diferenca para periodo anterior
```

---

### normalize() - Normalizacao

Normaliza serie para um valor base em data especifica.

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
from agora_charting import normalize

# Base 100 na primeira data
df_norm = normalize(df)

# Base 100 em data especifica
df_norm = normalize(df, base_date='2020-01-01')

# Comparar duas series com escalas diferentes
import pandas as pd

series_a = normalize(df['a'])
series_b = normalize(df['b'])
pd.concat([series_a, series_b], axis=1).agora.plot(title="Comparativo Base 100")
```

---

## Transformacoes de Juros

### annualize_daily() - Anualizar Taxa Diaria

Anualiza taxa diaria usando juros compostos.

Formula: `((1 + r_diaria) ^ dias_uteis - 1) * 100`

```python
def annualize_daily(df, trading_days: int = 252) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Taxas diarias em % |
| `trading_days` | int | 252 | Dias uteis no ano |

**Exemplo:**

```python
from agora_charting import annualize_daily

# CDI diario -> CDI anualizado
cdi_anual = annualize_daily(cdi_diario)
cdi_anual.agora.plot(title="CDI Anualizado", units='%')
```

---

### compound_rolling() - Retorno Composto

Calcula retorno composto em janela movel.

Formula: `Produto(1 + taxa) - 1`

```python
def compound_rolling(df, window: int = 12) -> DataFrame | Series
```

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `df` | DataFrame \| Series | - | Taxas em % |
| `window` | int | 12 | Janela em periodos |

**Exemplo:**

```python
from agora_charting import compound_rolling

# Selic mensal -> Selic acumulada 12 meses
selic_12m = compound_rolling(selic_mensal)
selic_12m.agora.plot(title="Selic 12m", units='%')
```

---

### real_rate() - Taxa Real (Equacao de Fisher)

Calcula taxa de juros real usando a Equacao de Fisher exata.

Formula: `((1 + nominal) / (1 + inflacao) - 1) * 100`

```python
def real_rate(nominal, inflation) -> DataFrame | Series
```

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `nominal` | DataFrame \| Series | Taxa nominal em % |
| `inflation` | DataFrame \| Series | Taxa de inflacao em % |

**Exemplo:**

```python
from agora_charting import compound_rolling, real_rate, to_month_end

# Calcula Selic acumulada 12 meses
selic_12m = compound_rolling(selic_mensal)

# Alinha indices para fim do mes
selic_12m = to_month_end(selic_12m)
ipca_12m = to_month_end(ipca_12m)

# Calcula juros real
juros_real = real_rate(selic_12m, ipca_12m)
juros_real.agora.plot(title="Juros Real (Selic - IPCA)", units='%')
```

---

### to_month_end() - Normalizar para Fim do Mes

Normaliza indice temporal para fim do mes.

```python
def to_month_end(df) -> DataFrame | Series
```

**Exemplo:**

```python
from agora_charting import to_month_end

# Alinhar series antes de operacoes
selic = to_month_end(selic)
ipca = to_month_end(ipca)

# Agora podem ser operadas juntas
spread = selic - ipca
```

---

## Casos de Uso Compostos

### Juros Real Completo

```python
import pandas as pd
from agora_charting import compound_rolling, real_rate, to_month_end

# Dados sinteticos
selic_mensal = pd.DataFrame({
    'selic': [0.87, 0.92, 0.95, 1.00, 1.05, 1.10,
              1.05, 1.00, 0.95, 0.90, 0.87, 0.85]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

ipca_mensal = pd.DataFrame({
    'ipca': [0.42, 0.55, 0.38, 0.45, 0.50, 0.48,
             0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

# Acumula 12 meses
selic_12m = compound_rolling(selic_mensal)
ipca_12m = compound_rolling(ipca_mensal)

# Calcula taxa real
juros_real = real_rate(selic_12m, ipca_12m)

# Plota
juros_real.agora.plot(title="Juros Real Ex-Post", units='%', source='BCB/IBGE')
```

### Comparacao Base 100

```python
import pandas as pd
from agora_charting import normalize

# Duas series com escalas diferentes
df = pd.DataFrame({
    'ibovespa': [100000, 105000, 102000, 110000],
    'sp500': [4000, 4200, 4100, 4400],
}, index=pd.date_range('2024-01', periods=4, freq='ME'))

# Normaliza para base 100
df_norm = normalize(df)

# Compara evolucao
df_norm.agora.plot(title="Ibovespa vs S&P500 (Base 100)")
```
