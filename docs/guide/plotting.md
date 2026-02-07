# Tipos de Grafico e Formatacao

Guia completo sobre os tipos de grafico disponiveis no chartkit e opcoes de formatacao.

## Grafico de Linhas

O grafico de linhas e o tipo padrao do chartkit. Ideal para visualizar tendencias temporais.

### Linha Simples

```python
import pandas as pd
import chartkit

# Dados de exemplo
df = pd.DataFrame({
    'taxa': [10.5, 11.2, 10.8, 12.1, 11.9, 13.0]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Grafico de linha basico
df.chartkit.plot(title="Taxa de Juros")
```

### Multiplas Series

Para plotar varias series no mesmo grafico, basta incluir multiplas colunas no DataFrame:

```python
df = pd.DataFrame({
    'serie_a': [10, 12, 11, 14, 13, 15],
    'serie_b': [8, 9, 10, 11, 12, 13],
    'serie_c': [12, 11, 13, 12, 14, 13],
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

# Plota todas as colunas numericas
df.chartkit.plot(title="Comparativo de Series")

# Ou selecione colunas especificas
df.chartkit.plot(y=['serie_a', 'serie_b'], title="Series A e B")
```

### Selecao de Colunas

Use o parametro `y` para especificar quais colunas plotar:

```python
# Uma unica coluna (passa como string)
df.chartkit.plot(y='serie_a', title="Apenas Serie A")

# Multiplas colunas (passa como lista)
df.chartkit.plot(y=['serie_a', 'serie_b'], title="Series Selecionadas")
```

Se `y` nao for especificado, todas as colunas numericas serao plotadas.

---

## Grafico de Barras

Use `kind='bar'` para criar graficos de barras. Ideal para comparacoes entre categorias ou visualizacao de valores positivos e negativos.

### Barras Basicas

```python
df = pd.DataFrame({
    'vendas': [150, 200, 180, 220, 250, 230]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.chartkit.plot(kind='bar', title="Vendas Mensais")
```

### Barras com Valores Positivos e Negativos

O chartkit lida automaticamente com valores positivos e negativos:

```python
df = pd.DataFrame({
    'saldo': [100, -50, 200, -75, 150, -25]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.chartkit.plot(kind='bar', title="Saldo Mensal", units='BRL')
```

### Origem do Eixo Y (y_origin)

O parametro `y_origin` e especifico de graficos de barras e passado via `**kwargs`:

```python
# Origem no zero (padrao) - mostra a magnitude completa
df.chartkit.plot(kind='bar', title="Saldo Mensal", y_origin='zero')

# Origem automatica - foca na variacao dos dados
df.chartkit.plot(kind='bar', title="Saldo Mensal", y_origin='auto')
```

| Valor | Comportamento |
|-------|---------------|
| `'zero'` | Eixo Y sempre comeca do zero. Mostra magnitude real. |
| `'auto'` | Matplotlib define os limites. Foca na variacao dos dados. |

Use `y_origin='zero'` quando a magnitude absoluta for importante. Use `y_origin='auto'` quando quiser destacar variacoes pequenas em valores grandes.

---

## Formatacao do Eixo Y

O parametro `units` controla como os valores do eixo Y sao formatados. O chartkit oferece varios formatadores pre-definidos.

### Moedas

```python
# Real brasileiro: R$ 1.234,56
df.chartkit.plot(title="Valores em BRL", units='BRL')

# Dolar americano: $ 1,234.56
df.chartkit.plot(title="Valores em USD", units='USD')
```

### Moedas Compactas

Para valores grandes, use os formatos compactos:

```python
# Real compacto: R$ 1,2 mi (milhoes), R$ 1,2 bi (bilhoes)
df.chartkit.plot(title="PIB", units='BRL_compact')

# Dolar compacto: $1.2M, $1.2B
df.chartkit.plot(title="Revenue", units='USD_compact')
```

### Percentual

```python
# Percentual: 10,5%
df.chartkit.plot(title="Taxa de Inflacao", units='%')
```

O formatador de percentual usa locale brasileiro (virgula como separador decimal).

### Inteiros (Points)

```python
# Inteiros com separador de milhar brasileiro: 1.234.567
df.chartkit.plot(title="Numero de Clientes", units='points')
```

Ideal para valores inteiros grandes como populacao, numero de clientes, etc.

### Notacao Humana (Human)

```python
# Notacao compacta: 1,2M (milhoes), 1,2B (bilhoes)
df.chartkit.plot(title="Volume", units='human')
```

O formato `human` e similar ao `BRL_compact`, mas sem o simbolo de moeda. Util para valores numericos gerais.

### Tabela de Formatadores

| Valor | Formato | Exemplo |
|-------|---------|---------|
| `'BRL'` | Real brasileiro | R$ 1.234,56 |
| `'USD'` | Dolar americano | $ 1,234.56 |
| `'BRL_compact'` | Real compacto | R$ 1,2 mi |
| `'USD_compact'` | Dolar compacto | $1.2M |
| `'%'` | Percentual | 10,5% |
| `'points'` | Inteiros BR | 1.234.567 |
| `'human'` | Notacao compacta | 1,2M |

Os formatadores de moeda utilizam a biblioteca [Babel](https://babel.pocoo.org/) e suportam qualquer codigo de moeda ISO 4217.

---

## Rodape com Fonte

O parametro `source` adiciona um rodape com a fonte dos dados:

```python
df.chartkit.plot(
    title="Taxa Selic",
    units='%',
    source='Banco Central do Brasil'
)
```

O texto do rodape segue o formato configurado em `branding.footer_format`. O padrao e:

```
Fonte: {source}, {company_name}
```

### Customizando o Formato do Rodape

Via arquivo TOML:

```toml
[branding]
company_name = "Minha Empresa"
footer_format = "Fonte: {source} | Elaboracao: {company_name}"
```

Via codigo:

```python
from chartkit import configure

configure(branding={
    'company_name': 'Minha Empresa',
    'footer_format': 'Fonte: {source} | Elaboracao: {company_name}'
})
```

---

## Destacar Ultimo Valor

O parametro `highlight_last=True` adiciona um marcador e label no ultimo ponto de cada serie:

```python
df.chartkit.plot(
    title="Taxa de Juros",
    units='%',
    highlight_last=True
)
```

Isso e util para:

- Destacar o valor mais recente em series temporais
- Facilitar a leitura do ultimo dado sem consultar a tabela
- Apresentacoes e relatorios

### Exemplo Completo

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'selic': [13.75, 13.25, 12.75, 12.25, 11.75, 11.25]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.chartkit.plot(
    title="Taxa Selic",
    units='%',
    source='BCB',
    highlight_last=True
)
```

---

## Method Chaining com PlotResult

O metodo `plot()` retorna um objeto `PlotResult` que permite encadeamento de operacoes.

### Salvar Grafico

```python
# Salva no diretorio de charts configurado
df.chartkit.plot(title="Grafico").save('meu_grafico.png')

# Salva com DPI customizado
df.chartkit.plot(title="Grafico").save('meu_grafico.png', dpi=150)

# Path absoluto
df.chartkit.plot(title="Grafico").save('C:/temp/grafico.png')
```

Se o path for relativo, o grafico e salvo em `CHARTS_PATH` (configuravel).

### Mostrar Grafico

```python
# Exibe em janela interativa
df.chartkit.plot(title="Grafico").show()
```

### Encadeamento Completo

```python
# Salvar e mostrar na mesma chamada
df.chartkit.plot(title="Grafico").save('grafico.png').show()

# Salvar com DPI alto, depois mostrar
df.chartkit.plot(title="Grafico").save('grafico.png', dpi=300).show()
```

### Acesso ao Axes e Figure

O `PlotResult` expoe o `Axes` e `Figure` do matplotlib para customizacoes avancadas:

```python
result = df.chartkit.plot(title="Grafico")

# Acesso ao Axes
result.axes.set_xlim(['2024-01-01', '2024-12-31'])
result.axes.axhline(5, color='red', linestyle='--')
result.axes.set_ylabel('Meu Label')

# Acesso ao Figure
result.figure.set_size_inches(14, 8)
result.figure.suptitle('Titulo Superior')

# Salvar apos customizacoes
result.save('grafico_customizado.png')
```

### API do PlotResult

| Metodo/Propriedade | Retorno | Descricao |
|--------------------|---------|-----------|
| `save(path, dpi=None)` | `PlotResult` | Salva o grafico e retorna self |
| `show()` | `PlotResult` | Exibe o grafico e retorna self |
| `axes` | `Axes` | Acesso ao matplotlib Axes |
| `figure` | `Figure` | Acesso ao matplotlib Figure |

---

## Exemplos Completos

### Dashboard Financeiro

```python
import pandas as pd
import chartkit

# Taxa Selic
selic = pd.DataFrame({
    'taxa': [13.75, 13.25, 12.75, 12.25, 11.75, 11.25]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

selic.chartkit.plot(
    title="Taxa Selic",
    units='%',
    source='Banco Central do Brasil',
    highlight_last=True
).save('selic.png')

# Variacao do Dolar
dolar = pd.DataFrame({
    'cotacao': [4.95, 5.02, 4.98, 5.15, 5.08, 5.22]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

dolar.chartkit.plot(
    title="Cotacao do Dolar",
    units='BRL',
    source='BCB',
    highlight_last=True
).save('dolar.png')
```

### Comparativo de Investimentos

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'CDI': [100, 101.1, 102.2, 103.4, 104.6, 105.8],
    'Ibovespa': [100, 98.5, 102.3, 105.1, 103.8, 108.2],
    'S&P 500': [100, 101.5, 103.2, 105.8, 107.1, 109.5],
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.chartkit.plot(
    title="Comparativo de Investimentos (Base 100)",
    units='points',
    source='Bloomberg',
    highlight_last=True
).save('comparativo.png')
```

### Saldo Mensal com Barras

```python
import pandas as pd
import chartkit

df = pd.DataFrame({
    'saldo': [15000, -8000, 22000, -5000, 18000, 25000]
}, index=pd.date_range('2024-01', periods=6, freq='ME'))

df.chartkit.plot(
    kind='bar',
    title="Saldo Mensal",
    units='BRL_compact',
    source='Contabilidade',
    y_origin='zero'
).save('saldo_mensal.png')
```

---

## Proximos Passos

- [Transforms](transforms.md) - Transformacoes temporais (YoY, MoM, etc.)
- [Metricas](metrics.md) - Overlays declarativos (ATH, medias moveis, bandas)
- [Configuracao](../reference/configuration.md) - Personalizacao completa
