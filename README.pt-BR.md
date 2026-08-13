# chartkit

Biblioteca de charting padronizado para visualização de dados financeiros.

Gere gráficos profissionais via Pandas Accessor com uma linha de código.

> Read this in [English](README.md).

## Instalação

```bash
uv add chartkit
```

## Início rápido

```python
import pandas as pd
import chartkit  # Registra o accessor .chartkit

# Dados de exemplo
df = pd.DataFrame({
    'taxa': [10.5, 11.2, 10.8, 12.1, 11.9, 13.0]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Gráfico de linha
df.chartkit.plot(title="Taxa de juros", units='%', source='BCB')

# Gráfico de barras
df.chartkit.variation().plot(kind='bar', title="Variação mensal", units='%', highlight=['last'])

# Gráfico com métricas (ATH, média móvel, etc)
df.chartkit.plot(title="Análise", metrics=['ath|Máxima', 'atl|Mínima', 'ma:12|Média móvel'])

# Encadeamento completo
df.chartkit.variation().plot(title="Variação mensal").show()
```

### Exemplo rápido de composição

```python
from chartkit import compose

camada_taxa = df.chartkit.layer(units='%', highlight=True)
camada_variacao = df.chartkit.variation().layer(kind='bar', units='%', axis='right')

compose(camada_taxa, camada_variacao, title="Taxa e variação mensal", source="BCB")
```

## Recursos

- **Pandas Accessor**: use `df.chartkit.plot()` direto em qualquer DataFrame
- **Tipos de gráfico**: linha, barra, barra empilhada, área, histograma, pizza, dispersão, stem, stairs, boxplot, violinplot e outros -- qualquer tipo do matplotlib funciona via rendering genérico
- **Composição**: combine múltiplas camadas com suporte a eixo duplo via `compose()`
- **Formatadores**: BRL, USD, BRL_compact, USD_compact, %, pontos, notação legível (1k, 1M)
- **Métricas declarativas**: `metrics=['ath', 'atl', 'ma:12', 'hline:3.0', 'band:1.5:4.5', 'target:1000', 'std_band:20:2', 'vband:2020-03:2020-06']`
- **Transforms encadeáveis**: `df.chartkit.variation(horizon='year').drawdown().plot()` com method chaining e detecção automática de frequência
- **Controle de eixos**: `xlabel`, `ylabel`, `xlim`, `ylim`, `grid`, `tick_format`, `tick_freq`
- **Overlays**: bandas de desvio padrão, bandas verticais
- **ChartRenderer**: rendering genérico via `ax.{kind}()` para qualquer tipo do matplotlib, com enhancers para os tipos complexos
- **Configuração via TOML + variáveis de ambiente**: customize por arquivo TOML ou por variáveis (`CHARTKIT_*`)

### Localização

Os defaults são pt-BR: `R$ 1.234,56` no eixo Y, `mar/24` no eixo X. A localidade
vale para os dois -- `formatters.locale.babel_locale` alimenta tanto os valores
monetários quanto os nomes de mês e de dia da semana pedidos por um
`tick_format`. Troque para `en_US` e o gráfico inteiro acompanha.

## Comportamento como biblioteca

O chartkit é feito para não deixar rastro no processo que o hospeda:

- **Sem mutação global de `rcParams`.** O tema é escopado a cada gráfico por um
  context manager, então seus outros plots de matplotlib não são afetados.
- **Sem figuras retidas.** Os gráficos são construídos fora do `pyplot`, então a
  figura é liberada assim que você descarta o `PlotResult`. Use `.close()` ou a
  forma de context manager ao gerar gráficos em loop, e depois de `.show()`.
- **Agnóstico de backend.** Funciona headless sob `Agg`, `pdf` e `svg`.
- **Logging silencioso, warnings audíveis.** O logging segue a convenção da
  stdlib e não emite nada até você configurá-lo. Qualquer coisa que mude seu
  resultado -- uma coluna descartada, uma janela inferida, um parâmetro ignorado
  -- vira um `ChartKitWarning`, visível por padrão e filtrável.

```python
import warnings
import chartkit

# Trata qualquer mudança silenciosa nos dados como erro
warnings.simplefilter("error", chartkit.DataMutationWarning)

# Libera figuras imediatamente num job em lote
for nome, frame in datasets.items():
    with frame.chartkit.plot(title=nome) as chart:
        chart.save(f"{nome}.png")
```

Importar o chartkit registra o accessor `.chartkit` do pandas e os enhancers de
gráfico, e anexa um `NullHandler` ao logger. Não lê arquivos de configuração nem
cria figuras -- isso acontece no primeiro plot.

## Documentação

A documentação está em inglês.

### Para começar

- [Galeria](docs/gallery.md) - séries macro brasileiras, renderizadas com o tema padrão
- [Getting Started](docs/getting-started.md) - seu primeiro gráfico em 2 minutos
- [Cookbook](docs/cookbook.md) - receitas práticas para dados financeiros

### Guias

| Guia | Descrição |
|------|-----------|
| [Plotting](docs/guide/plotting.md) | Tipos de gráfico, formatação, composição e PlotResult |
| [Composition](docs/guide/composition.md) | Tutoriais e snippets de `layer()` + `compose()` |
| [Metrics](docs/guide/metrics.md) | Sistema declarativo de métricas |
| [Transforms](docs/guide/transforms.md) | Transformações temporais e encadeamento |
| [Configuration](docs/guide/configuration.md) | TOML, paths e auto-discovery |

### Referência

- [API Reference](docs/reference/api.md) - assinaturas, tipos e parâmetros

### Para contribuidores

| Documento | Descrição |
|-----------|-----------|
| [Architecture](docs/contributing/architecture.md) | Visão geral e fluxo de dados |
| [Extending](docs/contributing/extending.md) | MetricRegistry e extensibilidade |
| [Internals](docs/contributing/internals.md) | Thread-safety, caching e logging |
| [Testing](docs/contributing/testing.md) | Suite de testes, fixtures e padrões |

## Requisitos

- Python >= 3.12
- pandas >= 2.2.0
- matplotlib >= 3.10.0
- numpy >= 2.0.0
- pydantic >= 2.0
- pydantic-settings >= 2.12.0
- Babel >= 2.17.0
