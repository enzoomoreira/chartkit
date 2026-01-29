# Styling

Identidade visual e customizacao dos graficos.

> **Nota:** Todos os valores descritos nesta pagina sao os defaults e podem ser
> personalizados via arquivo TOML ou `configure()`. Veja [Configuration](configuration.md).

## Paleta de Cores

### Cores Principais (Gradiente Verde)

| Nome | Hex | Uso |
|------|-----|-----|
| primary | `#00464D` | Verde escuro institucional |
| secondary | `#006B6B` | Verde medio |
| tertiary | `#008B8B` | Teal |
| quaternary | `#20B2AA` | Light sea green |
| quinary | `#5F9EA0` | Cadet blue |
| senary | `#2E8B57` | Sea green |

### Cores Semanticas

| Nome | Hex | Uso |
|------|-----|-----|
| text | `#00464D` | Texto e labels |
| grid | `lightgray` | Linhas de grade |
| background | `white` | Fundo |
| positive | `#00464D` | Valores positivos (ATH) |
| negative | `#8B0000` | Valores negativos (ATL) |

### Ciclo de Cores

Para graficos com multiplas series, as cores sao aplicadas em ordem:

```python
from agora_charting import theme

colors = theme.colors.cycle()
# ['#00464D', '#006B6B', '#008B8B', '#20B2AA', '#5F9EA0', '#2E8B57']
```

---

## Fonte

O tema usa a fonte **BradescoSans-Light** quando disponivel.

### Localizacao

```
src/agora_charting/assets/fonts/BradescoSans-Light.ttf
```

### Fallback

Se a fonte nao estiver disponivel, usa `sans-serif`.

### Acesso Programatico

```python
from agora_charting import theme

print(theme.font_name)  # Nome da fonte ativa
print(theme.font)       # FontProperties do matplotlib
```

---

## Formatadores de Eixo Y

Use o parametro `units` para formatar valores no eixo Y.

### Disponíveis

| Valor | Funcao | Exemplo |
|-------|--------|---------|
| `'BRL'` | currency_formatter('BRL') | R$ 1.234,56 |
| `'USD'` | currency_formatter('USD') | $ 1,234.56 |
| `'%'` | percent_formatter() | 10,5% |
| `'points'` | points_formatter() | 1.234.567 |
| `'human'` | human_readable_formatter() | 1,2M |

### BRL - Real Brasileiro

```python
df.agora.plot(units='BRL')
# R$ 1.234,56
```

- Prefixo: R$
- Separador de milhar: ponto
- Separador decimal: virgula

### USD - Dolar Americano

```python
df.agora.plot(units='USD')
# $ 1,234.56
```

- Prefixo: $
- Separador de milhar: virgula
- Separador decimal: ponto

### % - Percentual

```python
df.agora.plot(units='%')
# 10.000,5%
```

- Sufixo: %
- Separador de milhar: ponto (padrao BR)
- Separador decimal: virgula

### points - Inteiros

```python
df.agora.plot(units='points')
# 1.234.567
```

- Separador de milhar: ponto (padrao BR)
- Sem casas decimais por padrao

### human - Notacao Compacta

```python
df.agora.plot(units='human')
# 1,2M  (1.200.000)
# 500k  (500.000)
# 2,5B  (2.500.000.000)
```

Sufixos: k (mil), M (milhao), B (bilhao), T (trilhao)

---

## Componentes

### Footer (Rodape)

Adicionado automaticamente quando `source` e especificado.

```python
df.agora.plot(title="Grafico", source='BCB')
# Rodape: "Fonte: BCB, Agora Investimentos"

df.agora.plot(title="Grafico")
# Rodape: "Agora Investimentos"
```

#### Caracteristicas

- Posicao: Canto inferior esquerdo
- Alinhamento: Borda esquerda do axes
- Fonte: 9pt, cinza (configuravel via `fonts.sizes.footer` e `layout.footer.color`)
- Formato configuravel via `branding.footer_format` e `branding.footer_format_no_source`

#### Personalizacao

```toml
# charting.toml
[branding]
company_name = "Minha Empresa"
footer_format = "Dados: {source} | {company_name}"
footer_format_no_source = "Elaborado por {company_name}"
```

### Markers (Destaque)

Ativado com `highlight_last=True`.

```python
df.agora.plot(title="Grafico", highlight_last=True)
```

#### Linha

- Ponto circular no ultimo valor
- Label com valor formatado (usa formatador do eixo Y)

#### Barras

- Ultima barra destacada com cor diferente
- Label com valor formatado

---

## Configuracoes do Tema

O tema aplica as seguintes configuracoes no matplotlib (valores default):

```python
# Fontes (configuravel via fonts.sizes)
'font.family': 'BradescoSans-Light'  # ou fallback (fonts.fallback)
'font.size': 11                       # fonts.sizes.default
'axes.titlesize': 18                  # fonts.sizes.title
'axes.labelsize': 11                  # fonts.sizes.axis_label

# Grid
'axes.grid': False

# Layout (configuravel via layout.figsize)
'figure.figsize': (10, 6)             # layout.figsize
'figure.facecolor': 'white'           # colors.background
'axes.facecolor': 'white'             # colors.background

# Spines (bordas)
'axes.spines.top': False
'axes.spines.right': False
'axes.spines.left': True
'axes.spines.bottom': True
```

### Estilo Base

O tema usa `seaborn-v0_8-white` como base.

### Personalizacao via TOML

```toml
# charting.toml
[fonts.sizes]
default = 12
title = 20
footer = 10
axis_label = 12

[layout]
figsize = [12.0, 8.0]
dpi = 150

[colors]
background = "#FAFAFA"
text = "#333333"
```

---

## Tema Programatico

### Aplicar Manualmente

```python
from agora_charting import theme

theme.apply()  # Aplica configuracoes no matplotlib global
```

### Acessar Cores

```python
from agora_charting import theme

theme.colors.primary    # '#00464D'
theme.colors.negative   # '#8B0000'
theme.colors.cycle()    # Lista de 6 cores
```

### Acessar Fonte

```python
from agora_charting import theme

theme.font_name  # 'BradescoSans-Light' ou 'sans-serif'
theme.font       # FontProperties
```

### Acessar Configuracao Completa

```python
from agora_charting import get_config

config = get_config()
print(config.colors.primary)
print(config.fonts.sizes.title)
print(config.layout.figsize)
```

---

## Veja Tambem

- [Configuration](configuration.md) - Guia completo de configuracao TOML
