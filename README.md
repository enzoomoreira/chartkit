# agora-charting

Biblioteca de charting padronizado para visualizacao de dados financeiros, seguindo a identidade visual da Agora Investimentos.

Gera graficos profissionais via Pandas Accessor com uma linha de codigo.

## Instalacao

```bash
uv add agora-charting
```

## Quick Start

```python
import pandas as pd
import agora_charting  # Registra o accessor .agora

# Dados de exemplo
df = pd.DataFrame({
    'taxa': [10.5, 11.2, 10.8, 12.1, 11.9, 13.0]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Grafico de linha com formatacao percentual
df.agora.plot(title="Taxa de Juros", units='%', source='BCB')

# Grafico de barras
df.agora.plot(kind='bar', title="Variacao Mensal", units='%', highlight_last=True)

# Salvar grafico
df.agora.plot(title="Meu Grafico", save_path="grafico.png")
```

## Funcionalidades

- **Pandas Accessor**: Use `df.agora.plot()` diretamente em qualquer DataFrame
- **Graficos**: Linhas e barras com estilo institucional
- **Formatadores**: BRL, USD, %, pontos, notacao humana (1k, 1M)
- **Overlays**: Media movel, linhas ATH/ATL, linhas de referencia, bandas
- **Transformacoes**: YoY, MoM, acumulado 12m, juros real, normalizacao
- **Auto-discovery**: Detecta automaticamente paths de output do projeto

## Documentacao

| Documento | Descricao |
|-----------|-----------|
| [Getting Started](docs/getting-started.md) | Instalacao e primeiros passos |
| [API Reference](docs/api-reference.md) | Referencia completa da API |
| [Transforms](docs/transforms.md) | Funcoes de transformacao temporal |
| [Overlays](docs/overlays.md) | Elementos visuais secundarios |
| [Styling](docs/styling.md) | Tema, cores e formatadores |
| [Architecture](docs/architecture.md) | Arquitetura interna |

## Requisitos

- Python >= 3.12
- pandas >= 2.2.0
- matplotlib >= 3.10.0
- numpy >= 2.0.0
