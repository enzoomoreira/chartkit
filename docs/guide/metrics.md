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
| Linha Horizontal | `'hline:V'` | Linha horizontal no valor V |
| Banda | `'band:L:U'` | Area sombreada entre L e U |

---

## Uso Basico

Todas as metricas sao passadas como lista de strings no parametro `metrics`:

```python
# Uma metrica
df.chartkit.plot(metrics=['ath'])

# Multiplas metricas
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

## Veja Tambem

- [Configuration](configuration.md) - Personalizacao de cores, labels e estilos de metricas
