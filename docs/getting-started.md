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

## Configuracao

O modulo usa um sistema de configuracao flexivel baseado em TOML. Por padrao, usa valores da Agora Investimentos, mas voce pode personalizar tudo.

### Ordem de Precedencia

A configuracao e carregada das seguintes fontes (maior para menor prioridade):

1. `configure()` - Configuracao programatica
2. `.charting.toml` ou `charting.toml` - Arquivo na raiz do projeto
3. `pyproject.toml [tool.charting]` - Secao no pyproject.toml
4. `~/.config/charting/config.toml` - Config global do usuario (Linux/Mac)
5. `%APPDATA%/charting/config.toml` - Config global do usuario (Windows)
6. Defaults built-in

### Arquivo TOML

Crie um arquivo `.charting.toml` ou `charting.toml` na raiz do projeto:

```toml
[branding]
company_name = "Minha Empresa"
footer_format = "Fonte: {source}, {company_name}"

[colors]
primary = "#003366"
secondary = "#0066CC"

[layout]
figsize = [12.0, 8.0]
dpi = 150
```

Veja `charting.example.toml` para todas as opcoes disponiveis.

### Via pyproject.toml

```toml
[tool.charting]
[tool.charting.branding]
company_name = "Minha Empresa"

[tool.charting.colors]
primary = "#003366"
```

### Configuracao Programatica

```python
from agora_charting import configure

# Customiza branding
configure(branding={'company_name': 'Minha Empresa'})

# Customiza cores
configure(colors={'primary': '#FF0000', 'secondary': '#00FF00'})

# Customiza layout
configure(layout={'figsize': [12.0, 8.0], 'dpi': 150})

# Combina multiplas secoes
configure(
    branding={'company_name': 'Banco XYZ'},
    colors={'primary': '#003366'},
)
```

### Arquivo de Configuracao Explicito

```python
from pathlib import Path
from agora_charting import configure

configure(config_path=Path('./minha-config.toml'))
```

### Variavel de Ambiente para Outputs

```powershell
$env:AGORA_CHARTING_OUTPUTS_PATH = "C:/caminho/para/outputs"
```

### Verificar Configuracao Atual

```python
from agora_charting import get_config, CHARTS_PATH, OUTPUTS_PATH

# Ver configuracao completa
config = get_config()
print(f"Company: {config.branding.company_name}")
print(f"Cor primaria: {config.colors.primary}")

# Ver paths
print(f"Charts: {CHARTS_PATH}")
print(f"Outputs: {OUTPUTS_PATH}")
```

### Reset de Configuracao

```python
from agora_charting.settings import reset_config

reset_config()  # Volta para defaults
```

## Auto-Discovery de Paths

O sistema detecta automaticamente onde salvar os graficos:

1. Procura por markers de projeto (`pyproject.toml`, `.git`, etc)
2. Usa convencoes de pastas: `outputs/`, `data/outputs/`, `output/`, `data/output/`
3. Se nenhuma existir, usa `outputs/charts` relativo ao project root

### Configuracao Manual de Paths

```python
from agora_charting import configure
from pathlib import Path

# Define path customizado para outputs
configure(outputs_path=Path('./meus_outputs'))
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

O texto do rodape e configuravel via `branding.footer_format`.

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
- [Configuration](configuration.md) - Guia completo de configuracao
