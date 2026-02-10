# Getting Started

Seu primeiro grafico em 2 minutos.

## Pre-requisitos

- Python >= 3.12
- pandas >= 2.2.0

## Instalacao

```bash
uv add chartkit
```

## Primeiro Grafico

```python
import pandas as pd
import chartkit  # Registra o accessor .chartkit

# Dados de exemplo
df = pd.DataFrame({
    'valor': [10.5, 11.2, 10.8, 12.1, 11.9, 13.0]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Grafico basico
df.chartkit.plot(title="Meu Primeiro Grafico")
```

O import do `chartkit` registra automaticamente o accessor `.chartkit` em todos os DataFrames e Series.

```python
# Funciona tanto com DataFrame quanto com Series
df.chartkit.plot(title="DataFrame")
df["valor"].chartkit.plot(title="Series")
```

### Adicionando Formatacao

```python
# Com unidade de medida e fonte
df.chartkit.plot(
    title="Taxa de Juros",
    units='%',
    source='BCB'
)
```

### Salvando o Grafico

```python
# Salvar e mostrar
df.chartkit.plot(title="Grafico").save("grafico.png").show()

# Apenas salvar
df.chartkit.plot(title="Grafico").save("grafico.png")
```

### Usando Transforms

```python
# Calcular variacao ano-a-ano e plotar
df.chartkit.yoy().plot(title="Variacao YoY", units='%')

# Encadeamento multiplo
df.chartkit.annualize_daily().plot(metrics=['ath']).save('chart.png')
```

### Adicionando Metricas

```python
# Maximo historico e media movel
df.chartkit.plot(metrics=['ath', 'ma:12'])

# Banda de meta
df.chartkit.plot(metrics=['band:1.5:4.5', 'hline:3.0'])
```

## Proximos Passos

- [Plotting](guide/plotting.md) - Tipos de grafico e opcoes de formatacao
- [Metrics](guide/metrics.md) - Sistema de metricas declarativas
- [Transforms](guide/transforms.md) - Funcoes de transformacao temporal
- [Configuration](guide/configuration.md) - Personalizacao via TOML
