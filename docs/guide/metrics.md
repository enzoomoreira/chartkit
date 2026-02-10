# Metricas

Sistema declarativo de metricas para adicionar elementos visuais sobre os dados principais.

> **Nota:** Valores default como cores, espessuras e labels podem ser personalizados
> via arquivo TOML. Veja [Configuration](configuration.md).

---

## Resumo

| Metrica | Sintaxe | Descricao |
|---------|---------|-----------|
| Media Movel | `'ma:N'` | Linha de media movel de N periodos |
| ATH | `'ath'` | Linha no maximo historico (All-Time High) |
| ATL | `'atl'` | Linha no minimo historico (All-Time Low) |
| Media | `'avg'` | Linha horizontal na media (mean) dos dados |
| Linha Horizontal | `'hline:V'` | Linha horizontal no valor V |
| Banda | `'band:L:U'` | Area sombreada entre L e U |
| Meta | `'target:V'` | Linha horizontal de meta no valor V |
| Banda de Desvio Padrao | `'std_band:W:N'` | Banda de N desvios padrao com janela W |
| Banda Vertical | `'vband:D1:D2'` | Area sombreada entre duas datas |

---

## Uso Basico

Metricas sao passadas como string ou lista de strings no parametro `metrics`:

```python
# Uma metrica (string unica)
df.chartkit.plot(metrics='ath')

# Multiplas metricas (lista)
df.chartkit.plot(metrics=['ath', 'atl', 'ma:12'])

# Combinacao completa
df.chartkit.plot(metrics=['ath', 'ma:12', 'hline:3.0', 'band:1.5:4.5'])
```

O sistema de metricas utiliza um registry centralizado que parseia as strings
de especificacao e aplica as funcoes correspondentes ao grafico.

---

## Media Movel (ma:N)

Adiciona linha de media movel sobre os dados usando a sintaxe `'ma:N'`, onde N
e o numero de periodos.

```python
df.chartkit.plot(title="Dados com MM12", metrics=['ma:12'])
```

### Sintaxe

- `'ma:3'` - Media movel de 3 periodos
- `'ma:12'` - Media movel de 12 periodos
- `'ma:24'` - Media movel de 24 periodos

### Caracteristicas Visuais

| Propriedade | Valor | Configuracao TOML |
|-------------|-------|-------------------|
| Cor | Cinza (#888888) | `colors.moving_average` |
| Estilo | Linha solida | - |
| Espessura | 1.5 | `lines.overlay_width` |
| Label | "MM{window}" | `labels.moving_average_format` |
| zorder | 2 | Acima de referencias, abaixo dos dados |

### Exemplo

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'valor': [10, 12, 11, 14, 13, 15, 14, 16, 15, 18, 17, 19]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

df.chartkit.plot(
    title="Serie com Media Movel",
    metrics=['ma:3'],
    units='%'
)
```

---

## ATH e ATL

Linhas horizontais tracejadas nos extremos historicos da serie.

### ATH (All-Time High)

Linha no maximo historico dos dados.

```python
df.chartkit.plot(title="Grafico", metrics=['ath'])
```

| Propriedade | Valor | Configuracao TOML |
|-------------|-------|-------------------|
| Cor | Verde | `colors.positive` |
| Label | "ATH" | `labels.ath` |
| Estilo | Tracejado (--) | `lines.reference_style` |
| zorder | 1 | Nivel de linhas de referencia |

### ATL (All-Time Low)

Linha no minimo historico dos dados.

```python
df.chartkit.plot(title="Grafico", metrics=['atl'])
```

| Propriedade | Valor | Configuracao TOML |
|-------------|-------|-------------------|
| Cor | Vermelho | `colors.negative` |
| Label | "ATL" | `labels.atl` |
| Estilo | Tracejado (--) | `lines.reference_style` |
| zorder | 1 | Nivel de linhas de referencia |

### Ambos

```python
df.chartkit.plot(title="Extremos Historicos", metrics=['ath', 'atl'])
```

### Exemplo

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'ipca': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8, 3.5, 4.0, 5.5, 4.0]
}, index=pd.date_range('2024-01', periods=10, freq='ME'))

df.chartkit.plot(
    title="IPCA com Extremos",
    units='%',
    metrics=['ath', 'atl']
)
```

---

## Media (avg)

Linha horizontal na media (mean) dos dados. Usa a cor `colors.grid` e estilo tracejado.

```python
df.chartkit.plot(title="Grafico com Media", metrics=['avg'])
```

| Propriedade | Valor | Configuracao TOML |
|-------------|-------|-------------------|
| Cor | Grid (lightgray) | `colors.grid` |
| Label | "AVG" | `labels.avg` |
| Estilo | Tracejado (--) | `lines.reference_style` |
| zorder | 1 | Nivel de linhas de referencia |

### Exemplo

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'ipca': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8, 3.5, 4.0, 5.5, 4.0]
}, index=pd.date_range('2024-01', periods=10, freq='ME'))

df.chartkit.plot(
    title="IPCA com Media",
    units='%',
    metrics=['avg', 'ath', 'atl']
)
```

---

## Linhas Horizontais (hline:V)

Use a sintaxe `'hline:V'` para adicionar linhas de referencia em valores
arbitrarios, onde V e o valor no eixo Y.

```python
# Linha simples
df.chartkit.plot(metrics=['hline:3.0'])

# Multiplas linhas
df.chartkit.plot(metrics=['hline:3.0', 'hline:4.5', 'hline:1.5'])
```

### Sintaxe

- `'hline:3.0'` - Linha horizontal em y=3.0
- `'hline:100'` - Linha horizontal em y=100
- `'hline:-5.5'` - Linha horizontal em y=-5.5 (valores negativos suportados)

### Exemplo: Meta de Inflacao

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'ipca': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Linha central da meta (3.0%) e limites de tolerancia (1.5% e 4.5%)
df.chartkit.plot(
    title="IPCA vs Meta",
    units='%',
    metrics=['hline:3.0', 'hline:4.5', 'hline:1.5']
)
```

---

## Bandas Sombreadas (band:L:U)

Use a sintaxe `'band:L:U'` para adicionar areas sombreadas entre dois valores,
onde L e o limite inferior e U e o limite superior.

```python
df.chartkit.plot(metrics=['band:1.5:4.5'])
```

### Sintaxe

- `'band:1.5:4.5'` - Banda entre 1.5 e 4.5
- `'band:0:100'` - Banda entre 0 e 100
- `'band:-10:10'` - Banda entre -10 e 10

### Caracteristicas Visuais

| Propriedade | Valor |
|-------------|-------|
| Estilo | Area preenchida semi-transparente |
| zorder | 0 | Mais ao fundo, atras de todos os outros elementos |

### Exemplo: Banda de Tolerancia

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'ipca': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Banda representando intervalo de tolerancia da meta de inflacao
df.chartkit.plot(
    title="IPCA com Banda de Meta",
    units='%',
    metrics=['band:1.5:4.5']
)
```

---

## Linha de Meta (target:V)

Use a sintaxe `'target:V'` para adicionar uma linha horizontal de meta com estilo diferenciado
(cor secondary, dash-dot). O label e gerado automaticamente com o valor formatado.

```python
# Meta simples
df.chartkit.plot(metrics=['target:1000'])

# Meta com formatacao de moeda
df.chartkit.plot(units='BRL', metrics=['target:1000'])
# Label: "Meta: R$ 1.000,00"
```

### Sintaxe

- `'target:1000'` - Linha de meta em 1000
- `'target:3.0'` - Linha de meta em 3.0

### Caracteristicas Visuais

| Propriedade | Valor | Configuracao TOML |
|-------------|-------|-------------------|
| Cor | Secondary | `colors.secondary` |
| Estilo | Dash-dot (-.) | `lines.target_style` |
| Espessura | 1.5 | `lines.overlay_width` |
| Label | "Meta: {value}" | `labels.target_format` |
| zorder | 1 | Nivel de linhas de referencia |

A linha de meta usa cor `secondary` e estilo dash-dot (`-.`) por default, distinguindo-se
visualmente das linhas de referencia padrao (ATH, ATL, hline) que usam tracejado.

---

## Banda de Desvio Padrao (std_band:W:N)

Use a sintaxe `'std_band:W:N'` para adicionar uma banda de desvio padrao (Bollinger Band)
com media movel central. W e a janela da media movel e N e o numero de desvios padrao.

```python
# Bollinger Band: janela 20, 2 desvios padrao
df.chartkit.plot(metrics=['std_band:20:2'])
```

### Sintaxe

- `'std_band:20:2'` - Janela 20 periodos, 2 desvios padrao
- `'std_band:12:1.5'` - Janela 12 periodos, 1.5 desvios padrao

### Caracteristicas Visuais

| Propriedade | Valor | Configuracao TOML |
|-------------|-------|-------------------|
| Cor da banda | Grid (lightgray) | `colors.grid` |
| Estilo da linha central | Tracejado (--) | `lines.reference_style` |
| Espessura | 1.5 | `lines.overlay_width` |
| Label | "BB({window}, {num_std})" | `labels.std_band_format` |

### Exemplo

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'preco': [100, 102, 98, 105, 103, 107, 101, 108, 106, 110]
}, index=pd.date_range('2024-01', periods=10, freq='ME'))

# Bollinger Band com media movel de 5 periodos e 2 desvios padrao
df.chartkit.plot(
    title="Preco com Bollinger Band",
    metrics=['std_band:5:2']
)
```

---

## Banda Vertical (vband:D1:D2)

Use a sintaxe `'vband:D1:D2'` para adicionar uma area sombreada vertical entre duas datas.
Ideal para destacar periodos especificos como recessoes, crises ou eventos.

```python
# Sombreia periodo entre duas datas
df.chartkit.plot(metrics=['vband:2020-03-01:2020-06-30'])
```

### Sintaxe

- `'vband:2020-03-01:2020-06-30'` - Banda vertical entre marco e junho de 2020
- `'vband:2008-09-01:2009-06-30'` - Banda vertical para a crise financeira

### Exemplo

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'pib': [100, 102, 104, 95, 88, 92, 98, 105, 108, 110]
}, index=pd.date_range('2019-07', periods=10, freq='QE'))

# Destaca periodo de recessao
df.chartkit.plot(
    title="PIB com Periodo de Crise",
    metrics=['vband:2020-01-01:2020-09-30']
)
```

---

## Combinando Metricas

Todas as metricas podem ser combinadas livremente em uma unica lista.
O sistema aplica cada metrica na ordem especificada, respeitando a hierarquia
de zorder para sobreposicao visual.

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'valor': [10, 12, 11, 14, 13, 15, 14, 16, 15, 18, 17, 19]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

df.chartkit.plot(
    title="Analise Completa",
    units='%',
    metrics=[
        'ath',          # Maximo historico
        'atl',          # Minimo historico
        'ma:3',         # Media movel 3 periodos
        'hline:15',     # Linha de referencia
        'band:12:18'    # Banda sombreada
    ]
)
```

### Exemplo: Analise de Inflacao

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'ipca': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8, 3.5, 4.0, 5.5, 4.0, 3.8, 4.2]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

df.chartkit.plot(
    title="IPCA - Analise Completa",
    units='%',
    metrics=[
        'band:1.5:4.5',  # Banda de tolerancia da meta
        'hline:3.0',     # Centro da meta
        'ma:3',          # Tendencia de curto prazo
        'ath',           # Pico historico
        'atl'            # Vale historico
    ]
)
```

---

## Ordem de Renderizacao (zorder)

O sistema de metricas utiliza zorder para controlar a sobreposicao visual
dos elementos. Elementos com zorder menor sao renderizados primeiro (mais
ao fundo), enquanto elementos com zorder maior ficam mais a frente.

| Elemento | zorder | Posicao |
|----------|--------|---------|
| Banda (`band`) | 0 | Mais ao fundo |
| ATH/ATL/hlines | 1 | Linhas de referencia |
| Media movel (`ma`) | 2 | Intermediario |
| Dados principais | 3+ | Mais a frente |

Esta hierarquia garante que:

1. Bandas sombreadas nao obscurecem outros elementos
2. Linhas de referencia (ATH, ATL, hlines) ficam visiveis mas nao interferem nos dados
3. Media movel acompanha os dados mas nao os sobrepoe
4. Dados principais sempre ficam visiveis no topo

---

## Sintaxe @ (Direcionar para Coluna)

Para DataFrames com multiplas colunas, use a sintaxe `@` para direcionar uma
metrica a uma coluna especifica:

```python
df = pd.DataFrame({
    'revenue': [100, 120, 110, 140],
    'costs': [80, 90, 85, 95],
}, index=pd.date_range('2024-01', periods=4, freq='ME'))

# ATH apenas na coluna revenue
df.chartkit.plot(metrics=['ath@revenue'])

# Media movel na coluna costs
df.chartkit.plot(metrics=['ma:12@costs'])

# Combinacao
df.chartkit.plot(metrics=['ath@revenue', 'atl@costs', 'ma:6@revenue'])
```

### Sintaxe

- `'metrica@coluna'` - Aplica metrica apenas na coluna especificada
- `'metrica:param@coluna'` - Com parametros: `'ma:12@revenue'`
- Sem `@`: metrica usa a primeira coluna (ou a unica coluna para Series)

### Metricas Data-Independent

Metricas que nao dependem dos dados (`hline`, `band`) ignoram o `@`
automaticamente, pois sao registradas com `uses_series=False`.

```python
# hline ignora @coluna silenciosamente
df.chartkit.plot(metrics=['hline:3.0', 'ath@revenue'])
```

---

## Labels Customizados (sintaxe |)

Por padrao, cada metrica usa um label pre-definido (ex: "ATH", "MM12"). Para customizar
o nome exibido na legenda, use a sintaxe `|` ao final da especificacao:

```python
# Label customizado simples
df.chartkit.plot(metrics=['ath|Maximo Historico'])

# Com parametros
df.chartkit.plot(metrics=['ma:12|Media 12 Meses'])

# Combinando com @coluna
df.chartkit.plot(metrics=['ma:12@revenue|Media 12M'])

# Com caracteres especiais no label
df.chartkit.plot(metrics=['hline:100|Meta: Q1'])
```

### Sintaxe

- `'metrica|label'` - Label customizado simples
- `'metrica:param|label'` - Com parametros
- `'metrica:param@coluna|label'` - Com parametros e coluna
- Sem `|`: usa o label default da metrica

O `|` e extraido antes do `@` e `:`, permitindo caracteres especiais no label.

---

## Veja Tambem

- [Configuration](configuration.md) - Personalizacao de cores, labels e estilos de metricas
