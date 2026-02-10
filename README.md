# chartkit

Biblioteca de charting padronizado para visualizacao de dados financeiros.

Gera graficos profissionais via Pandas Accessor com uma linha de codigo.

## Instalacao

```bash
uv add chartkit
```

## Quick Start

```python
import pandas as pd
import chartkit  # Registra o accessor .chartkit

# Dados de exemplo
df = pd.DataFrame({
    'taxa': [10.5, 11.2, 10.8, 12.1, 11.9, 13.0]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Grafico de linha
df.chartkit.plot(title="Taxa de Juros", units='%', source='BCB')

# Grafico de barras
df.chartkit.variation().plot(kind='bar', title="Variacao Mensal", units='%', highlight=['last'])

# Grafico com metricas (ATH, media movel, etc)
df.chartkit.plot(title="Análise", metrics=['ath|Máxima', 'atl|Mínima', 'ma:12|Média Móvel'])

# Encadeamento completo
df.chartkit.variation().plot(title="Variacao Mensal").show()
```

## Funcionalidades

- **Pandas Accessor**: Use `df.chartkit.plot()` diretamente em qualquer DataFrame
- **Graficos**: Linhas, barras e barras empilhadas com estilo profissional
- **Formatadores**: BRL, USD, BRL_compact, USD_compact, %, pontos, notacao humana (1k, 1M)
- **Metricas Declarativas**: `metrics=['ath', 'atl', 'ma:12', 'hline:3.0', 'band:1.5:4.5', 'target:1000', 'std_band:20:2', 'vband:2020-03:2020-06']`
- **Transforms Encadeados**: `df.chartkit.variation(horizon='year').drawdown().plot()` com method chaining e auto-deteccao de frequencia
- **Overlays**: Area entre series (`fill_between`), bandas de desvio padrao, bandas verticais
- **ChartRegistry**: Sistema plugavel de chart types via decorator
- **Configuracao TOML + Env Vars**: Personalize via arquivo TOML ou variaveis de ambiente (`CHARTKIT_*`)

## Documentacao

### Primeiros Passos

- [Getting Started](docs/getting-started.md) - Primeiro grafico em 2 minutos
- [Cookbook](docs/cookbook.md) - Receitas praticas para dados financeiros

### Guias

| Guia | Descricao |
|------|-----------|
| [Plotting](docs/guide/plotting.md) | Tipos de grafico, formatacao e PlotResult |
| [Metrics](docs/guide/metrics.md) | Sistema declarativo de metricas |
| [Transforms](docs/guide/transforms.md) | Transformacoes temporais e encadeamento |
| [Configuration](docs/guide/configuration.md) | TOML, paths e auto-discovery |

### Referencia

- [API Reference](docs/reference/api.md) - Assinaturas, tipos e parametros

### Para Contribuidores

| Documento | Descricao |
|-----------|-----------|
| [Architecture](docs/contributing/architecture.md) | Visao geral e fluxo de dados |
| [Extending](docs/contributing/extending.md) | MetricRegistry e extensibilidade |
| [Internals](docs/contributing/internals.md) | Thread-safety, caching e logging |

## Requisitos

- Python >= 3.12
- pandas >= 2.2.0
- matplotlib >= 3.10.0
- numpy >= 2.0.0
- pydantic-settings >= 2.12.0
