# Plano de Preparação para Publicação -- chartkit

Documento de planejamento derivado da auditoria completa do repositório (2026-08-02).
Cobre os 62 achados identificados, organizados em 8 fases sequenciais.

**Estado atual**: 603 testes passando, 8.108 linhas em `src/`, arquitetura sólida.
**Objetivo**: publicar no PyPI como `0.1.0` sem dívida de API nem comportamento de "má cidadã".

---

## Critério de pronto

A lib está pronta para publicar quando:

1. Não altera estado global do processo do usuário (rcParams, fontes, logger, figuras).
2. Não altera dados silenciosamente -- toda mutação de dados emite `warnings.warn`.
3. Funciona em backends headless (`Agg`, `pdf`, `svg`) sem `AttributeError`.
4. A API pública está congelada: mudá-la depois da 0.1.0 seria breaking change.
5. Metadados de distribuição completos, `LICENSE` presente, `py.typed` presente.
6. CI verificando matriz real de versões (Python, pandas, backends).

---

## Decisões de arquitetura

Estas decisões atravessam várias fases e devem ser tomadas antes de começar a implementar.

### D1 -- Ciclo de vida de figura: sair do pyplot

`create_figure()` usa `plt.subplots()` ([pipeline.py:41](src/chartkit/_internal/pipeline.py:41)), o que registra a figura no gerenciador global do pyplot. Isso é a causa raiz do vazamento de memória e do warning de "more than 20 figures".

**Decisão**: criar a figura via `matplotlib.figure.Figure()` + `FigureCanvasAgg` explícito, sem passar pelo pyplot. O handoff para o pyplot acontece apenas em `PlotResult.show()`, que é o único ponto onde interatividade é desejada.

Ganhos em cascata:
- Elimina o vazamento de figuras (sem registro global).
- Como a lib passa a **possuir** o canvas, `get_renderer()` sempre existe -- resolve o bug de backends não-Agg de raiz, em vez de por fallback defensivo.
- `PlotResult` deixa de depender do backend ativo do usuário.

### D2 -- Tema: `rc_context` em vez de mutação global

`theme.apply()` executa `plt.style.use()` + `plt.rcParams.update()` ([theme.py:41,71](src/chartkit/styling/theme.py:41)), alterando 24 chaves globalmente por plot.

**Decisão**: substituir `theme.apply()` por `theme.context()`, um context manager baseado em `matplotlib.rc_context`. Todo o corpo de `plot()` e `compose()` passa a rodar dentro dele.

Atenção: o matplotlib lê rcParams no momento de **criação** de cada artist, não no `savefig`. Portanto o context precisa envolver criação de figura, rendering, metrics, overlays e decorations -- ou seja, o corpo inteiro de `plot()`. Isso é um refactor estrutural, não uma troca de duas linhas.

### D3 -- Logging: migrar de loguru para `logging` stdlib

`_logging.py:14` chama `logger.disable("chartkit")` no logger **global** do loguru -- a lib toca o estado de logging de terceiros no import.

**Decisão**: migrar para `logging.getLogger(__name__)` + `NullHandler`. Remove uma dependência obrigatória e opinativa, e alinha com a expectativa de qualquer consumidor de biblioteca Python.

Custo: converter as chamadas de lazy-format do loguru (`logger.debug("x={}", v)`) para o estilo stdlib (`logger.debug("x=%s", v)`). É mecânico e verificável.

### D4 -- Avisos: `warnings.warn` para o que o usuário precisa ver

Hoje **todos** os avisos vão para o logger, que está desabilitado por padrão. Isso inclui avisos sobre alteração silenciosa de dados.

**Decisão**: criar `chartkit/warnings.py` com uma hierarquia própria:

```
ChartKitWarning(UserWarning)
├── DataMutationWarning   # dados alterados: colunas descartadas, spikes substituídos, inf->NaN
├── InferenceWarning      # fallback de frequência, janela auto-detectada
└── RenderingWarning      # highlight ignorado, gráfico ilegível, unidades conflitantes
```

Regra de corte: se a mensagem descreve algo que **muda o resultado** que o usuário vê ou os dados que ele plotou, é `warnings.warn`. Se é diagnóstico de fluxo interno, permanece no logger.

### D5 -- Paridade de assinatura por teste, não por metaprogramação

A assinatura de `plot()` está triplicada ([engine.py:48](src/chartkit/engine.py:48), [accessor.py:141](src/chartkit/accessor.py:141), [transforms/accessor.py:150](src/chartkit/transforms/accessor.py:150)) e **já divergiu**: `decimals` existe apenas na primeira.

**Decisão**: manter as assinaturas explícitas (melhor autocomplete e docstring por camada) e adicionar um teste de paridade via `inspect.signature` que falha se os três conjuntos de parâmetros divergirem. Custa ~20 linhas e trava a regressão para sempre.

Alternativa considerada e descartada: `**kwargs: Unpack[PlotOptions]` (PEP 692). Elimina a duplicação de verdade, mas proíbe chaves extras -- e a lib depende de repassar kwargs arbitrários ao matplotlib.

### D6 -- Idioma

Código, docstrings, mensagens de erro, CHANGELOG e docs técnicas em **inglês** (alcance internacional, convenção de ecossistema). README com seção ou arquivo `README.pt-BR.md` para o público-alvo brasileiro. Hoje há mistura: `description` do `pyproject` em pt-BR, CHANGELOG em pt-BR, resto em inglês.

---

## Fase 0 -- Fundação de verificação

Precede tudo: sem isso não há como provar que as correções das fases seguintes funcionam.

| # | Tarefa | Onde |
|---|---|---|
| F0.1 | Fixture autouse no conftest raiz: limpar registries de colisão, `reset_config()`, snapshot/restore de `rcParams`, fechar figuras | `tests/conftest.py` |
| F0.2 | Promover os conftests locais de `tests/metrics/` e `tests/settings/` para o raiz (hoje só esses dois módulos são isolados) | `tests/*/conftest.py` |
| F0.3 | Adicionar `pytest-mpl` e baseline de imagens para os kinds principais | `tests/visual/` |
| F0.4 | CI GitHub Actions: matriz Python 3.12/3.13 x pandas 2.2/3.0, backends Agg + pdf | `.github/workflows/ci.yml` |
| F0.5 | Declarar ruff + pyright no grupo dev (hoje só `pytest`) | `pyproject.toml:23-26` |
| F0.6 | Teste de vazamento: N plots + `gc.collect()` deve deixar 0 Figures/Axes vivos | `tests/test_lifecycle.py` |

**Ordem do baseline visual**: capturar as imagens de referência **antes** das correções da Fase 3. Cada fix de rendering então atualiza baselines específicos, e o diff vira evidência revisável do que mudou visualmente. Capturar depois esconderia exatamente o que se quer demonstrar.

**Commit**: `test: add state isolation, visual regression baseline and CI matrix`

---

## Fase 1 -- Cidadania de biblioteca

A frente de maior impacto. São os problemas que geram issues nos primeiros dias após o lançamento.

| # | Tarefa | Achado | Onde |
|---|---|---|---|
| F1.1 | Figura fora do pyplot (D1); `PlotResult.close()` + suporte a `with`; `show()` faz o handoff | 2.2, A2-1 | `pipeline.py:41`, `result.py` |
| F1.2 | `theme.context()` via `rc_context` (D2); remover `theme.apply()` | 2.1, A2-6 | `theme.py:37-72`, `pipeline.py:38` |
| F1.3 | Quebrar o ciclo do collision registry: guardar referência fraca ao artist ou limpar em `resolve_collisions` | A2-1 | `collision/_registry.py:16-20` |
| F1.4 | Cache de fonte por caminho+nome; parar de zerar `self._font` a cada `apply()`; deduplicar `addfont` | A2-8 | `theme.py:39`, `fonts.py:34` |
| F1.5 | Renderer garantido pelo canvas próprio (consequência de D1); remover os `type: ignore` de `get_renderer` | 1.6, A2-2 | `_engine.py:68,97,132,162`, `tick_rotation.py:17` |
| F1.6 | Migrar loguru -> `logging` stdlib (D3); remover a dependência | 6.4, D3 | todo `src/`, `_logging.py` |
| F1.7 | Hierarquia `ChartKitWarning` (D4) e conversão dos avisos user-facing | 6.1, A2-19 | novo `warnings.py` |
| F1.8 | `_handler_ids` global -> encapsular em objeto de estado | 2.7 | `_logging.py:18` |
| F1.9 | `bbox_inches='tight'` configurável; documentar o `mkdir` implícito | 6.5 | `saving.py:26-31` |
| F1.10 | Documentar explicitamente os efeitos de import (accessor pandas, enhancers) | 2.6 | README + `docs/contributing/internals.md` |

**Avisos a converter em F1.7** (todos hoje invisíveis por padrão):

- `DataMutationWarning`: colunas não-numéricas descartadas ([_validation.py:261-265](src/chartkit/transforms/_validation.py:261)), spikes substituídos ([temporal.py:536-537](src/chartkit/transforms/temporal.py:536)), `inf` -> NaN em `sanitize_result`.
- `InferenceWarning`: fallback de janela do `accum` ([temporal.py:164-171](src/chartkit/transforms/temporal.py:164)), banda de Bollinger com períodos insuficientes.
- `RenderingWarning`: unidades conflitantes ([compose.py:84](src/chartkit/composing/compose.py:84)), gráfico de barras ilegível ([bar.py:71,111](src/chartkit/charts/enhancers/bar.py:71)), highlight pulado ([markers.py:180,185](src/chartkit/overlays/markers.py:180)), fonte não encontrada ([fonts.py:38,41](src/chartkit/styling/fonts.py:38)), params de métrica ignorados ([registry.py:128](src/chartkit/metrics/registry.py:128)), TOML ilegível ([loader.py:35](src/chartkit/settings/loader.py:35)), `vband` invertido ([vband.py:34](src/chartkit/overlays/vband.py:34)).

**Verificação**: rodar N plots e assertar que `plt.rcParams` volta idêntico ao estado inicial; `gc.collect()` deixa 0 figures; `matplotlib.use("pdf")` + plot com highlight não levanta.

**Commits**: um por bloco lógico -- `refactor(figure)`, `refactor(theme)`, `refactor(logging)`, `feat(warnings)`.

---

## Fase 2 -- Congelamento da API

**Fazer antes da 0.1.0.** Depois de publicado, cada item destes vira breaking change.

| # | Tarefa | Achado | Onde |
|---|---|---|---|
| F2.1 | `layer()` passa a ter a mesma ordem posicional de `plot()`: `layer(x, y, *, kind=...)` | 3.1 | `accessor.py:224`, `transforms/accessor.py:232` |
| F2.2 | Adicionar `figsize` a `plot()` (hoje só `compose()` tem; `create_figure` já suporta) | 3.2 | `engine.py:48`, `pipeline.py:29` |
| F2.3 | Adicionar `decimals` a `compose()`, `Layer` e às duas fachadas de accessor | 3.3, 3.9, A2-24 | `compose.py:92`, `layer.py`, ambos accessors |
| F2.4 | Teste de paridade de assinatura (D5) | D5 | `tests/test_api_parity.py` |
| F2.5 | `ChartKind` como `Literal[...] | str` para dar autocomplete sem fechar a extensibilidade | 5.1 | `engine.py:36` |
| F2.6 | Validar `highlight`/`units`/`kind` na criação do `Layer`, não no render | 3.4, 3.5 | `layer.py:84-95` |
| F2.7 | `validate_kind` com allowlist real (hoje `kind='clear'` e `kind='set_title'` passam) | 3.8 | `renderer.py:184-188` |
| F2.8 | Alinhar `KindCaps` ao comportamento: `barh` declara `highlight=True` mas sempre descarta | 3.6 | `_classification.py:51`, `bar.py:241` |
| F2.9 | Normalizar `color`/`zorder` entre enhancers; `alpha` do `area` configurável | 3.7 | `pie.py:44`, `stem.py`, `statistical.py`, `area.py` |
| F2.10 | Type hints públicos com os `Literal` que a validação já usa (`horizon`, `freq`, `method`) | A2-25 | `transforms/accessor.py:42-148` |
| F2.11 | Documentar que `compose()` usa o X apenas da primeira camada | 3.10 | `compose.py:175-181` |
| F2.12 | `normalize(base=)` aceitar `float` (hoje `PositiveInt` impede rebase para 1.0) | A2-28 | `_validation.py:112` |
| F2.13 | Documentar a assimetria de sinal de `periods` entre `diff` e `variation`/`annualize` | A2-29 | `_validation.py:86,119` |

**Commit**: `feat(api)!: freeze public signatures before 0.1.0` (breaking, documentar no CHANGELOG).

---

## Fase 3 -- Correção de bugs

### 3A -- Rendering

| # | Bug | Achado | Onde |
|---|---|---|---|
| F3.1 | Highlight na coordenada errada: `add_highlight` sem `x=` usa o label do índice | 1.1 | `renderer.py:155-161`, `area.py:47`, `stairs.py:47`, `stem.py:47` |
| F3.2 | Highlight quebra com índice duplicado (`idxmax` -> Series -> `np.isfinite` estoura) | A2-4 | `markers.py:57-64,207` |
| F3.3 | Coluna X reincluída em Y quando `x` é numérica e `y=None` | 1.4 | `extraction.py:61-69` |
| F3.4 | Tick formatting temporal aplicado a kinds não temporais (`hist`, `ecdf`, `pie`, `boxplot`) | 1.3 | `tick_formatting.py:184-254` |
| F3.5 | `stairs` sem `edges` joga o eixo para 0..n mas o pipeline segue tratando como temporal | 1.2 | `stairs.py:36` |
| F3.6 | Colisão resolvida antes de `finalize_chart` alterar limites/rotação/margem | 1.5 | `engine.py:155-175`, `compose.py:199-219` |
| F3.7 | `sort` do bar/barh é no-op em eixo datetime/numérico -- validar ou avisar | 1.7 | `bar.py:116-119,214-217` |
| F3.8 | `y_origin='auto'` com série constante gera `set_lim(v, v)` -> warning que vira erro sob `-W error` | 1.8 | `_helpers.py:142-147` |
| F3.9 | `xlim=("2024","2025")` vira float 2024.0 em eixo de datas (coerção tenta `float` antes de data) | 1.9 | `plot_validation.py:57-62` |
| F3.10 | Reuso de `ChartingPlotter` corrompe o `PlotResult` anterior | 1.10 | `engine.py:131-132,181` |
| F3.11 | `normalize_highlight` levanta `TypeError` fora da hierarquia `ChartKitError` | 1.11 | `highlight.py:31-38` |
| F3.12 | `tick_rotation=True` aceito como ângulo (`isinstance(True, int)`) | 1.12 | `tick_rotation.py:110` |
| F3.13 | `resolve_color` com paleta vazia -> `ZeroDivisionError` | 1.15 | `_helpers.py:73` |
| F3.14 | `y=["a","a"]` faz `ctx.y_data[col]` devolver DataFrame e quebra os enhancers | 1.16 | `extraction.py:77` |
| F3.15 | `_coerce_datetime_index` reinterpreta índice numérico como nanossegundos | 1.13 | `_helpers.py:180-193` |
| F3.16 | `is_categorical_index` retorna `True` para índice object vazio | 1.14 | `_helpers.py:86-87` |

Notas de implementação:
- **F3.6** é o mais estrutural: exige mover `resolve_collisions` para depois de `finalize_chart`, ou dividir `finalize_chart` em pré-colisão (geometria) e pós-colisão (decorations). O código já reconhece o problema no comentário do passo 9 do `engine.py`.
- **F3.4/F3.5** pedem que `finalize_chart` receba a informação de que o eixo X não é temporal para aquele kind -- o `KindCaps.group` (hoje morto, ver F6.1) é o lugar natural para isso.

### 3B -- Transforms

| # | Bug | Achado | Onde |
|---|---|---|---|
| F3.17 | `despike(method="interpolate")` interpola a série inteira e imputa NaNs genuínos do input | A2-5 | `temporal.py:542-544` |
| F3.18 | `despike` com janela centrada compara bordas a vizinhança unilateral -> falsos spikes nas extremidades | A2-22 | `temporal.py:508-513` |
| F3.19 | `resample` pula `validate_numeric`/`sanitize_result` -- foge do contrato dos demais | A2-10 | `temporal.py:597-615` |
| F3.20 | `normalize(base_date=)` vaza `TypeError`/`InvalidIndexError` crus do pandas | A2-9 | `temporal.py:262` |
| F3.21 | `zscore` diagnostica "constant data, std=0" mesmo quando a causa é `window > len(data)` | A2-17 | `temporal.py:437-442` |
| F3.22 | `accum` cai para janela 12 quando `infer_freq` falha, independentemente da granularidade real | A2-18 | `temporal.py:164-171` |

### 3C -- Overlays, formatters e decorations

| # | Bug | Achado | Onde |
|---|---|---|---|
| F3.23 | `footer_format` do TOML com chave desconhecida -> `KeyError` no meio do `plot()` | A2-11 | `footer.py:26-33` |
| F3.24 | `human_readable_formatter` com `suffixes` vazio -> `IndexError`; falta `min_length` no schema | A2-12 | `formatters.py:89-93`, `schema.py:333` |
| F3.25 | `points_formatter(decimals=0)` trunca via `int(x)`: eixo 0-1 vira `['0','0','0','0','1']` | A2-20 | `formatters.py:134-136` |
| F3.26 | `MM12` com `min_periods=1`: os 11 primeiros pontos são médias de 1-11 amostras com legenda "MM12" | A2-16 | `schema.py:230`, `moving_average.py:37`, `std_band.py:54` |
| F3.27 | `vband` com string inválida levanta `ValueError` do pandas em vez de `ValidationError` | A2-27 | `vband.py:30-31` |
| F3.28 | `std_band_full_format` só recebe `deviations`; `{window}` no template dá `KeyError` | A2-27 | `std_band.py:69` |

**F3.26 merece decisão de produto**: mudar o default para `min_periods=None` (janela cheia) torna a média móvel honesta com o rótulo, ao custo de 11 pontos iniciais vazios. Para uma lib voltada a research houses, honestidade visual vale mais. É breaking, então entra aqui e não depois.

**Commits**: `fix(rendering)`, `fix(transforms)`, `fix(overlays)` -- separados, cada um revertível.

---

## Fase 4 -- Estado global e configuração

| # | Tarefa | Achado | Onde |
|---|---|---|---|
| F4.1 | `MetricRegistry`: guard contra sobrescrita silenciosa, `unregister()`, `reset_to_builtins()` | 2.3, A2-13 | `registry.py:46,77,192-194` |
| F4.2 | `ChartRenderer.register_enhancer`: mesma proteção contra sobrescrita | 2.3 | `renderer.py:46` |
| F4.3 | Remover o `ClassVar _toml_data` -- passar TOML por instância de settings source | 2.5, A2-14 | `schema.py:407`, `loader.py:128,168` |
| F4.4 | `ConfigLoader`: mover leituras/escritas de `_project_root*` para dentro do lock | A2-15 | `loader.py:132-162` |
| F4.5 | Collision registry: documentar como não-thread-safe ou adicionar lock | 2.4 | `collision/_registry.py` |
| F4.6 | Opt-out da descoberta automática de config (`CHARTKIT_NO_AUTO_CONFIG`) | 6.6, A2-31 | `discovery.py:39-56` |
| F4.7 | Corrigir doc de precedência: Windows usa `%APPDATA%`, e env vars não aparecem na cadeia documentada | A2-26 | `settings/__init__.py:3-4`, `discovery.py:66-72` |
| F4.8 | Trocar `cachetools` por `functools.lru_cache` -- remove dependência | A2-30 | `discovery.py:10,29,38` |

**Commit**: `refactor(state): protect registries and config from cross-plot leakage`

---

## Fase 5 -- Performance da colisão

Medido: scatter com 200 pontos leva **22,25s** com `collision=True` contra 0,19s sem. Com 1000 pontos não termina em 70s. A mesma série como `line` leva 0,16s.

Causa: `_path_from_collection` cria um Path por ponto ([_obstacles.py:145-175](src/chartkit/_internal/collision/_obstacles.py:145)), e `intersects` varre todos os paths -- dentro de `_position_is_free`, por candidato (~28), por label, por iteração (até 50).

| # | Tarefa | Onde |
|---|---|---|
| F5.1 | Prefiltro por bbox agregado antes do teste path-a-path (rejeição barata) | `_obstacles.py:45-58` |
| F5.2 | Para `Collection` acima de um limiar de pontos, colapsar para grade de ocupação em vez de N paths | `_obstacles.py:145-175` |
| F5.3 | Early-exit no loop de candidatos assim que uma posição livre é encontrada | `_engine.py:232-301` |
| F5.4 | Auto-desabilitar colisão acima de um limiar de artists, com `RenderingWarning` | `_engine.py` |
| F5.5 | Benchmark de regressão no CI (line/scatter/bar com 100/1000/10000 pontos) | `tests/perf/` |

**Commit**: `perf(collision): bbox prefilter and occupancy grid for large collections`

---

## Fase 6 -- Limpeza

| # | Tarefa | Achado | Onde |
|---|---|---|---|
| F6.1 | `KindCaps.group`/`AxisGroup`: usar em F3.4 (decidir eixo temporal) ou remover | 4.1 | `_classification.py:18,27-33` |
| F6.2 | Remover `FORMATTERS` importado sem uso | A2-23 | `engine.py:11` |
| F6.3 | Remover parâmetro `renderer` não usado em toda a cadeia do collision | A2-23 | `_obstacles.py:45-47,56-58,145-147` |
| F6.4 | Remover campo `_artist` armazenado e nunca lido | A2-23 | `_obstacles.py:19,41` |
| F6.5 | Remover `self._ax` atribuído e nunca lido | 1.10 | `engine.py:46,132` |
| F6.6 | Unificar `bar`/`barh` (barh perdeu o warning de legibilidade e o `detect_bar_width`) | 4.4 | `bar.py:32-146,149-242` |
| F6.7 | Consolidar `_ALIASES` e `resolve_kind_alias` num caminho só | 4.2 | `renderer.py:48`, `_classification.py:74` |
| F6.8 | Avaliar remoção do `Saveable`/`_ComposePlotter` -- `PlotResult` já tem `fig` | 4.3 | `result.py:14-15,31`, `compose.py:38-45` |
| F6.9 | Remover `patch_artist` get com default inalcançável | 4.5 | `statistical.py:36-39` |
| F6.10 | Trocar `assert` de módulo por teste (removido sob `python -O`) | 4.6 | `formatting.py:30-32` |
| F6.11 | Mover `_infer_highlight_style` para fora do loop | 4.7 | `renderer.py:163-171` |
| F6.12 | Anotar `**kwargs: Any` nos enhancers de barra (quebram o `Enhancer` Protocol) | 5.2 | `bar.py:39,156`, `stacked_bar.py:36` |
| F6.13 | Anotações de retorno faltantes | 5.3 | `formatting.py:35`, `theme.py:21`, `registry.py:36` |
| F6.14 | `spec: str | object` -> `str | MetricSpec` (o `hasattr(spec,"name")` casaria com `pd.Series`) | 5.4 | `_classification.py:100,106` |
| F6.15 | Docstrings de módulo ausentes (`result.py`, `accessor.py`, `markers.py`, 11 enhancers) | 5.5 | vários |
| F6.16 | Documentar que boxplot/violinplot ignoram `x` silenciosamente | 5.6 | `statistical.py:17-75` |
| F6.17 | Ordem de imports fora da convenção | A2-32 | `collision/_debug.py:13-15` |
| F6.18 | `_ipython_display_` no-op não renderiza em backend não-inline | 6.8 | `result.py:61-63` |

**Commit**: `chore: remove dead code and complete type annotations`

---

## Fase 7 -- Packaging e lançamento

| # | Tarefa | Achado |
|---|---|---|
| F7.1 | **Verificar disponibilidade do nome `chartkit` no PyPI** antes de qualquer outra coisa desta fase | -- |
| F7.2 | Adicionar `LICENSE` (bloqueador absoluto) | 6.7, A2-7 |
| F7.3 | Metadados: `license`, `authors`, `classifiers`, `keywords`, `project.urls` | 6.7, A2-7 |
| F7.4 | Criar `src/chartkit/py.typed` + incluir no build (sem isso os type hints são invisíveis -- PEP 561) | 6.7, A2-7 |
| F7.5 | Declarar `pydantic` explicitamente (importado direto, hoje vem por transitividade) | A2-7 |
| F7.6 | Validar ou estreitar `pandas>=2.2` -- lock está em 3.0.0 e o suporte a 2.2 nunca foi testado | A2-21 |
| F7.7 | Unificar idioma conforme D6; traduzir `description` e CHANGELOG | 6.7 |
| F7.8 | `examples/` + galeria visual nos docs -- para uma lib de tema corporativo é o principal argumento de venda | -- |
| F7.9 | Workflow de release com trusted publishing + `twine check` | -- |
| F7.10 | Testar instalação limpa do wheel em venv virgem (import, accessor registrado, plot básico) | -- |

**Commit**: `build: complete distribution metadata for PyPI release`

---

## Matriz de rastreabilidade

Mapeia cada achado da auditoria para a tarefa que o resolve. `A1-x` = auditoria de rendering, `A2-x` = auditoria de internals.

### Severidade alta

| Achado | Descrição | Tarefa |
|---|---|---|
| A1-1.1 / A2-4 | Highlight sem `x=` e com índice duplicado | F3.1, F3.2 |
| A1-1.2 | `stairs` desalinha o eixo X | F3.5 |
| A1-1.3 | Ticks temporais em eixo não temporal | F3.4 |
| A1-1.4 | Coluna X reincluída em Y | F3.3 |
| A1-1.5 | Colisão antes da geometria final | F3.6 |
| A1-1.6 / A2-2 | Quebra em backends não-Agg | F1.5 (via D1) |
| A1-2.1 / A2-6 | `rcParams` globais mutados | F1.2 (via D2) |
| A1-2.2 | Figuras nunca fechadas | F1.1 (via D1) |
| A2-1 | Collision registry retém Axes/Figures | F1.3 |
| A2-3 | Custo explosivo com scatter | F5.1-F5.4 |
| A2-5 | `despike` interpola NaNs genuínos | F3.17 |
| A1-3.1 | Ordem posicional `plot` vs `layer` | F2.1 |
| A1-3.2 | `figsize` só em `compose` | F2.2 |
| A1-3.3 | `decimals` só em `plot` | F2.3 |
| A1-6.1 / A2-19 | Avisos invisíveis por padrão | F1.7 (via D4) |
| A2-7 | Metadados de publicação ausentes | F7.2-F7.5 |

### Severidade média

| Achado | Descrição | Tarefa |
|---|---|---|
| A1-1.7 | `sort` no-op em eixo datetime | F3.7 |
| A1-1.8 | `y_origin='auto'` com série constante | F3.8 |
| A1-1.9 | `"2024"` como float | F3.9 |
| A1-1.10 | Reuso de `ChartingPlotter` | F3.10, F6.5, F6.8 |
| A1-1.11 | `TypeError` fora da hierarquia | F3.11 |
| A1-1.12 | `tick_rotation=True` | F3.12 |
| A1-2.3 / A2-13 | Registries de classe sem proteção | F4.1, F4.2 |
| A1-2.4 | Collision state sem lock | F4.5 |
| A1-2.5 / A2-14 | `_toml_data` ClassVar | F4.3 |
| A1-2.6 | Efeitos colaterais de import | F1.10 |
| A1-3.4 / A1-3.5 | `Layer` pula validação | F2.6 |
| A1-3.6 | `barh` declara highlight que descarta | F2.8 |
| A1-3.7 | `color`/`zorder` inconsistentes | F2.9 |
| A1-3.8 | `validate_kind` aceita qualquer método de `Axes` | F2.7 |
| A1-4.1 | `KindCaps.group` nunca lido | F6.1 |
| A1-5.1 | `ChartKind = str` | F2.5 |
| A1-5.2 | `**kwargs` sem anotação | F6.12 |
| A1-5.3 | Retornos sem anotação | F6.13 |
| A1-6.4 | `loguru` obrigatória | F1.6 (via D3) |
| A1-6.5 | `save()` com `bbox_inches` fixo | F1.9 |
| A1-6.6 / A2-31 | Descoberta de config varre o FS | F4.6 |
| A2-8 | `fontManager` cresce | F1.4 |
| A2-9 | `normalize` vaza exceções pandas | F3.20 |
| A2-10 | `resample` foge do contrato | F3.19 |
| A2-11 | `footer_format` -> `KeyError` | F3.23 |
| A2-12 | `suffixes` vazio -> `IndexError` | F3.24 |
| A2-15 | `ConfigLoader` fora do lock | F4.4 |
| A2-16 | `MM12` com `min_periods=1` | F3.26 |
| A2-17 | `zscore` diagnostica errado | F3.21 |
| A2-18 | `accum` fallback silencioso | F3.22 |
| A2-20 | `points_formatter` trunca | F3.25 |
| A2-21 | Faixa de pandas não testada | F0.4, F7.6 |
| A2-22 | `despike` assimétrico nas bordas | F3.18 |

### Severidade baixa

| Achado | Descrição | Tarefa |
|---|---|---|
| A1-1.13 | Índice numérico como nanossegundos | F3.15 |
| A1-1.14 | `is_categorical_index` com índice vazio | F3.16 |
| A1-1.15 | Paleta vazia -> `ZeroDivisionError` | F3.13 |
| A1-1.16 | Colunas Y duplicadas | F3.14 |
| A1-2.7 | `_handler_ids` global | F1.8 |
| A1-3.9 / A2-24 | `decimals` ausente nas fachadas | F2.3, F2.4 |
| A1-3.10 | `compose` usa X da primeira camada | F2.11 |
| A1-4.2 | `_ALIASES` redundante | F6.7 |
| A1-4.3 | `Saveable` desnecessário | F6.8 |
| A1-4.4 | Duplicação bar/barh | F6.6 |
| A1-4.5 | `patch_artist` sempre-verdadeiro | F6.9 |
| A1-4.6 | `assert` de módulo | F6.10 |
| A1-4.7 | `_infer_highlight_style` no loop | F6.11 |
| A1-5.4 | `spec: str | object` | F6.14 |
| A1-5.5 | Docstrings de módulo ausentes | F6.15 |
| A1-5.6 | `x` ignorado sem nota | F6.16 |
| A1-6.8 | `_ipython_display_` no-op | F6.18 |
| A2-23 | Dead code diverso | F6.2-F6.5 |
| A2-25 | Type hints públicos fracos | F2.10 |
| A2-26 | Doc de precedência divergente | F4.7 |
| A2-27 | Exceções cruas em overlays | F3.27, F3.28 |
| A2-28 | `normalize(base=)` só inteiro | F2.12 |
| A2-29 | Sinal de `periods` inconsistente | F2.13 |
| A2-30 | `cachetools` desnecessária | F4.8 |
| A2-32 | Ordem de imports | F6.17 |
| A2-nota | Testes sem isolamento de estado | F0.1, F0.2 |

---

## Sequenciamento e dependências

```
F0 (verificação)
 └─> F1 (cidadania) ──> F5 (performance)
      └─> F2 (API freeze)
           └─> F3 (bugs) ──> F6 (limpeza)
                └─> F4 (estado/config)
                     └─> F7 (packaging) ──> 0.1.0
```

Restrições de ordem que importam:

- **F0 antes de tudo**: sem isolamento de estado nos testes, correções de estado global não são verificáveis.
- **F1 antes de F5**: a decisão D1 (canvas próprio) muda como o renderer é obtido, que é exatamente o hot path da colisão.
- **F2 antes de F3**: corrigir bugs em assinaturas que ainda vão mudar gera retrabalho.
- **F3.4 depende de F6.1**: a decisão sobre `KindCaps.group` define como o pipeline sabe que um eixo não é temporal.
- **F7 por último**, mas **F7.1 (nome no PyPI) primeiro de tudo** -- se o nome estiver ocupado, muda o escopo do rebranding.

---

## Estimativa relativa

| Fase | Peso | Observação |
|---|---|---|
| F0 | Médio | CI e baseline visual são setup, não design |
| F1 | **Alto** | D1 e D2 são refactors estruturais que tocam todo o pipeline |
| F2 | Médio | Mudanças mecânicas, mas exigem atualizar docs e testes |
| F3 | **Alto** | 28 bugs, alguns (F3.6) com implicação arquitetural |
| F4 | Baixo | Localizado em `settings/` e nos registries |
| F5 | Médio | Exige medição antes e depois |
| F6 | Baixo | Mecânico |
| F7 | Baixo | Metadados e workflow |

O caminho crítico é **F1 + F3**. As demais fases são majoritariamente mecânicas.
