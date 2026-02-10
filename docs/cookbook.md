# Cookbook

Receitas praticas e casos de uso reais para dados financeiros brasileiros.

---

## IPCA Acumulado 12 Meses

**Caso de uso:** Visualizar a inflacao acumulada em janela movel de 12 meses, com banda indicando a meta de inflacao e sua tolerancia.

```python
import pandas as pd
import chartkit

# Dados de IPCA mensal (variacao % no mes)
ipca_mensal = pd.DataFrame({
    'ipca': [0.42, 0.83, 0.16, 0.61, 0.44, 0.26,
             0.12, -0.02, 0.26, 0.24, 0.28, 0.56,
             0.42, 0.83, 0.71, 0.38, 0.46, 0.21]
}, index=pd.date_range('2023-01', periods=18, freq='ME'))

# Transforma IPCA mensal em acumulado 12 meses
# A funcao accum aplica a formula: (Produto(1 + x/100) - 1) * 100
ipca_12m = ipca_mensal.chartkit.accum()

# Plota com banda de meta (3% centro, tolerancia de 1.5 p.p.)
ipca_12m.plot(
    title="IPCA Acumulado 12 Meses",
    units='%',
    source='IBGE',
    metrics=[
        'hline:3.0',      # Meta central
        'band:1.5:4.5'    # Banda de tolerancia (+/- 1.5 p.p.)
    ]
).save('ipca_12m.png')
```

---

## Selic vs IPCA (Juro Real)

**Caso de uso:** Comparar a evolucao da taxa Selic e do IPCA acumulado para visualizar o juro real implicito.

```python
import pandas as pd
import chartkit
from chartkit import to_month_end

# Dados de Selic (meta % a.a.) e IPCA 12m (% a.a.)
dados = pd.DataFrame({
    'selic': [13.75, 13.75, 13.75, 13.25, 12.75, 12.25,
              11.75, 11.25, 10.75, 10.50, 10.50, 10.50],
    'ipca_12m': [5.77, 5.60, 4.65, 4.18, 3.94, 3.16,
                 3.99, 4.24, 4.42, 4.50, 4.62, 4.51]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

# Normaliza indices para fim do mes (garante alinhamento)
dados = to_month_end(dados)

# Plota as duas series no mesmo grafico
dados.chartkit.plot(
    title="Selic vs IPCA 12m",
    units='%',
    source='BCB/IBGE',
    highlight=True
).save('selic_vs_ipca.png')

# Opcional: calcular e plotar o juro real
# Juro real = ((1 + selic/100) / (1 + ipca/100) - 1) * 100
dados['juro_real'] = ((1 + dados['selic']/100) / (1 + dados['ipca_12m']/100) - 1) * 100

dados[['juro_real']].chartkit.plot(
    title="Juro Real Ex-Post",
    units='%',
    source='BCB/IBGE',
    metrics=['hline:0']  # Linha em zero para referencia
).save('juro_real.png')
```

---

## Comparativo Base 100

**Caso de uso:** Comparar a evolucao de ativos com escalas muito diferentes (ex: Ibovespa em milhares vs S&P 500 em milhares, mas valores absolutos distintos).

```python
import pandas as pd
import chartkit
from chartkit import normalize

# Dados de Ibovespa e S&P 500 com escalas diferentes
indices = pd.DataFrame({
    'ibovespa': [127500, 128900, 126100, 131200, 129800, 134500,
                 132100, 135800, 133200, 138900, 136500, 140200],
    'sp500': [4770, 4845, 4769, 4958, 4890, 5026,
              4967, 5137, 5078, 5234, 5186, 5321]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

# Normaliza ambas as series para base 100 na primeira data
# Isso permite comparar a variacao percentual relativa
indices_norm = normalize(indices, base=100)

# Plota comparativo
indices_norm.chartkit.plot(
    title="Ibovespa vs S&P 500 (Base 100)",
    units='points',
    source='B3/NYSE',
    highlight=True
).save('indices_base100.png')

# Alternativa: normalizar a partir de uma data especifica
indices_norm_2024 = normalize(indices, base=100, base_date='2024-06-30')

indices_norm_2024.chartkit.plot(
    title="Ibovespa vs S&P 500 (Base 100 em Jun/24)",
    units='points',
    source='B3/NYSE'
).save('indices_base100_jun.png')
```

---

## CDI Anualizado

**Caso de uso:** Converter a taxa CDI diaria (expressa em % ao dia) para taxa anualizada equivalente.

```python
import pandas as pd
import chartkit
from chartkit import annualize_daily

# Dados de CDI diario (taxa % ao dia)
# Nota: valores tipicos de CDI diario sao muito pequenos (~0.04% ao dia)
cdi_diario = pd.DataFrame({
    'cdi': [0.0407, 0.0407, 0.0403, 0.0399, 0.0395,
            0.0391, 0.0387, 0.0383, 0.0379, 0.0375,
            0.0371, 0.0367, 0.0363, 0.0359, 0.0355]
}, index=pd.date_range('2024-06-01', periods=15, freq='B'))  # B = business days

# Anualiza usando a formula de juros compostos
# Formula: ((1 + taxa_diaria/100) ^ 252 - 1) * 100
cdi_anual = annualize_daily(cdi_diario, trading_days=252)

# Plota CDI anualizado
cdi_anual.chartkit.plot(
    title="CDI Anualizado",
    units='%',
    source='CETIP',
    highlight=True,
    metrics=['ath', 'atl']  # Mostra maximo e minimo do periodo
).save('cdi_anualizado.png')
```

---

## Variacao YoY com Extremos

**Caso de uso:** Calcular variacao ano contra ano e destacar os valores extremos (ATH/ATL) para identificar picos e vales historicos.

```python
import pandas as pd
import chartkit
from chartkit import yoy

# Dados de producao industrial (indice, base 100)
producao = pd.DataFrame({
    'producao': [98.5, 99.2, 100.1, 101.3, 100.8, 102.5,
                 103.2, 102.1, 104.5, 105.2, 103.8, 106.1,
                 104.2, 105.8, 107.2, 108.5, 106.9, 109.3,
                 110.1, 108.5, 111.2, 112.5, 110.8, 114.2]
}, index=pd.date_range('2022-01', periods=24, freq='ME'))

# Calcula variacao ano contra ano (12 periodos para dados mensais)
producao_yoy = yoy(producao, periods=12)

# Plota com extremos historicos destacados
producao_yoy.chartkit.plot(
    title="Producao Industrial - Variacao YoY",
    units='%',
    source='IBGE',
    metrics=['ath', 'atl'],  # All-Time High e All-Time Low
    highlight=True
).save('producao_yoy.png')

# Para dados trimestrais, usar periods=4
pib_trimestral = pd.DataFrame({
    'pib': [2.1, 2.3, 2.5, 2.8, 2.2, 2.4, 2.6, 2.9]
}, index=pd.date_range('2022-03', periods=8, freq='QE'))

pib_yoy = yoy(pib_trimestral, periods=4)

pib_yoy.chartkit.plot(
    title="PIB - Variacao YoY",
    units='%',
    source='IBGE',
    metrics=['ath', 'atl']
).save('pib_yoy.png')
```

---

## Serie com Media Movel

**Caso de uso:** Suavizar uma serie volatil com media movel para identificar tendencias.

```python
import pandas as pd
import chartkit

# Dados de vendas no varejo (indice dessazonalizado)
varejo = pd.DataFrame({
    'vendas': [102.5, 98.3, 105.2, 101.8, 99.5, 103.2,
               100.1, 97.8, 104.5, 102.2, 98.9, 106.1,
               103.5, 99.2, 107.8, 104.1, 100.5, 108.5,
               105.2, 101.8, 110.2, 106.5, 102.9, 112.1]
}, index=pd.date_range('2022-01', periods=24, freq='ME'))

# Plota com media movel de 12 periodos
varejo.chartkit.plot(
    title="Vendas no Varejo com Media Movel",
    units='points',
    source='IBGE',
    metrics=['ma:12'],  # Media movel de 12 meses
    highlight=True
).save('varejo_mm12.png')

# Combinando media movel com ATH/ATL
varejo.chartkit.plot(
    title="Vendas no Varejo - Analise Completa",
    units='points',
    source='IBGE',
    metrics=[
        'ma:3',   # MM3 para tendencia de curto prazo
        'ma:12',  # MM12 para tendencia de longo prazo
        'ath',    # Maximo historico
        'atl'     # Minimo historico
    ]
).save('varejo_completo.png')
```

---

## Meta de Inflacao

**Caso de uso:** Visualizar a inflacao em relacao a meta do Banco Central, incluindo a banda de tolerancia.

```python
import pandas as pd
import chartkit

# Dados de IPCA acumulado 12 meses
ipca_12m = pd.DataFrame({
    'ipca': [5.77, 5.60, 4.65, 4.18, 3.94, 3.16,
             3.99, 4.24, 4.42, 4.50, 4.62, 4.51,
             4.56, 4.83, 5.19, 5.26, 5.35, 5.52]
}, index=pd.date_range('2024-01', periods=18, freq='ME'))

# Plota com meta e banda de tolerancia
# Meta de inflacao 2024-2025: 3.0% com tolerancia de +/- 1.5 p.p.
ipca_12m.chartkit.plot(
    title="IPCA 12m vs Meta de Inflacao",
    units='%',
    source='IBGE',
    highlight=True,
    metrics=[
        'hline:3.0',      # Meta central (linha pontilhada)
        'band:1.5:4.5',   # Banda de tolerancia (area sombreada)
        'hline:4.5',      # Teto da meta
        'hline:1.5'       # Piso da meta
    ]
).save('ipca_meta.png')

# Versao simplificada apenas com banda
ipca_12m.chartkit.plot(
    title="IPCA 12m - Regime de Metas",
    units='%',
    source='IBGE',
    metrics=[
        'hline:3.0',      # Meta central
        'band:1.5:4.5'    # Banda de tolerancia
    ]
).save('ipca_meta_simples.png')
```

---

## Combinando Multiplas Tecnicas

**Caso de uso:** Analise completa de uma serie temporal combinando transformacoes e overlays.

```python
import pandas as pd
import chartkit
from chartkit import accum, normalize

# Dados de IPCA mensal
ipca_mensal = pd.DataFrame({
    'ipca': [0.42, 0.83, 0.16, 0.61, 0.44, 0.26,
             0.12, -0.02, 0.26, 0.24, 0.28, 0.56,
             0.42, 0.83, 0.71, 0.38, 0.46, 0.21,
             0.35, 0.44, 0.52, 0.39, 0.41, 0.67]
}, index=pd.date_range('2023-01', periods=24, freq='ME'))

# Pipeline completo: IPCA mensal -> acumulado 12m -> plot com metricas
(ipca_mensal
    .chartkit
    .accum()  # Transforma em acumulado 12 meses
    .plot(
        title="IPCA Acumulado 12m - Analise Completa",
        units='%',
        source='IBGE',
        highlight=True,
        metrics=[
            'ma:6',           # Media movel 6 meses
            'ath',            # Maximo historico
            'atl',            # Minimo historico
            'hline:3.0',      # Meta de inflacao
            'band:1.5:4.5'    # Banda de tolerancia
        ]
    )
    .save('ipca_analise_completa.png')
)
```

---

## Dicas e Boas Praticas

### Alinhamento de Series

Sempre normalize datas para fim do mes antes de combinar series de fontes diferentes:

```python
from chartkit import to_month_end

selic = to_month_end(selic_raw)
ipca = to_month_end(ipca_raw)
combined = pd.concat([selic, ipca], axis=1)
```

### Escolha de Metricas

| Situacao | Metricas Recomendadas |
|----------|----------------------|
| Inflacao vs Meta | `hline:meta`, `band:piso:teto` |
| Volatilidade | `ma:12`, `ath`, `atl` |
| Tendencia | `ma:3`, `ma:12` |
| Valores extremos | `ath`, `atl` |
| Referencia zero | `hline:0` |

### Salvando com Qualidade

```python
# Para apresentacoes (maior DPI)
df.chartkit.plot(title="Chart").save('chart.png', dpi=300)

# Para web (menor tamanho)
df.chartkit.plot(title="Chart").save('chart.png', dpi=100)
```
