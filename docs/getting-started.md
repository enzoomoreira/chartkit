# Getting Started

Guia de instalacao e primeiros passos com o agora-charting.

## Pre-requisitos

- Python >= 3.12
- pandas >= 2.2.0

## Instalacao

```bash
uv add agora-charting
```

## Primeiro Grafico

```python
import pandas as pd
import agora_charting  # Registra o accessor .agora

# Dados de exemplo
df = pd.DataFrame({
    'valor': [10.5, 11.2, 10.8, 12.1, 11.9, 13.0]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Grafico basico
df.agora.plot(title="Meu Primeiro Grafico")
```

O import do `agora_charting` registra automaticamente o accessor `.agora` em todos os DataFrames.

## Configuracao de Paths

O modulo detecta automaticamente onde salvar os graficos. Voce pode customizar se necessario.

### Auto-Discovery (Padrao)

O sistema procura por markers de projeto (`pyproject.toml`, `.git`, etc) e usa convencoes de pastas:

1. `outputs/`
2. `data/outputs/`
3. `output/`
4. `data/output/`

Se nenhuma existir, usa `outputs/charts` relativo ao project root.

### Configuracao Manual

```python
from agora_charting import configure
from pathlib import Path

# Define path customizado
configure(outputs_path=Path('./meus_outputs'))

# Ou apenas o subdiretorio de charts
configure(charts_subdir='graficos')
```

### Variavel de Ambiente

```powershell
$env:AGORA_CHARTING_OUTPUTS_PATH = "C:/caminho/para/outputs"
```

### Verificar Path Atual

```python
from agora_charting import CHARTS_PATH, OUTPUTS_PATH

print(f"Charts: {CHARTS_PATH}")
print(f"Outputs: {OUTPUTS_PATH}")
```

## Salvando Graficos

### Via Parametro

```python
df.agora.plot(title="Grafico", save_path="grafico.png")
```

Se o path for relativo, salva em `CHARTS_PATH/grafico.png`.

### Via Metodo

```python
df.agora.plot(title="Grafico")
df.agora.save("grafico.png")
```

### Path Absoluto

```python
df.agora.plot(title="Grafico", save_path="C:/temp/grafico.png")
```

## Tipos de Grafico

### Linhas (Padrao)

```python
df.agora.plot(title="Linha", units='%')
```

### Barras

```python
df.agora.plot(kind='bar', title="Barras", units='%')
```

## Formatacao do Eixo Y

Use o parametro `units` para formatar valores:

```python
# Moeda brasileira: R$ 1.234,56
df.agora.plot(units='BRL')

# Dolar: $ 1,234.56
df.agora.plot(units='USD')

# Percentual: 10,5%
df.agora.plot(units='%')

# Inteiros com separador: 1.234.567
df.agora.plot(units='points')

# Notacao compacta: 1,2M
df.agora.plot(units='human')
```

## Rodape com Fonte

```python
df.agora.plot(title="Taxa Selic", units='%', source='BCB')
# Rodape: "Fonte: BCB, Agora Investimentos"
```

## Destacar Ultimo Valor

```python
df.agora.plot(title="Grafico", highlight_last=True)
```

Adiciona um marcador e label no ultimo ponto da serie.

## Proximos Passos

- [API Reference](api-reference.md) - Documentacao completa da API
- [Transforms](transforms.md) - Funcoes de transformacao temporal
- [Overlays](overlays.md) - Media movel, linhas de referencia
- [Styling](styling.md) - Customizacao visual
