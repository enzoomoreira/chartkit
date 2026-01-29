# Overlays

Elementos visuais secundarios que podem ser adicionados sobre os dados principais.

## Resumo

| Overlay | Parametro | Descricao |
|---------|-----------|-----------|
| Media Movel | `moving_avg=12` | Linha de media movel |
| ATH | `show_ath=True` | Linha no maximo historico |
| ATL | `show_atl=True` | Linha no minimo historico |
| Linhas | `overlays['hlines']` | Linhas horizontais customizadas |
| Bandas | `overlays['band']` | Area sombreada entre valores |

---

## Media Movel

Adiciona linha de media movel sobre os dados.

```python
df.agora.plot(title="Dados com MM12", moving_avg=12)
```

### Caracteristicas

- Cor: Cinza (#888888) por padrao
- Estilo: Linha solida
- Label: "MM{window}" (ex: MM12)
- zorder: 2 (acima de linhas de referencia, abaixo dos dados)

### Exemplo

```python
import pandas as pd
import agora_charting

df = pd.DataFrame({
    'valor': [10, 12, 11, 14, 13, 15, 14, 16, 15, 18, 17, 19]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

df.agora.plot(
    title="Serie com Media Movel",
    moving_avg=3,  # MM3
    units='%'
)
```

---

## Linhas ATH/ATL

Linhas horizontais no maximo (All-Time High) e minimo (All-Time Low) historico.

### ATH (All-Time High)

```python
df.agora.plot(title="Grafico", show_ath=True)
```

- Cor: Verde (theme.colors.positive)
- Label: "ATH"

### ATL (All-Time Low)

```python
df.agora.plot(title="Grafico", show_atl=True)
```

- Cor: Vermelho (theme.colors.negative)
- Label: "ATL"

### Ambos

```python
df.agora.plot(title="Extremos Historicos", show_ath=True, show_atl=True)
```

### Exemplo

```python
import pandas as pd
import agora_charting

df = pd.DataFrame({
    'ipca': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8, 3.5, 4.0, 5.5, 4.0]
}, index=pd.date_range('2024-01', periods=10, freq='ME'))

df.agora.plot(
    title="IPCA com Extremos",
    units='%',
    show_ath=True,
    show_atl=True
)
```

---

## Linhas Horizontais Customizadas

Use `overlays['hlines']` para adicionar linhas de referencia em valores arbitrarios.

### Estrutura

```python
overlays={
    'hlines': [
        {'value': 3.0, 'label': 'Meta', 'color': 'green'},
        {'value': 4.5, 'label': 'Teto', 'color': 'orange', 'linestyle': ':'},
    ]
}
```

### Parametros de Cada Linha

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `value` | float | - | Valor Y da linha (obrigatorio) |
| `label` | str | None | Rotulo para legenda |
| `color` | str | cinza | Cor da linha |
| `linestyle` | str | '--' | Estilo: '-', '--', ':', '-.' |
| `linewidth` | float | 1.5 | Espessura |

### Exemplo: Meta de Inflacao

```python
import pandas as pd
import agora_charting

df = pd.DataFrame({
    'ipca': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.agora.plot(
    title="IPCA vs Meta",
    units='%',
    overlays={
        'hlines': [
            {'value': 3.0, 'label': 'Meta', 'color': 'green'},
            {'value': 4.5, 'label': 'Teto', 'color': 'orange', 'linestyle': ':'},
            {'value': 1.5, 'label': 'Piso', 'color': 'orange', 'linestyle': ':'},
        ]
    }
)
```

---

## Bandas Sombreadas

Use `overlays['band']` para adicionar areas sombreadas entre dois valores.

### Estrutura

```python
overlays={
    'band': {
        'lower': 1.5,
        'upper': 4.5,
        'color': 'green',
        'alpha': 0.1,
        'label': 'Meta'
    }
}
```

### Parametros

| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| `lower` | float | - | Limite inferior (obrigatorio) |
| `upper` | float | - | Limite superior (obrigatorio) |
| `color` | str | cinza | Cor da banda |
| `alpha` | float | 0.15 | Transparencia (0-1) |
| `label` | str | None | Rotulo para legenda |

### Exemplo: Banda de Tolerancia

```python
import pandas as pd
import agora_charting

df = pd.DataFrame({
    'ipca': [4.2, 5.5, 3.8, 4.5, 6.0, 4.8]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.agora.plot(
    title="IPCA com Banda de Meta",
    units='%',
    overlays={
        'band': {
            'lower': 1.5,
            'upper': 4.5,
            'color': 'green',
            'alpha': 0.1,
            'label': 'Intervalo de Meta'
        }
    }
)
```

---

## Combinando Overlays

Todos os tipos podem ser usados juntos.

```python
import pandas as pd
import agora_charting

df = pd.DataFrame({
    'valor': [10, 12, 11, 14, 13, 15, 14, 16, 15, 18, 17, 19]
}, index=pd.date_range('2024-01', periods=12, freq='ME'))

df.agora.plot(
    title="Analise Completa",
    units='%',
    # Media movel
    moving_avg=3,
    # Extremos historicos
    show_ath=True,
    show_atl=True,
    # Overlays customizados
    overlays={
        'hlines': [
            {'value': 15, 'label': 'Referencia', 'color': 'blue', 'linestyle': ':'}
        ],
        'band': {
            'lower': 12,
            'upper': 18,
            'alpha': 0.1
        }
    }
)
```

---

## Ordem de Renderizacao (zorder)

| Elemento | zorder | Descricao |
|----------|--------|-----------|
| Banda | 0 | Mais ao fundo |
| ATH/ATL/hlines | 1 | Linhas de referencia |
| Media movel | 2 | Intermediario |
| Dados principais | 3+ | Mais a frente |
