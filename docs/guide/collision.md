# Collision Engine

Engine de resolucao automatica de colisao entre elementos visuais de graficos.

Quando um grafico possui multiplos labels, linhas de referencia e barras, esses
elementos competem pelo mesmo espaco visual. A collision engine reposiciona
labels automaticamente para eliminar sobreposicoes, produzindo graficos legivos
sem intervencao manual.

---

## Conceito

A engine e **agnostica a tipos**. Ela nao sabe o que e um "label", uma "barra"
ou uma "linha ATH". Ela so enxerga retangulos (bounding boxes) em pixels de tela
e tres categorias de participacao:

| Categoria | Funcao | Significado |
|-----------|--------|-------------|
| **Moveable** | `register_moveable(ax, artist)` | Pode ser reposicionado para resolver colisoes |
| **Fixed** | `register_fixed(ax, artist)` | Obstaculo imutavel que outros devem evitar |
| **Passive** | `register_passive(ax, artist)` | Existe visualmente mas nao participa da colisao |

Cada modulo externo decide como classificar seus proprios elementos. A engine
fornece os building blocks; os modulos fazem a integracao.

---

## Uso Automatico

Na maioria dos casos, a collision engine funciona automaticamente. Basta usar
metricas e highlights:

```python
# Labels e linhas sao registrados automaticamente
df.chartkit.plot(
    metrics=["ath", "atl", "hline:3.0", "band:1.5:4.5"],
    highlight=True,
)
```

Internamente, o pipeline do `engine.py` chama `resolve_collisions(ax)` apos
todos os elementos serem registrados.

---

## Uso Manual

Para cenarios avancados (overlays customizados, metricas proprias), use a API
diretamente:

```python
from chartkit import register_moveable, register_fixed, register_passive

# Criar um label que pode ser movido
text = ax.text(x, y, "Meu label", ha="left", va="center")
register_moveable(ax, text)

# Criar uma linha de referencia como obstaculo
line = ax.axhline(y=100, color="red", linestyle="--")
register_fixed(ax, line)

# Criar uma area de fundo que NAO e obstaculo
patch = ax.axhspan(50, 150, alpha=0.1, color="gray")
register_passive(ax, patch)
```

> **Importante**: Use `ax.text()`, nao `ax.annotate()`. O `ax.text()` usa
> `transData` nativamente, permitindo reposicionamento programatico via
> `get_position()`/`set_position()`. O `ax.annotate(textcoords="offset points")`
> usa transforms customizados incompativeis com a engine.

---

## Como Funciona

### Estado Interno

O estado de colisao (quais artists sao moveable, fixed, passive) e armazenado
em `WeakKeyDictionary` module-level indexadas por `Axes`. Isso significa:

- **Limpeza automatica**: quando um `Axes` e destruido pelo GC, suas entradas
  sao removidas automaticamente. Nao ha risco de memory leak.
- **Sem poluicao de namespace**: nenhum atributo privado e adicionado aos
  objetos matplotlib (anteriormente usava `ax._charting_labels`, etc.).

### Pipeline de Rendering

A collision engine e executada no step 6 do pipeline, apos todos os elementos
serem criados e antes das decoracoes finais:

```
1. Style           theme.apply()
2. Data            resolve x_data, y_data
3. Y Formatter     ax.yaxis.set_major_formatter(...)
4. Plot Core       ChartRegistry dispatch + highlights (register_moveable)
5. Metrics         ATH/ATL/hline (register_fixed) + MA (register_passive) + band (register_passive)
6. Collisions      resolve_collisions(ax)
7. Title/Footer    ax.set_title(), fig.text()
8. Output          PlotResult
```

### Algoritmo em 3 Fases

#### Fase 1: Moveables vs Fixed

Para cada moveable, verifica colisao contra todos os obstaculos fixos.
Se ha colisao, calcula o **menor deslocamento possivel** entre ate 4 direcoes:

```
Exemplo com movement="y" (default):

    Label colide com linha ATH.

    UP:   mover label acima da linha   -> 15px
    DOWN: mover label abaixo da linha  -> 42px

    Menor: UP (15px). Label sobe 15px.
```

Restricoes respeitadas:
- **Eixo de movimento**: configuravel (`"y"`, `"x"`, ou `"xy"`)
- **Limites do axes**: label nunca sai da area visivel do grafico

Se nenhuma direcao e valida (label encurralado entre obstaculos e borda do axes),
o label permanece na posicao original.

#### Fase 2: Moveables vs Moveables

Push-apart iterativo entre pares de labels. Quando dois labels colidem, ambos
sao empurrados em direcoes opostas por metade do overlap + padding:

```
    Label A e Label B sobrepostos em Y por 20px:

    shift = 20/2 + padding/2 = 12px

    Label A (mais alto): sobe 12px
    Label B (mais baixo): desce 12px
```

Repete ate convergir (nenhum par colide) ou atingir `max_iterations`.

#### Fase 3: Connectors

Se um label foi deslocado alem de `connector_threshold_px` (default: 30px)
da posicao original, uma linha guia e desenhada conectando o ponto de dados
original ao label reposicionado. Preserva a associacao visual dado-label.

### Coleta de Obstaculos

A engine combina duas fontes de obstaculos:

1. **Explicitos**: elementos registrados via `register_fixed()` (linhas ATH, ATL, hline)
2. **Auto-detectados**: todos os `ax.patches` (barras de graficos de barras)

A auto-deteccao existe para que barras sejam obstaculos automaticamente sem
registro manual. Porem, nem todo patch e obstaculo - bandas sombreadas
(`ax.axhspan`) tambem criam patches, mas sao elementos de fundo transparentes.

Para excluir um patch da auto-deteccao, use `register_passive()`. A engine
filtra:
- Patches registrados como moveable (labels nao sao obstaculos de si mesmos)
- Patches registrados como passive (bandas, areas de fundo)
- Patches ja registrados como fixed (evita duplicacao)

---

## Integracao com Metricas Customizadas

Ao criar metricas customizadas via `MetricRegistry.register`, use as funcoes
de registro para integrar com a collision engine:

```python
from chartkit import register_fixed, register_moveable, register_passive
from chartkit.metrics import MetricRegistry

@MetricRegistry.register("target", param_names=["value"])
def metric_target(ax, x_data, y_data, value: float, **kwargs):
    """Linha de meta com label."""
    # Linha como obstaculo fixo
    line = ax.axhline(y=value, color="green", linestyle="--")
    register_fixed(ax, line)

    # Label como moveable
    text = ax.text(
        x_data[-1], value, f"  Meta: {value}",
        ha="left", va="center", color="green",
    )
    register_moveable(ax, text)

# Uso:
df.chartkit.plot(metrics=["target:100", "ath"], highlight=True)
# A engine resolve colisoes entre o label "Meta: 100", o label do
# highlight, a linha ATH e a linha de meta automaticamente.
```

Se sua metrica cria uma area de fundo que nao deve ser obstaculo:

```python
@MetricRegistry.register("zone", param_names=["lower", "upper"], uses_series=False)
def metric_zone(ax, x_data, y_data, lower: float, upper: float, **kwargs):
    """Zona sombreada (nao-obstaculo)."""
    patch = ax.axhspan(lower, upper, alpha=0.1, color="blue")
    register_passive(ax, patch)
```

---

## Configuracao

Todos os parametros da engine sao configuraveis via TOML:

```toml
[collision]
movement = "y"                  # Eixo de deslocamento: "y", "x", ou "xy"
obstacle_padding_px = 8.0       # Padding entre label e obstaculo (px)
label_padding_px = 4.0          # Padding entre labels (px)
max_iterations = 50             # Limite de iteracoes push-apart
connector_threshold_px = 30.0   # Distancia minima para desenhar connector (px)
connector_alpha = 0.6           # Transparencia da linha connector
connector_style = "-"           # Estilo da linha connector ("-", "--", ":", "-.")
connector_width = 1.0           # Espessura da linha connector
```

Ou via `configure()`:

```python
from chartkit import configure

configure(collision={
    "movement": "xy",
    "connector_threshold_px": 50.0,
})
```

### Parametros

| Parametro | Default | Descricao |
|-----------|---------|-----------|
| `movement` | `"y"` | Eixo permitido para deslocamento. `"y"` e recomendado para series temporais (preserva posicao temporal no eixo X) |
| `obstacle_padding_px` | `8.0` | Espaco minimo entre label e obstaculo em pixels |
| `label_padding_px` | `4.0` | Espaco minimo entre dois labels em pixels |
| `max_iterations` | `50` | Numero maximo de iteracoes do push-apart entre labels |
| `connector_threshold_px` | `30.0` | Distancia minima (px) de deslocamento para desenhar linha guia |
| `connector_alpha` | `0.6` | Transparencia da linha guia (0.0 = invisivel, 1.0 = opaco) |
| `connector_style` | `"-"` | Estilo matplotlib da linha guia |
| `connector_width` | `1.0` | Espessura da linha guia em pontos |

---

## Decisoes de Design

### Por que agnostica a tipos concretos?

A engine nunca faz `isinstance(artist, Text)` ou `isinstance(patch, Rectangle)`.
Para moveables, usa um `PositionableArtist` Protocol (`runtime_checkable`) que
verifica estruturalmente se o artist tem `get_position()`, `set_position()` e
`get_window_extent()`. Para obstaculos, trabalha exclusivamente com
`Artist.get_window_extent(renderer)`, que retorna um `Bbox` em display pixels.

Se amanha adicionarmos um novo tipo de overlay (ex: anotacoes, setas, boxes),
ele funciona com a engine sem modificar uma unica linha dela -- basta que
implemente os metodos do Protocol. A responsabilidade de classificacao e do
modulo que cria o elemento.

### Por que display pixels?

Data coordinates podem ser datas, percentuais, moedas - unidades incomparaveis
entre X e Y. Display pixels sao uniformes e permitem:
- Comparacao direta entre bboxes de elementos em eixos diferentes
- Padding visual consistente independente do zoom ou escala
- Uso direto de `Bbox.overlaps()` do matplotlib

### Por que `movement="y"` como default?

Em series temporais (caso de uso principal), o eixo X representa tempo. Deslocar
um label horizontalmente quebraria a associacao temporal - o label de "dezembro"
apareceria sobre "novembro". Restringir movimento ao eixo Y preserva a posicao
temporal e produz resultados intuitivos.

### Por que 3 categorias (moveable/fixed/passive)?

Duas categorias (moveable/fixed) nao sao suficientes. A auto-deteccao de
`ax.patches` como obstaculos e necessaria para barras, mas `ax.axhspan()` tambem
cria patches. Sem a terceira categoria, bandas semi-transparentes de fundo seriam
tratadas como obstaculos gigantes, empurrando labels para fora da area da banda.

A alternativa seria a engine verificar tipos (`isinstance(patch, Polygon)`) ou
propriedades (`alpha < 0.5`), mas isso quebraria o agnosticismo. A solucao
correta: o modulo que cria o elemento sabe o que ele e e se auto-classifica.

### Por que `resolve_collisions` nao e publica?

A resolucao e orquestrada pelo pipeline do `engine.py`. Metricas customizadas
registram elementos e a engine resolve automaticamente no step 6. Expor
`resolve_collisions` na API publica incentivaria chamadas manuais em momentos
errados do pipeline (antes de todos os elementos serem registrados, por exemplo).

`register_moveable`, `register_fixed` e `register_passive` sao publicas porque
metricas customizadas precisam registrar seus elementos. A resolucao em si e
responsabilidade do orquestrador.
