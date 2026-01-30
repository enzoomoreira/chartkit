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
from chartkit import theme

colors = theme.colors.cycle()
# ['#00464D', '#006B6B', '#008B8B', '#20B2AA', '#5F9EA0', '#2E8B57']
```

---

## Fonte

O tema suporta fontes customizadas via configuracao TOML.

### Configuracao

```toml
[fonts]
file = "fonts/MinhaFonte.ttf"  # Relativo a assets/ ou caminho absoluto
fallback = "sans-serif"        # Fonte de fallback
```

Se nenhuma fonte customizada for configurada (`file = ""`), o sistema usa
diretamente a fonte de fallback (`sans-serif` por padrao).

### Acesso Programatico

```python
from chartkit import theme

print(theme.font_name)  # Nome da fonte configurada ou fallback
print(theme.font)       # FontProperties do matplotlib
```

---

## Formatadores de Eixo Y

Use o parametro `units` para formatar valores no eixo Y.

Os formatadores de moeda usam a biblioteca [Babel](https://babel.pocoo.org/) para
internacionalizacao, suportando qualquer codigo de moeda ISO 4217.

### Disponíveis

| Valor | Funcao | Exemplo |
|-------|--------|---------|
| `'BRL'` | currency_formatter('BRL') | R$ 1.234,56 |
| `'USD'` | currency_formatter('USD') | $ 1,234.56 |
| `'BRL_compact'` | compact_currency_formatter('BRL') | R$ 1,2 mi |
| `'USD_compact'` | compact_currency_formatter('USD') | $1.2M |
| `'%'` | percent_formatter() | 10,5% |
| `'points'` | points_formatter() | 1.234.567 |
| `'human'` | human_readable_formatter() | 1,2M |

### BRL - Real Brasileiro

```python
df.chartkit.plot(units='BRL')
# R$ 1.234,56
```

Formatado via Babel com locale `pt_BR`. Suporta qualquer moeda ISO 4217.

### USD - Dolar Americano

```python
df.chartkit.plot(units='USD')
# $ 1,234.56
```

Formatado via Babel com locale configurado (default: `pt_BR`).

### BRL_compact / USD_compact - Notacao Compacta

```python
df.chartkit.plot(units='BRL_compact')
# R$ 1,2 mi  (para 1.234.567)
# R$ 500 mil (para 500.000)
# R$ 2,5 bi  (para 2.500.000.000)

df.chartkit.plot(units='USD_compact')
# $1.2M  (para 1.234.567)
```

Ideal para graficos com valores grandes (milhoes, bilhoes). Valores abaixo de 1.000
usam formatacao normal.

### % - Percentual

```python
df.chartkit.plot(units='%')
# 10.000,5%
```

- Sufixo: %
- Separador de milhar: ponto (padrao BR)
- Separador decimal: virgula

### points - Inteiros

```python
df.chartkit.plot(units='points')
# 1.234.567
```

- Separador de milhar: ponto (padrao BR)
- Sem casas decimais por padrao

### human - Notacao Compacta

```python
df.chartkit.plot(units='human')
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
df.chartkit.plot(title="Grafico", source='BCB')
# Rodape: "Fonte: BCB, {company_name}"  (configure via branding.company_name)

df.chartkit.plot(title="Grafico")
# Rodape: "{company_name}"  (ou vazio se nao configurado)
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
df.chartkit.plot(title="Grafico", highlight_last=True)
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
'font.family': fonts.fallback  # Fonte configurada ou 'sans-serif'
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
from chartkit import theme

theme.apply()  # Aplica configuracoes no matplotlib global
```

### Acessar Cores

```python
from chartkit import theme

theme.colors.primary    # '#00464D'
theme.colors.negative   # '#8B0000'
theme.colors.cycle()    # Lista de 6 cores
```

### Acessar Fonte

```python
from chartkit import theme

theme.font_name  # Nome da fonte configurada ou 'sans-serif'
theme.font       # FontProperties
```

### Acessar Configuracao Completa

```python
from chartkit import get_config

config = get_config()
print(config.colors.primary)
print(config.fonts.sizes.title)
print(config.layout.figsize)
```

---

## Veja Tambem

- [Configuration](configuration.md) - Guia completo de configuracao TOML
