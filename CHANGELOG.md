# Project Changelog

## [2026-08-05 03:48]
### Changed
- **Erros de pyright: 174 -> 51**: duas anotacoes que estavam de fato erradas respondiam por 123 deles. As factories de colisao declaravam `Artist` mas chamavam metodos de `Line2D`, `Patch` e `Collection`; e `Path.vertices` era indexado sem `np.asarray`, entao os stubs viam `ArrayLike`. O que resta e atrito com os stubs de matplotlib e pandas (`Figure | SubFigure`, `Timestamp | NaTType`), que pede `cast()` e nao tipo melhor
- **`barh` avisa sobre legibilidade**: `bar` avisa desde sempre acima de `bars.warning_threshold`; a versao horizontal nunca avisou
- **`_infer_highlight_style` sai do laco**: era recalculado por coluna, revarrendo os patches que as colunas anteriores tinham adicionado. A resposta -- se o kind desenha patches -- ja fica decidida na primeira
- **`**kwargs: Any` nos enhancers de barra**: sem a anotacao eles nao satisfaziam o Protocol `Enhancer`
- **`_extract_metric_name(spec: str | MetricSpec)`**: era `str | object`, e o `hasattr(spec, "name")` la dentro casaria com um `pd.Series`

### Added
- **Docstrings de modulo em 13 arquivos**: os 11 enhancers, `accessor.py` e `markers.py`
- **Teste de cobertura do dispatch de formatters**: era um `assert` de modulo, que `python -O` remove -- justamente nas execucoes onde a falha custa mais

### Removed
- **`kwargs.get("patch_artist", True)` no boxplot**: o `setdefault` logo acima torna o default inalcancavel

## [2026-08-05 03:02]
### Performance
- **Colisao em scatter: 45s -> 0,6s com 100 pontos**: `_PathObstacle` chamava `Path.get_extents()` a cada teste de intersecao -- por path, por candidato, por label, por iteracao. Em scatter cada marcador e um circulo de Beziers, e `get_extents()` resolve os extremos exatos com um root-find polinomial por segmento. O profile mostrou 9,8s de 9,8s ali. Os bounding boxes agora saem dos pontos de controle e sao calculados uma vez na construcao
- **Hull agregado por obstaculo**: uma comparacao descarta o obstaculo inteiro quando o label esta longe dele; so os paths que realmente se sobrepoem chegam ao `intersects_bbox()`
- Medido: 1.000 pontos de 12,9s para 0,38s; 10.000 pontos de 75s para 2,0s. `plot` (linha) permanece inalterado

### Added
- **`tests/collision/test_collision_perf.py`**: expressa o teto como multiplo do mesmo grafico com a engine desligada, para continuar valendo em maquina mais lenta

### Not done
- **Grade de ocupacao para Collections grandes (F5.2)**: implementada e medida contra a alternativa. Depois da correcao dos extents ela perde de forma consistente ate em 10.000 pontos (3,96s contra 3,58s) -- a primeira medicao favoravel era ruido. Removida
- **Early-exit no laco de candidatos (F5.3)**: contradiz a selecao por custo que entrou depois do plano ser escrito. O solver precisa avaliar todos os candidatos validos para escolher o de menor custo; parar no primeiro livre volta ao comportamento greedy
- **Auto-desabilitar acima de um limiar (F5.4)**: era valvula de seguranca para o caso patologico, que deixou de existir

## [2026-08-05 02:14]
### Changed
- **BREAKING -- registrar nome ja existente levanta `RegistryError`**: `MetricRegistry.register` e `ChartRenderer.register_enhancer` sobrescreviam em silencio, entao duas bibliotecas registrando `'ma'` se anulavam sem aviso. Passe `replace=True` para sobrescrever de proposito
- **BREAKING -- `MetricRegistry.clear()` removido**: esvaziava o registry inteiro, deixando `'ath'` e `'ma'` indefinidos. Substituido por `reset_to_builtins()`, que descarta so o que o usuario registrou
- **`_toml_data` deixa de ser `ClassVar`**: o TOML mesclado vivia em estado de classe compartilhado por todo loader e toda thread -- dois configs construidos ao mesmo tempo liam os arquivos um do outro. Agora viaja como init kwarg, consumido em `settings_customise_sources` antes da validacao
- **`ConfigLoader.project_root` le e escreve sob o lock**: `reset()` limpa os dois campos, e um leitor sem sincronizacao podia ver a flag de resolvido ligada com o valor ja apagado
- **Erro de configuracao invalida vira `ValidationError` do chartkit**: o `ValidationError` do pydantic vazava do `get_config()`, sem indicar que a causa era um setting

### Added
- **`MetricRegistry.unregister(name)` e `reset_to_builtins()`**: o conftest da suite alcancava `_metrics` diretamente por falta de API publica
- **`CHARTKIT_NO_AUTO_CONFIG`**: desliga a descoberta automatica de TOML. Sem isso, a lib le qualquer `pyproject.toml` acima do diretorio de trabalho -- surpreendente para uma aplicacao que quer honrar apenas os proprios settings

### Removed
- **Dependencia `cachetools`**: existia para dar um lock ao cache de `find_project_root`. A justificativa registrada -- "`lru_cache` nao e thread-safe" -- era imprecisa: o CPython protege a contabilidade interna dele. O que nao e garantido e execucao unica por chave sob concorrencia, e para uma varredura de filesystem sem efeito colateral isso custa no maximo um `stat()` redundante

## [2026-08-05 01:26]
### Fixed
- **`points_formatter` truncava em vez de arredondar**: `int(x)` corta em direcao ao zero, entao o label do maximo de uma serie que chega a 110,85 dizia `110`. Num grafico cuja funcao e destacar o extremo, isso subestimava a maxima em quase um ponto inteiro. A snapshot `test_highlight_modes_snapshot` registra a correcao (`"110"` -> `"111"`)
- **`footer_format` com placeholder desconhecido**: `str.format` levantava `KeyError` cru no meio do `plot()`, nomeando a chave mas nao onde ela mora. Agora e `ValidationError` citando o setting e os placeholders validos
- **`std_band_full_format` nao aceitava `{window}`**: o ramo full-series passava so `deviations`, entao um template que mencionasse `{window}` -- valido no ramo rolling -- morria com `KeyError`. Os dois ramos recebem os mesmos campos
- **`vband` com data ilegivel**: vazava `DateParseError` do pandas, fora da hierarquia `ChartKitError`
- **`formatters.magnitude.suffixes` vazio**: o formatter indexa a ultima entrada como teto, entao a lista vazia era um `IndexError` esperando um numero grande o suficiente. Rejeitado no schema via `min_length=1`

### Pending decision
- **F3.26 -- `min_periods=1` na media movel**: os 11 primeiros pontos de uma `MM12` sao medias de 1 a 11 amostras, com a legenda dizendo `MM12`; o mesmo vale para `std_band`. Mudar o default de `lines.moving_avg_min_periods` para a janela cheia torna a linha honesta com o rotulo, ao custo de 11 pontos iniciais vazios, e e breaking. Aguardando decisao

## [2026-08-05 00:41]
### Fixed
- **`despike(method='interpolate')` imputava NaNs do proprio input**: `interpolate()` preenche toda lacuna que encontra, entao os NaNs que o chamador forneceu voltavam como valores inventados. Agora so as posicoes que o filtro zerou sao preenchidas
- **`resample` fora do contrato dos demais transforms**: nao passava por `validate_numeric` nem `sanitize_result`, entao colunas de texto atravessavam intactas e infinitos sobreviviam. A checagem de `DatetimeIndex` vem antes da validacao numerica, para nao avisar sobre um indice que sera rejeitado logo em seguida
- **`normalize(base_date=)` vazava erros crus do pandas**: `get_indexer` levanta `TypeError` em indice nao-temporal e `InvalidIndexError` em indice duplicado -- nenhum dos dois e `ChartKitError`
- **`zscore` culpava dado constante**: o log dizia `constant data, std=0` mesmo quando a causa era `window` maior que a serie, mandando o leitor investigar os dados em vez da chamada
- **`accum` usava janela mensal em dado diario**: `pd.infer_freq` exige indice perfeitamente regular, o que nenhuma serie de mercado tem -- um feriado basta. O fallback caia na `accum_window` da config (12), acumulando 12 *dias*

### Added
- **`estimate_freq()` em `_internal/frequency.py`**: estima frequencia pelo espacamento mediano entre observacoes, para quando `pd.infer_freq` desiste. Distingue `B` de `D` pela presenca de fins de semana no indice -- 252 contra 365 periodos ao ano e diferenca grande demais para chutar. Usado apenas no fallback do `accum`; `variation` e `annualize` continuam exigindo frequencia explicita

### Not fixed
- **Falsos spikes nas bordas do `despike` (A2-22)**: a janela centrada e unilateral nas extremidades. Marcacoes nas bordas foram observadas em series com tendencia e ruido, mas nao ficou provado que sejam falsos positivos, e as duas correcoes tentadas regrediram -- exigir janela cheia cega o filtro em series curtas (um spike de 350 num bairro de 100 deixou de ser detectado), e reflexao impar marcou mais bordas ainda. Mantido como esta

## [2026-08-04 23:18]
### Fixed
- **Eixos nao-temporais recebiam formatacao de data**: com `ticks.date_format` configurado -- o uso normal da lib -- `hist`, `ecdf`, `boxplot` e `violinplot` rotulavam o eixo X com `"Jan/1970"`, porque o `finalize_chart` aplicava `DateFormatter` sem olhar o que o kind poe naquele eixo. Agora so o grupo `series` do `KindCaps` recebe locator e formatter de data
- **Colisao resolvida antes da geometria final**: `resolve_collisions` rodava antes do `finalize_chart` aplicar limites, rotacao e margem. Como a resolucao mede sobreposicao em pixels, os labels eram posicionados contra uma geometria que mudava logo depois -- com `ylim` comprimindo os dados, dois labels sobrepunham 46x14 px. As duas etapas trocaram de ordem no `engine` e no `compose`
- **`stairs` descartava as datas**: `ax.stairs(values)` sem `edges` gera `range(n+1)`, jogando o eixo para 0..n. Agora as bordas sao derivadas do x real (datetime ou numerico); indice categorico mantem o comportamento posicional
- **Highlight ancorado no rotulo do indice**: `add_highlight` era chamado sem `x=` no caminho generico e nos enhancers de `area`, `stem` e `stairs`, posicionando o marcador pelo label em vez da coordenada
- **`idxmax`/`idxmin` com indice duplicado**: devolviam Series e estouravam em `np.isfinite`. Trocado por busca posicional via `argmax`/`argmin`
- **Coluna X reincluida em Y**: `plot(x='ano')` com `y=None` deixava `ano` no `select_dtypes` e desenhava a coluna contra si mesma
- **`y=['a','a']`**: `df[['a','a']]['a']` devolve DataFrame e quebrava o broadcasting dos enhancers. Agora rejeitado com mensagem clara
- **`xlim=('2023','2024')` em eixo de datas**: a coercao tentava `float` antes de data, virando 2023.0 -- dois milenios longe dos dados. Em eixo temporal a ordem se inverte
- **`sort` em eixo datetime/numerico era no-op**: as barras eram reordenadas mas redesenhadas em suas proprias datas, reproduzindo o grafico original. Agora rejeitado -- ranquear e operacao categorica, e `barh` ja funciona por ser ordinal
- **`y_origin='auto'` com serie constante**: `set_ylim(v, v)` emitia `UserWarning` de transformacao singular, que vira erro sob `-W error`
- **`tick_rotation=True` aceito como angulo**: `isinstance(True, int)` fazia `True` significar 1 grau
- **`normalize_highlight` com valor nao-iteravel**: vazava `TypeError` fora da hierarquia `ChartKitError`
- **Paleta vazia**: `resolve_color` estourava `ZeroDivisionError` no modulo
- **Indice numerico lido como nanossegundos**: `_coerce_datetime_index([2020, 2021])` devolvia 1970-01-01
- **Indice object vazio classificado como categorico**: `all([])` e `True`

### Changed
- **BREAKING -- `PlotResult` nao tem mais o campo `plotter`**: `save()` agora escreve `self.fig`. Antes delegava ao plotter que construiu o grafico, cujo `_fig` era sobrescrito a cada `plot()` -- um `ChartingPlotter` reutilizado fazia o primeiro `PlotResult` salvar a figura do segundo
- **BREAKING -- `ChartingPlotter.save()` removido**: existia so para esse caminho com estado. O dono da figura e o `PlotResult`
- **`Saveable` Protocol e `_ComposePlotter` removidos**: existiam apenas para satisfazer o campo `plotter`

## [2026-08-04 22:02]
### Changed
- **BREAKING -- `layer()` reordenado para espelhar `plot()`**: A ordem posicional passou de `(kind, x, y)` para `(x, y)` com `kind` keyword-only. `layer('data', 'valor')` agora seleciona as mesmas colunas que `plot('data', 'valor')`. Chamadas que passavam `kind` posicionalmente precisam usar `kind=`
- **BREAKING -- `kind` validado contra allowlist**: A validacao aceitava qualquer atributo chamavel de `Axes`; apenas 9 kinds genericos funcionam de fato pela convencao `(x, y_series)`. Metodos com assinatura incompativel (`hlines`, `psd`, `hexbin`) e metodos que nao plotam (`clear`, `set_title`, `twinx`) agora levantam `ValidationError` listando os kinds disponiveis, em vez de vazar um `TypeError` cru do matplotlib
- **BREAKING -- `barh` rejeita `highlight`**: `KindCaps` declarava `highlight=True` mas o enhancer descartava o parametro silenciosamente. A capability foi alinhada ao comportamento -- os marcadores se posicionam contra um eixo vertical de valores, que `barh` nao possui
- **`normalize(base=)` aceita `float`**: Era `PositiveInt`, o que impedia rebasear para `1.0` -- convencao para graficos de indice e multiplo
- **Tipos dos transforms expostos como `Literal`**: `horizon`, `freq`, `method` deixam de ser `str` nas assinaturas publicas (`chartkit.transforms.types`), dando autocomplete e checagem estatica dos valores que os validadores ja exigiam em runtime
- **`tick_freq` anotado como `TickFreq`**: Era `str` nas fachadas, embora `plot_validation` ja restringisse os valores

### Added
- **`decimals` e `figsize` nas fachadas publicas**: `decimals` existia so em `ChartingPlotter.plot`; `figsize` so em `compose()`. Ambos agora aparecem em `plot()` dos dois accessors, e `decimals` tambem no `Layer` -- ao lado do `units` que ele refina, ja que cada eixo e formatado independentemente
- **`FillsConfig`**: `fills.area_alpha` (default `0.3`) e `fills.violin_alpha` (default `0.7`) tornam configuraveis opacidades antes hardcoded nos enhancers
- **`ChartKind` como `Literal | str`**: 24 kinds conhecidos ganham autocomplete sem fechar o tipo para enhancers registrados pelo usuario
- **`tests/test_api_parity.py`**: Compara nome, ordem, default e anotacao entre as tres copias de `plot()` e as duas de `layer()`, e verifica por sentinela que todo parametro aceito chega de fato ao engine. Um parametro que existe na assinatura mas nunca e repassado agora quebra o build
- **Validacao de `highlight` na construcao do `Layer`**: Modos invalidos eram descobertos so no meio do rendering de `compose()`
- **`zorder` aplicado nas wedges de `pie`**: `ax.pie()` nao aceita `zorder`, entao o valor do `RenderContext` era perdido

## [2026-03-22 22:17]
### Added
- **Sistema de classificacao de chart kinds (`_classification.py`)**: Tabela declarativa `KindCaps` define capacidades de cada chart kind (highlight, metrics temporais, composability, axis group). Validacao early-fail em `engine.py`, `create_layer()` e `compose()` bloqueia combinacoes incompativeis antes do rendering
- **Validacao de highlight por kind**: Kinds sem suporte a highlight (stackplot, boxplot, violinplot, hist, ecdf, pie, eventplot) agora rejeitam `highlight=True` com erro claro
- **Validacao de metrics por kind**: Kinds sem suporte a metrics (distribution, aggregation, isolated, event) rejeitam qualquer metrica. Kinds sem suporte temporal rejeitam `ma`, `std_band` e `vband`
- **Validacao de composability**: `compose()` rejeita kinds incompativeis com multi-layer (boxplot, violinplot, hist, ecdf, pie, eventplot) com mensagem descritiva

### Changed
- **`ChartRenderer._ALIASES` referencia `KIND_ALIASES` centralizado**: Source of truth unica para aliases de chart kind, eliminando duplicacao entre renderer e classification

## [2026-03-22 21:11]
### Changed
- **Config renomeado de `charting` para `chartkit`**: TOML discovery agora busca `.chartkit/config.toml` (era `.charting.toml`/`charting.toml`), pyproject.toml usa `[tool.chartkit]` (era `[tool.charting]`), user config em `~/.config/chartkit/` e `%APPDATA%/chartkit/` (era `charting/`). Breaking change -- configs existentes precisam ser migrados manualmente
- **Exemplo de config movido para `.chartkit/config.example.toml`**: Substituiu `charting.example.toml` na raiz do projeto. Novo local segue convencao dotfolder e fica junto ao config do usuario
- **`.gitignore` atualizado**: `.chartkit/config.toml` ignorado para evitar commit acidental de config do usuario

### Removed
- **`charting.example.toml`**: Substituido por `.chartkit/config.example.toml`
- **Suporte a `.charting.toml`/`charting.toml` na raiz**: Discovery simplificado para buscar apenas `.chartkit/config.toml`

## [2026-02-20 11:47]
### Changed
- **Collision: unified artist dispatch via `_classify_artist()`**: Logica duplicada de conversao Artist->_PathObstacle em `_collect_obstacles()` e `_collect_passive_obstacles()` extraida para funcao unica com dispatch estrutural (Collection > Patch > Line > fallback extent)
- **Debug overlay diferencia passive lines de passive shapes**: Obstaculos passivos nao-preenchidos (linhas) agora renderizam com estilo de linha (face transparente, linewidth fino) em vez de estilo shape -- facecolor simplificado para depender apenas de `_filled`
- **Auto-rotation escala para 90 graus quando angulo configurado nao resolve overlap**: `apply_tick_rotation()` com `"auto"` agora aplica o angulo configurado primeiro e, se sobreposicao persistir, escala para 90 graus. Logica de rotacao extraida para helper `_apply_angle()`
- **Moving average e std_band center line promovidos a obstaculos ativos**: `register_passive()` substituido por `register_artist_obstacle(filled=False)` -- linhas de media movel e centro da banda de desvio padrao agora causam repulsao real no collision engine, nao apenas aparecem no debug overlay

### Added
- **Area fills registrados como obstaculos passivos**: `fill_between` PolyCollections do area enhancer agora sao registrados via `register_passive()`, tornando preenchimentos de area visiveis no debug overlay do collision engine

## [2026-02-20 10:44]
### Changed
- **Collision engine: cost-based candidate selection**: Substituido o sistema greedy (primeiro candidato livre vence) por funcao de custo continua com 3 componentes ponderados -- distancia do anchor (w=1.0), preferencia de eixo (w=3.0) e proximidade de borda (w=5.0). O solver agora avalia todos os candidatos validos e escolhe o de menor custo
- **Candidatos proativos em 8 direcoes cardinais**: Novo gerador `_generate_proactive_candidates()` posiciona candidatos em N/NE/E/SE/S/SW/W/NW a multiplas distancias (configuraveis via `candidate_distances`), com normalizacao de diagonais para distancia uniforme
- **Candidatos reativos renomeados**: `_compute_displacement_options()` renomeado para `_generate_reactive_candidates()` -- semantica snap-to-edge preservada como complemento dos candidatos proativos
- **Anchor bboxes snapshot**: `_resolve_all()` agora captura bounding boxes originais antes de qualquer movimento, garantindo que a funcao de custo mede distancia ao ponto de ancoragem real

### Added
- **`CollisionConfig.candidate_distances`**: Tupla de multiplicadores de distancia (em alturas de label) para geracao de candidatos proativos. Default: `(1.0, 1.5, 2.0)`
- **`CollisionConfig.edge_margin_factor`**: Margem de borda como fracao da altura do label. Labels dentro dessa margem recebem penalidade crescente. Default: `1.0`
- **`_edge_proximity_cost()`**: Penalidade linear quando label esta proximo a qualquer borda dos axes -- retorna 0.0 quando seguro, escala ate 1.0 quando tocando a borda
- **`_compute_placement_cost()`**: Funcao de custo unificada combinando distancia normalizada, preferencia de eixo e proximidade de borda
- **Testes para proactive candidates e cost function**: `TestProactiveCandidates` (geracao em 8 direcoes, bounds check, normalizacao diagonal), `TestPlacementCost` (monotonicidade, preferencia de eixo, penalidade de borda), `TestBestCostSelection` (resolucao realista com dois labels sobrepostos)

### Removed
- **`_axis_priority()`**: Substituida pela funcao de custo continua `_compute_placement_cost()` -- o sort discreto por bins de prioridade nao escala para avaliacao multi-criterio
- **Fallback diagonal em `_find_free_position()`**: Eliminado -- candidatos proativos em 8 direcoes ja cobrem diagonais nativamente

## [2026-02-20 02:13]
### Added
- **`_internal/frequency.py`**: Novo modulo compartilhado de deteccao e display de frequencia -- centraliza `FREQ_ALIASES`, `normalize_freq_code()`, `infer_freq()` (antes em `transforms/_validation.py`) e adiciona `FREQ_DISPLAY_MAP` com labels curtos pt-BR (D, DU, S, M, T, A) e `freq_display_label()` para conversao
- **Metricas frequency-aware**: `MetricRegistry.register()` aceita `uses_freq=True` -- metricas marcadas recebem `detected_freq` automaticamente via `MetricRegistry.apply()`, que infere a frequencia uma unica vez e propaga para todas as metricas que precisam
- **Placeholder `{freq}` em labels de metricas**: `moving_average_format` e `std_band_format` agora suportam `{freq}` para exibir a frequencia detectada dos dados (ex: "MM12M" para media movel de 12 meses) -- opt-in via config TOML
- **`draw_debug_overlay()` e `draw_composed_debug_overlay()`**: Funcoes standalone para overlay de debug com geometria atualizada -- chamadas apos `finalize_chart()` para refletir posicao final dos axes (tick rotation, subplots_adjust)

### Changed
- **Debug overlay desacoplado da resolucao de colisao**: `resolve_collisions()` e `resolve_composed_collisions()` nao recebem mais `debug` -- overlay agora e step separado no pipeline (step 9 no engine, step 7 no compose), garantindo que geometria reflete o layout final
- **`infer_freq()` aceita `pd.Index` diretamente**: Alem de DataFrame e Series, simplificando uso no MetricRegistry onde x_data pode ser Index
- **`ma` e `std_band` marcados como `uses_freq=True`**: Labels de media movel e banda de desvio padrao exibem frequencia quando disponivel

### Removed
- **`_infer_freq()` e `_normalize_freq_code()` de `transforms/_validation.py`**: Movidos para `_internal/frequency.py` como `infer_freq()` e `normalize_freq_code()` (API publica do modulo interno)
- **`_ANCHORED_PREFIXES` e `FREQ_ALIASES` de `transforms/_validation.py`**: Movidos para `_internal/frequency.py`
- **Parametro `debug` de `resolve_collisions()` e `resolve_composed_collisions()`**: Substituido por funcoes standalone de overlay

## [2026-02-20 01:07]
### Added
- **Debug logging no pipeline interno**: Instrumentacao completa com `loguru.logger.debug()` nos pontos-chave do fluxo de plotagem -- `extract_plot_data` (x/y/rows), `create_figure` (figsize/grid), `apply_legend` (handles/skip), `finalize_chart` (steps aplicados), `coerce_axis_limits` (conversoes), `apply_tick_formatting` (locator type/freq/format)
- **Validacao de `tick_freq` via Pydantic**: `validate_plot_params()` agora valida `tick_freq` com `TickFreq` Literal type, capturando valores invalidos antes de chegar ao tick engine
- **Validacao de tipo em `tick_rotation`**: Guard defensivo rejeita valores que nao sao `int` nem `"auto"`, com `ValidationError` descritiva
- **Docstrings completas na API publica**: Documentacao Args/Attributes em `ChartingAccessor` (plot, layer, transforms), `TransformAccessor` (plot com signature explicita, layer, transforms), `PlotResult` (save, show, axes, figure), `Layer`, `create_layer()`, `MetricSpec`, `MetricRegistry.apply()`, `ChartingTheme` properties, e todos os 17 config models em `settings/schema.py`
- **`TickFreq` type centralizado**: Novo Literal type em `plot_validation.py` reusado por `tick_formatting.py` e `PlotParamsModel`

### Changed
- **`TransformAccessor.plot()` com signature explicita**: Substituiu `**kwargs` opaco por todos os parametros tipados (x, y, kind, title, units, source, highlight, metrics, legend, xlabel, ylabel, xlim, ylim, grid, tick_rotation, tick_format, tick_freq, collision, debug) -- habilita autocomplete e type checking no IDE
- **`ValidationError` em vez de `ValueError`**: `tick_formatting.py` e `tick_rotation.py` agora usam `chartkit.exceptions.ValidationError` para erros de input invalido, consistente com o resto da library
- **Logging de data extraction movido para `extraction.py`**: Debug log de x/y_columns/rows extraido de `engine.py` para `extract_plot_data()`, onde a logica de extracao realmente vive
- **`_validate_layers()` propaga `tick_freq`**: Validacao de compose agora passa `tick_freq` para `validate_plot_params()`, garantindo mesma validacao do plot direto

## [2026-02-19 23:45]
### Added
- **`_internal/pipeline.py`**: Novo modulo com pipeline steps compartilhados (`create_figure`, `apply_legend`, `finalize_chart`) -- elimina duplicacao entre engine e compose
- **`RenderContext`**: Dataclass frozen em `charts/_helpers.py` que encapsula config, color cycle, user_color, zorder e y_data pre-processado para enhancers
- **`prepare_render_context()` e `resolve_color()`**: Helpers que extraem boilerplate repetido de todos os enhancers (config loading, Series->DataFrame coercion, color resolution)
- **Thread-safety no `ConfigLoader`**: `threading.Lock` com double-checked locking em `configure()`, `reset()` e `get_config()`

### Changed
- **Enhancers unificados via RenderContext**: Todos os 9 enhancers (area, ecdf, eventplot, hist, stacked_bar, stackplot, stairs, statistical, stem) e o `ChartRenderer` agora usam `RenderContext` em vez de repetir config/color/zorder boilerplate individualmente
- **Engine e compose unificados via pipeline**: Steps duplicados (theme.apply, figure creation, tick formatting, tick rotation, axis limits, labels, decorations) extraidos para funcoes compartilhadas em `pipeline.py`
- **`apply_y_origin()` generalizado**: Novo parametro `axis` permite usar a mesma funcao para barras verticais (y) e horizontais (x), eliminando logica duplicada no enhancer barh
- **`compute_bar_offsets()` usado no bar enhancer**: Substituiu calculo inline de offsets por helper ja existente
- **`theme.apply()` reseta font cache**: Invalida `_font` antes de recarregar config, evitando fonte stale apos reconfiguracoes

### Removed
- **`_apply_composed_legend()`** de `compose.py` -- substituida por `apply_legend()` compartilhada
- **`ChartingPlotter._apply_legend()`** de `engine.py` -- substituida pela mesma funcao compartilhada
- **Pipeline steps duplicados**: ~50 linhas de codigo identico removidas entre engine e compose (theme.apply, plt.subplots, grid override, tick formatting, tick rotation, axis limits, labels, title, footer)
- **Logica duplicada de barh origin**: 12 linhas de calculo manual de xlim no enhancer barh, substituidas por `apply_y_origin(axis="x")`

## [2026-02-19 21:21]
### Added
- **Smart tick alignment**: Ticks posicionados nos pontos reais dos dados em vez de boundaries fixas do calendario -- dados trimestrais end-of-quarter (Mar/Jun/Sep/Dec) agora recebem ticks nos meses corretos, sem desalinhamento para Jan/Apr/Jul/Oct
- **Auto-inferencia de tick frequency**: Quando `tick_freq` nao e especificado, `pd.infer_freq()` detecta o padrao temporal dos dados e alinha ticks automaticamente para frequencias esparsas (quarterly, semestral, anual)
- **Phantom tick clipping**: Remove ticks fora do range real dos dados, causados por padding de xlim (comum em bar charts)
- **`coerce_axis_limits()`**: `xlim`/`ylim` agora aceitam strings (`"2024-01-01"`, `"100"`) com conversao automatica para datetime ou float
- **`AxisLimits` type alias**: Tipo semantico para tuplas de limites de eixo com suporte a str/int/float/datetime/Timestamp/None

### Changed
- Tick frequency `"quarter"` agora usa meses end-of-quarter (3,6,9,12) em vez de start-of-quarter (1,4,7,10)
- Tick frequency `"semester"` agora usa meses end-of-semester (6,12) em vez de start (1,7)
- Horizontal alignment de tick labels rotacionados mudou de angle-dependent (right/left) para sempre `center`
- `apply_tick_formatting()` recebe novo parametro `x_data` para posicionamento data-aware de ticks

### Removed
- **`add_right_margin()`**: Funcao removida junto com suas chamadas em engine e compose -- margem direita para highlight labels nao e mais necessaria

## [2026-02-18 22:36]
### Changed
- **Collision engine modularizado**: Modulo monolitico `_internal/collision.py` (877 linhas) dividido em pacote `_internal/collision/` com 4 sub-modulos especializados: `_registry.py` (estado global e registro de artists), `_obstacles.py` (PathObstacle e coleta de obstaculos), `_engine.py` (resolucao de colisoes), `_debug.py` (overlay de debug)
- API publica mantida identica via re-exports no `__init__.py`

## [2026-02-18 21:53]
### Added
- **Fixtures de edge cases financeiros** (`conftest.py`): `irregular_daily_prices` (datas irregulares), `quarterly_rates` (dados trimestrais), `gapped_prices` (precos com NaN gaps) -- cenarios reais problematicos
- **Testes de integracao** (`tests/integration/`): `test_accessor_pipeline.py` e `test_end_to_end.py` para validacao end-to-end do fluxo completo
- **Testes de formatting** (`tests/formatting/`): `test_axis_formatters.py` e `test_highlight.py` em diretorio dedicado
- **Testes de edge cases financeiros** em transforms: dados trimestrais com `variation`, timeseries irregulares, NaN gaps em `drawdown`, taxa -100% em `accum`, multi-column em `normalize`/`zscore`/`drawdown`/`accum`
- **Testes de MetricRegistry.apply** (`test_registry.py`): Validacao de chamada de handlers com ax/data e passagem de parametros

### Changed
- **Suite de testes reescrita**: Reorganizacao completa por dominio de negocio em vez de detalhe de implementacao -- testes focam em comportamento e corretude, nao em type-checking de inputs
- **Nomes de testes descritivos**: Classes e metodos renomeados para expressar intent (`TestAccumKnownValues`, `test_minus_100_rate_zeroes_product`, etc.)
- **Docstrings em todos os testes**: Cada teste documenta o que valida (`"""[1%, 2%, 3%] window=3 -> compound product."""`)
- **Charts tests reestruturados**: Testes individuais por enhancer (`test_area_enhancer.py`, `test_bar_enhancer.py`, `test_stacked_bar_enhancer.py`) + renderer generico (`test_renderer.py`)
- **Collision tests consolidados**: `test_collision_engine.py` substitui `test_collect_obstacles.py` e `test_pos_to_numeric.py`
- **Composing tests reorganizados**: `test_compose_pipeline.py` e `test_layer_validation.py` substituem 6 arquivos separados
- **Settings tests focados**: `test_config_precedence.py` substitui `test_deep_merge.py`, `test_loader.py` e `test_schema.py`
- **Transform tests enxutos**: `test_freq_resolution.py` e `test_input_pipeline.py` consolidam validacao transversal

### Removed
- **41 arquivos de teste antigos** deletados: testes granulares que testavam detalhes de implementacao (input type acceptance, empty raises, internal state access) substituidos por testes focados em comportamento
- **Testes redundantes de input type**: `test_accepts_series`, `test_accepts_dataframe` removidos de todos os transform tests -- testavam coercao do framework, nao logica de negocio
- **Testes de empty raises generico**: Removidos de `accum`, `annualize`, `diff`, `normalize`, `zscore` -- validacao de input vazia e responsabilidade da camada de coercao
- **Diretorios `tests/decorations/`, `tests/engine/`, `tests/internal/`**: Removidos junto com seus `__init__.py`

## [2026-02-18 21:11]
### Added
- **Controles de eixo** (`xlabel`, `ylabel`, `xlim`, `ylim`) em `plot()`, `compose()` e accessor: Controle direto de labels e limites dos eixos sem acessar o matplotlib diretamente
- **Grid per-call** (`grid` parameter): `grid=True/False` em `plot()` e `compose()` habilita/desabilita grid para um grafico especifico, com precedencia sobre config global
- **`GridConfig`** (`settings/schema.py`): Config estruturada substituindo o antigo `grid: bool` -- campos `enabled`, `alpha`, `color`, `linestyle`, `axis` configuraveis via TOML
- **Sistema de tick formatting** (`_internal/tick_formatting.py`): Controle de frequencia e formato de ticks temporais no eixo X via `tick_format` (strftime) e `tick_freq` (`"day"`, `"week"`, `"month"`, `"quarter"`, `"semester"`, `"year"`) -- usa `matplotlib.dates` locators/formatters
- **`TicksConfig.date_format` e `TicksConfig.date_freq`**: Campos de config para tick formatting, configuraveis via TOML e env vars
- **Area chart fill-between semantics**: 2 colunas agora preenchem entre o par (spread/intervalo) em vez de independentemente a partir de zero; 3+ colunas manteem comportamento independente
- **Passive obstacles no debug overlay**: Obstaculos passivos renderizados em cinza tracejado no modo `debug=True`
- **Stackplot registra PolyCollections como passive**: Collision engine agora reconhece areas empilhadas como obstaculos passivos

### Changed
- **Theme aplica config completa de grid** (`theme.py`): rcParams agora incluem `axes.grid.axis`, `grid.alpha`, `grid.color`, `grid.linestyle` alem do `axes.grid`
- **Debug overlay refatorado** (`collision.py`): `_draw_obstacles()` helper com suporte a passivos e `_collect_passive_obstacles()` para coleta cross-axis
- **`label_padding_px` default reduzido** de 4.0 para 2.0 (`CollisionConfig`)
- **Tick rotation: alinhamento para angulos negativos** corrigido de `"center"` para `"left"`
- **Collections nao-PathCollection deixadas sem registro** no renderer post-render -- auto-detectadas por `_collect_obstacles()` em vez de registro explicito como passive
- **`charting.example.toml` atualizado** com secao `[layout.grid]` e campos `date_format`/`date_freq` em `[ticks]`

### Removed
- **Parametro `fill_between`** de `plot()`, `compose()`, `Layer`, `create_layer()`, accessor e `TransformAccessor` -- funcionalidade absorvida pelo area enhancer (modo 2 colunas)
- **`overlays/fill_between.py`** -- modulo inteiro deletado
- **`add_fill_between()` da API publica de overlays**
- **`scripts/test_tick_rotation.py`** -- substituido por `test_axis_controls.py`

## [2026-02-18 15:30]
### Added
- **Parametro `collision`** em `plot()`, `compose()` e accessor: `collision=False` desabilita completamente a collision resolution engine -- util para graficos simples onde a resolucao de colisao e desnecessaria ou interfere no layout
- **Ajuste automatico de margem inferior** (`_internal/tick_rotation.py`): Apos rotacao de tick labels, `_adjust_bottom_margin()` empurra o axes para cima se labels sobreporem a area do footer

### Changed
- **Collision engine condicional** (`engine.py`, `compose.py`): Registro de legend como obstaculo e resolucao de colisoes agora executam apenas quando `collision=True` (default), evitando processamento desnecessario
- **Skip de rotacao quando angulo e zero** (`tick_rotation.py`): Early return evita setar rotation/ha desnecessariamente e pular ajuste de margem

## [2026-02-18 15:07]
### Added
- **`units="x"` (multiplier formatter)**: Novo formato de eixo Y para dados que representam multiplicadores (P/L, EV/EBITDA, etc.) -- formata valores como `12,3x`, `0,8x` respeitando locale para separador decimal

## [2026-02-18 14:48]
### Added
- **Sistema de tick rotation** (`_internal/tick_rotation.py`): Auto-rotacao de labels do eixo X para prevenir sobreposicao -- modo `"auto"` detecta overlap via `get_window_extent()` e aplica rotacao apenas quando necessario; modo fixo aceita angulo em graus
- **`TicksConfig`** (`settings/schema.py`): Nova sub-config com `rotation` (`"auto"` ou angulo) e `auto_rotation_angle` (default 45) -- configuravel via TOML e env vars
- **Parametro `tick_rotation`** em `plot()`, `compose()` e accessor: Controle per-call da rotacao de ticks, com precedencia sobre config global
- **Secao `[ticks]` no `charting.example.toml`**: Exemplo de configuracao com `rotation` e `auto_rotation_angle`

### Changed
- **Pipeline do engine** (`engine.py`): Novo step 5d aplica tick rotation apos right margin e antes da legenda
- **Pipeline do compose** (`compose.py`): Tick rotation inserido como step 4, reordenando steps subsequentes (5-8)

## [2026-02-18 14:25]
### Added
- **9 novos chart enhancers** (`charts/enhancers/`): Suporte especializado para area, ecdf, eventplot, hist, pie, stackplot, stairs, statistical (boxplot/violinplot) e stem -- cada um registrado via `@ChartRenderer.register_enhancer` com color cycling, labels e kwargs corretos para a API do matplotlib
- **Horizontal bar chart** (`charts/enhancers/bar.py`): `kind='barh'` com suporte a multi-coluna (grouped), sort, color cycling e y_origin
- **`compute_bar_offsets()`** (`charts/_helpers.py`): Calcula largura e offsets por coluna para grouped bar charts (vertical e horizontal)
- **`_UNSUPPORTED_KINDS`** (`charts/renderer.py`): Blocklist explicita para chart kinds incompativeis (imshow, contour, quiver, etc.) com mensagens de erro descritivas
- **Auto-deteccao de collections na collision engine** (`collision.py`): `ax.collections` de sibling axes agora auto-detectados como obstaculos -- `PathCollection` (scatter) como filled, outros como passive
- **Alias `area` -> `fill_between`** (`renderer.py`): `kind='area'` mapeia para `ax.fill_between()` via enhancer
- **Testes para todos os novos chart types** (11 arquivos): test_area, test_barh, test_ecdf, test_eventplot, test_hist, test_pie, test_stackplot, test_stairs, test_statistical, test_stem, test_unsupported

### Changed
- **Collision engine unificada com `_PathObstacle`** (`collision.py`): Sistema dual (bbox obstacles + `_LinePathObstacle`) substituido por classe unica `_PathObstacle` que extrai geometria real de qualquer Artist via factory functions (`_path_from_line`, `_path_from_patch`, `_path_from_collection`, `_path_from_extent`)
- **`register_artist_obstacle()` substitui `register_fixed()` + `register_line_obstacle()`**: API unica com parametros `filled` (shape vs line) e `colocate` (skip para labels que iniciam sobre a propria linha)
- **`_collect_obstacles()` com dispatch por tipo**: Recebe renderer, auto-detecta collections em siblings, e despacha artists registrados por tipo (Line2D -> path, Collection -> paths, Patch -> patch transform, fallback -> extent)
- **`_resolve_all()` usa lista unificada de `_PathObstacle`**: Padding condicional (obstacle_pad para filled, 0 para lines) em vez de separar bbox/path obstacles
- **Post-render no `ChartRenderer`**: PathCollection (scatter) registrado como filled obstacle, outras collections como passive -- alem dos Line2D existentes
- **Scatter markers registrados como passive** (`overlays/markers.py`): Evita que pontos de highlight se tornem obstaculos de colisao automaticamente
- **Debug overlay atualizado** (`collision.py`): Renderiza todas as geometrias (filled com face color, unfilled com edge grosso), substituindo o sistema anterior de rects translucidos
- **Documentacao atualizada**: architecture.md, extending.md, internals.md, collision.md e api.md refletem a nova API unificada

### Removed
- **`register_fixed()`**: Substituido por `register_artist_obstacle(ax, artist, filled=True)`
- **`register_line_obstacle()`**: Substituido por `register_artist_obstacle(ax, artist, filled=False, colocate=True)`
- **`_LinePathObstacle`**: Substituida pela `_PathObstacle` unificada
- **`_obstacles` e `_line_obstacles` WeakKeyDictionaries**: Consolidados em `_artist_obstacles`
- **Type alias `Obstacle`**: Desnecessario -- tudo e `_PathObstacle`

## [2026-02-13 21:14]
### Added
- **`ChartRenderer` com rendering generico** (`charts/renderer.py`): Novo motor de rendering que despacha para `ax.{kind}()` para qualquer tipo de grafico matplotlib, eliminando a necessidade de registrar cada tipo manualmente
  - Enhancers para tipos complexos via `@ChartRenderer.register_enhancer("name")` -- bar grouping e stacking continuam com logica especializada
  - `Enhancer` Protocol define a interface de handlers especializados
  - `_generic_render()` com color cycling automatico, kind defaults per-type, e highlight inference via snapshot diff de patches
  - `_ALIASES` mapeia `"line"` -> `"plot"` (matplotlib usa `ax.plot()`)
  - `_KIND_DEFAULTS` aplica defaults per-kind (ex: `linewidth` para `plot`)
  - Post-render: snapshot diff de `ax.lines` registra novos Line2D como obstaculos de colisao
  - `validate_kind()` publica para validacao eagerly em `create_layer()`
- **`charts/enhancers/` package**: Enhancers de bar e stacked_bar movidos para subpackage dedicado, com auto-registro via import no `__init__.py`

### Changed
- **`ChartKind` agora e `str`** (`engine.py`): Tipo expandido de `Literal["line", "bar", "stacked_bar"]` para `str` -- qualquer metodo valido de matplotlib Axes (scatter, step, stem, hist, etc.) funciona automaticamente
- **Engine e compose usam `ChartRenderer.render()`**: Dispatch unificado substitui `ChartRegistry.get(kind)` + chamada manual em ambos os pipelines
- **Layer validation via `ChartRenderer.validate_kind()`** (`layer.py`): Validacao eagerly agora levanta `ValidationError` (em vez de `RegistryError`) para kinds invalidos
- **Testes atualizados**: Import de `plot_bar` aponta para `charts/enhancers/bar.py`, teste de layer espera `ValidationError` em vez de `RegistryError`

### Removed
- **`ChartRegistry`** (`charts/registry.py`): Classe inteira deletada -- substituida por `ChartRenderer`
- **`charts/line.py`**: Rendering de linhas agora tratado genericamente pelo `ChartRenderer._generic_render()`
- **`charts/bar.py` e `charts/stacked_bar.py`** (top-level): Movidos para `charts/enhancers/` como enhancers registrados

## [2026-02-13 00:48]
### Fixed
- **Right margin para highlight labels** (`engine.py`): Pipeline single-chart agora aplica `add_right_margin()` (expansao de 6% no xlim) quando highlights estao presentes, evitando clipping de labels no ultimo datapoint -- comportamento ja existia no `compose()` mas faltava no `engine.py`
- **`ax.lines[-1]` implicito** (`line.py`): Captura explicita do retorno de `ax.plot()` em vez de depender da ordem de `ax.lines`, prevenindo fragilidade com hooks/callbacks

### Changed
- **Validacao do compose pipeline simplificada** (`compose.py`, `layer.py`): Removida tripla validacao redundante -- `create_layer()` valida eagerly, `_validate_layers()` agora contem apenas checks compose-level (empty layers, all-right, legend)
- **`MetricRegistry.apply()` aceita `str` diretamente** (`registry.py`): Normalizacao `str -> [str]` internalizada no registry, removidos isinstance checks duplicados de `engine.py` e `compose.py`
- **Stat line API com parametros explicitos** (`reference_lines.py`): `add_ath_line`, `add_atl_line`, `add_avg_line` recebem `color`, `linestyle`, `label`, `linewidth`, `series` em vez de `**kwargs`
- **`prepare_categorical_axis` consistente** (`stacked_bar.py`): Usa retorno de `prepare_categorical_axis()` diretamente (como `bar.py`), removendo `np.arange` manual e chamada redundante
- **Imports via facade** (`charts/`, `_internal/highlight.py`): Todos os imports de overlays agora usam `from ..overlays import ...` via package `__init__.py`
- **Type alias `Obstacle`** (`collision.py`): `Obstacle = Artist | _LinePathObstacle` para type annotations honestas em `_collect_obstacles`, `_resolve_all`, `_draw_debug_overlay`
- **Import top-level de `ValidationError`** (`_validation.py`): Movido de import deferido desnecessario para top-level junto com demais imports de pydantic

### Added
- **`resolve_series()` helper** (`_internal/extraction.py`): Extrai coluna de DataFrame com fallback para primeira coluna, eliminando bloco duplicado em 3 overlays
- **`add_right_margin()` compartilhado** (`_internal/extraction.py`): Extraido de `compose.py` para uso em ambos os pipelines (engine + compose)
- **`__all__` em 4 modulos**: `temporal.py`, `reference_lines.py`, `moving_average.py`, `bands.py` -- alinhado com convencao do projeto

### Removed
- **Dead code em `collision.py`**: `_LinePathObstacle.get_visible()` (nunca chamado), parametro `movement` em `_compute_displacement_options` (sempre `"xy"`), parametro redundante `collision` em `_add_connectors`
- **`_validate_params` static method** (`engine.py`): Delegacao pura removida, call site usa `validate_plot_params()` diretamente
- **`_needs_right_axis()` one-liner** (`compose.py`): Inlinado no unico call site
- **Testes obsoletos** (`test_layer.py`, `test_validate.py`): Testes de validacao redundante removidos -- cobertura mantida via pipeline completo

## [2026-02-12 23:40]
### Changed
- **Collision engine: path-based detection** (`collision.py`): `_LineSampleObstacle` (N obstacle objects per data point) substituido por `_LinePathObstacle` (1 objeto por linha), usando `Path.intersects_bbox()` (Cython/C) para deteccao continua e exata ao longo da curva inteira
  - Bulk transform via numpy em vez de N chamadas individuais a `ax.transData.transform()`
  - Quick-reject via `get_extents().overlaps()` antes do check detalhado por segmentos
  - `local_bbox()` filtra vertices por X-range com numpy mask para gerar candidatos de displacement
  - Cache de display path por `_LinePathObstacle` (transform estavel durante resolution pass)
  - Reducao de ~3000 objetos Python para 1 por linha, estimativa de ~10s para <1s em series longas
- **`_resolve_all()` separa bbox e path obstacles**: Novo fluxo distingue obstaculos discretos (patches, labels) de obstaculos continuos (line paths), com logica de co-location same-axis preservada via `obs.intersects()` em vez de `raw_bbox.overlaps(obs_ext)`
- **`_find_free_position()` valida contra paths**: Nova funcao `_position_is_free()` unifica validacao contra bbox overlaps e path intersections, usada tanto no candidate check quanto no fallback diagonal
- **`_collect_obstacles()` simplificado**: Loop de sampling por data point (com `isfinite` check, zip, e criacao de N `_LineSampleObstacle`) substituido por criacao direta de 1 `_LinePathObstacle` por linha registrada

### Added
- **`debug=True` em `plot()` e `compose()`**: Parametro propagado ate `resolve_collisions()` / `resolve_composed_collisions()`, ativa overlay visual de colisao sem scripts externos
- **`_draw_debug_overlay()`** (`collision.py`): Funcao interna que renderiza bboxes translucidos sobre a figura -- obstaculos fixos (vermelho), line paths (laranja com PathPatch), labels moveveis (azul), e bounds do axes (verde)
- **`_position_is_free()`** (`collision.py`): Helper que valida posicao contra lista de bbox obstacles e lista de path obstacles em chamada unica

### Removed
- **`_LineSampleObstacle`**: Classe inteira deletada (substituida por `_LinePathObstacle`)
- **`isfinite` import**: Unico uso era no loop de sampling de pontos, removido junto com o loop

## [2026-02-12 17:52]
### Added
- **Chart composition system** (`composing/`): Nova funcao `compose()` que combina multiplos `Layer` em um unico grafico com suporte a dual-axis
  - `Layer` (frozen dataclass) captura intent de plotagem sem renderizar; `create_layer()` valida eagerly
  - `AxisSide = Literal["left", "right"]` para controle de eixo por layer
  - `df.chartkit.layer()` em `ChartingAccessor` e `TransformAccessor` para criar layers
  - `compose(*layers, title, source, legend, figsize)` renderiza todas as layers, consolida legenda de ambos os eixos, e retorna `PlotResult`
  - `_ComposePlotter` satisfaz o `Saveable` Protocol para integrar com `PlotResult`
  - Validacao: exige pelo menos uma layer, rejeita todas no eixo direito, warning para unidades conflitantes no mesmo eixo
  - Margem direita automatica quando ha highlights (evita labels cortados na borda)
- **`Saveable` Protocol** (`result.py`): Interface estrutural para objetos que salvam figuras -- `PlotResult.plotter` aceita `ChartingPlotter` ou `_ComposePlotter`
- **Cross-axis collision resolution** (`resolve_composed_collisions`): Merge labels de todos os axes em pool unico e resolve em pixel space, respeitando transforms individuais por axes
- **Line path obstacle sampling**: `_LineSampleObstacle` cria obstaculos virtuais em cada data point de linhas registradas, permitindo que labels evitem o caminho visivel da linha (bboxes de Line2D abrangem a area inteira e sao inuteis como alvo de colisao)
- **`register_line_obstacle()`**: Nova API para registrar Line2D como obstaculo de colisao via amostragem de pontos
- **Highlight mode `"all"`** em `markers.py`: Anota cada data point (nao apenas last/max/min), com posicionamento vertical automatico por sinal do valor
- **Label offset** (`_apply_label_offset`): Respiro vertical configuravel entre label e data point via `markers.label_offset_fraction`
- **`add_title()` como decoration reutilizavel** (`decorations/title.py`): Titulo extraido do engine para modulo proprio, disponivel para composicao e plotagem simples
- **Modulos `_internal` compartilhados**: Logica extraida do engine para reuso entre `engine.py` e `compose.py`
  - `extraction.py`: `extract_plot_data()` e `should_show_legend()` -- data selection e legend logic
  - `formatting.py`: tabela `FORMATTERS` de dispatch para formatadores de eixo Y
  - `highlight.py`: `normalize_highlight()` para normalizacao de input de destaque
  - `plot_validation.py`: `validate_plot_params()`, `PlotParamsModel` e `UnitFormat`
  - `saving.py`: `save_figure()` com resolucao de paths relativos para diretorio de charts
- **Categorical index support** em bar/stacked_bar: `is_categorical_index()` e `prepare_categorical_axis()` para indices textuais
- **Bar chart `sort`**: Ordenacao ascending/descending para graficos de barra single-column
- **Bar chart `color='cycle'`**: Cycling de cor por barra individual usando paleta do tema (single-column only)
- **`MarkersConfig.label_offset_fraction`**: Novo campo de config para controle do respiro vertical dos labels
- **`CollisionConfig.movement` tipado como `Literal["x", "y", "xy"]`**: Validacao estatica em vez de string livre

### Changed
- **Collision engine reescrita**:
  - `_resolve_all()` unifica resolucao contra obstaculos fixos e entre labels (substitui `_resolve_against_fixed` + `_resolve_between_moveables`)
  - `_find_free_position()` gera candidatos de todos os obstaculos colidentes, valida contra todos, com fallback diagonal
  - `_pad_bbox()` substitui `_get_padded_bbox()` (padding fixo, mais simples)
  - `_compute_displacement_options()` retorna todas as opcoes (substitui `_best_displacement()` que retornava apenas a melhor)
  - `_shift_label()` usa `label.axes` em vez de receber ax explicito
  - `_add_connectors()` agrupa labels por axes pai para transforms corretos
  - `_collect_obstacles()` percorre sibling axes (twinx) para colisao cross-axis -- detecta patches, labels e line samples de todos os eixos compartilhados
  - `fig.canvas.draw()` substituido por `fig.draw_without_rendering()` (mais leve)
- **`bar.py` renderiza multi-coluna como grouped bars**: Chamadas individuais `ax.bar()` com color cycling, offsets calculados por coluna (substitui pandas `.plot(kind="bar")` que usava eixo categorico)
- **`highlight` obrigatorio em `bar.py`/`stacked_bar.py`**: Tipo mudou de `list | None = None` para `list` (normalizacao feita pelo caller)
- **`engine.py` simplificado**: Metodos privados extraidos para `_internal` e `decorations`, engine agora delega
- **Legend registrada como obstaculo fixo** para resolucao de colisao
- **`to_month_end()` consolida observacoes mensais**: Mantem apenas a ultima observacao cronologica por mes em vez de permitir indices duplicados
- **`detect_bar_width()` mais robusto**: `_coerce_datetime_index()` trata object-dtype e indices nao-datetime graciosamente
- **`_resolve_x_position()` em markers**: Trata indices duplicados retornando o primeiro match escalar
- **Testes atualizados**: matplotlib backend `Agg` forcado em conftest, imports atualizados para novos paths em `_internal`

### Removed
- **`_best_displacement()`**: Substituido por `_compute_displacement_options()` + `_find_free_position()`
- **`_get_padded_bbox()`**: Substituido por `_pad_bbox()`
- **`_resolve_against_fixed()` e `_resolve_between_moveables()`**: Unificados em `_resolve_all()`
- **`_FORMATTERS`, `_normalize_highlight()`, `_PlotParams`, `UnitFormat` do engine**: Movidos para `_internal/`
- **`_apply_title()` do engine**: Movido para `decorations/title.py`
- **`_apply_decorations()` do engine**: Substituido por chamadas diretas a `add_footer()` e `add_title()`
- **Logica de save do engine**: Movido para `_internal/saving.py`
- **`plot_lines` acumulador em `line.py`**: Lista nao utilizada removida
- **Testes `test_best_displacement.py` e `test_get_padded_bbox.py`**: API substituida pela nova collision engine

## [2026-02-12 00:53]
### Added
- **Suite de testes com 283 tests**: Cobertura completa dos modulos com logica propria, preparando a lib para open-source
  - `tests/transforms/` (150 tests): validacao, coercao, resolucao de frequencia, pydantic models, e todas as 8 funcoes de transform (variation, accum, diff, normalize, annualize, drawdown, zscore, to_month_end) + TransformAccessor delegation
  - `tests/metrics/` (30 tests): MetricRegistry.parse() com specs simples/compostas/targeting/labels, coercao de tipos, erros, e registro/lifecycle do registry
  - `tests/settings/` (39 tests): _deep_merge, find_project_root/find_config_files, ConfigLoader (cache, reset, path resolution, TOML loading), ChartingConfig defaults e env vars
  - `tests/collision/` (16 tests): _best_displacement com geometria exata (Bbox), _pos_to_numeric, _get_padded_bbox com mock artist
  - `tests/engine/` (13 tests): _normalize_highlight (modos validos/invalidos, bool, lista) e _PlotParams validation (Pydantic)
  - `tests/test_formatters.py` (15 tests): currency, compact_currency, percent, human_readable e points formatters com mock de config
- **Fixtures compartilhadas** (`tests/conftest.py`): DataFrames financeiros realistas (seed fixa rng=42), edge cases (empty, all-NaN, constant, non-datetime index)
- **Fixtures por modulo**: known-value data para transforms (resultados pre-calculados), registry snapshot/restore para metrics, config isolation para settings
- **Config pytest** (`pyproject.toml`): `[tool.pytest.ini_options]` com strict-markers, strict-config, filterwarnings error + ignore matplotlib UserWarning

## [2026-02-11 21:18]
### Added
- **Custom exception hierarchy**: `ValidationError`, `RegistryError`, `StateError` com heranca multipla dos tipos built-in (`ValueError`, `LookupError`, `RuntimeError`) para manter compatibilidade com `except ValueError` existente
- **`disable_logging()`**: Nova funcao publica para reverter `configure_logging()` -- remove handlers e desativa logger
- **Logging estruturado em toda a lib**: `logger.debug` para tracing interno (plot params, dispatch, collision counts, transform resolution) e `logger.warning` para problemas potenciais (series vazias, dados NaN, datas invertidas, comprimentos diferentes)
- **Validacao de `diff(periods=0)`**: Rejeitado com mensagem descritiva (retorna all-zeros, quase certamente erro do usuario)
- **Validacao de `zscore(window=1)`**: Rejeitado (std de 1 valor e indefinido, produziria all-NaN)
- **Frequencias `BME`/`BMS` (Business Month End/Start)**: Suportadas em `FREQ_ALIASES` e `FREQ_PERIODS_MAP`
- **Frequencias `BQE`/`BQS`/`BYE`/`BYS` (Business Quarter/Year)**: Adicionadas ao `FREQ_PERIODS_MAP` e restauradas em `_ANCHORED_PREFIXES` para auto-detect via `pd.infer_freq()`
- **Erro especifico para frequencia detectada mas nao suportada**: `resolve_periods()` agora diferencia "nao consegui detectar" de "detectei mas nao suporto", com mensagem listando frequencias validas

### Changed
- **`ValueError`/`RuntimeError`/`TypeError` migrados para hierarquia customizada**: Todos os raises internos agora usam `ValidationError`, `RegistryError`, `StateError` ou `TransformError` -- catch via `except ChartKitError` captura todos
- **`configure_logging()` idempotente**: Chamadas repetidas removem handler anterior antes de adicionar novo, evitando duplicacao de logs
- **`_PctChangeParams` renomeado para `_FreqResolvedParams`**: Nome mais descritivo (usado por `variation` e `annualize`)
- **`normalize(base_date)` com error handling**: `pd.Timestamp()` invalido agora gera `TransformError` em vez de exception crua
- **`diff()` e `zscore()` com validacao via pydantic**: Parametros validados antes da execucao, mensagens de erro limpas
- **`TransformsConfig.normalize_base` e `accum_window` validados como `PositiveInt`**: Config com valores <= 0 rejeitada na carga
- **Logs padronizados em ingles**: Mensagens de warning em `bar.py` e `stacked_bar.py` convertidas de portugues para ingles

### Fixed
- **`_ANCHORED_PREFIXES` incompleto**: Prefixos `BQE-`/`BQS-`/`BYE-`/`BYS-` haviam sido removidos, quebrando auto-detect para dados com frequencia business quarter/year
- **Stripping de multiplicador em freq codes produzia calculos errados**: `"2D"` (bidiario) era normalizado para `"D"` (diario), resultando em periods incorretos. Agora frequencias multiplicadas caem no erro "not supported" com sugestao de usar `periods=` explicito
- **`coerce_input()` levantava `TypeError` em vez de `TransformError`**: Inconsistente com o resto do modulo de validacao

### Removed
- **Aliases ambiguos `"day"`, `"bday"`, `"week"`, `"month"`, `"quarter"`, `"year"` de `FREQ_ALIASES`**: Conflitavam com `horizon='month'`/`'year'` em `variation()`. Aliases existentes `"daily"`, `"business"`, `"weekly"`, `"monthly"`, `"quarterly"`, `"yearly"` cobrem os mesmos casos sem ambiguidade
- **Nomes com underscore de `__all__` em `_validation.py`**: `_FreqResolvedParams`, `_DiffParams`, `_ZScoreParams`, `_infer_freq`, `_normalize_freq_code` removidos -- modulo interno nao deve exportar nomes privados

## [2026-02-10 05:00]
### Changed
- **`yoy()` e `mom()` unificados em `variation(horizon)`**: API simplificada -- `variation(horizon='year')` substitui `yoy()`, `variation(horizon='month')` substitui `mom()`. Horizonte como parametro semantico em vez de funcoes separadas
- **`compound_rolling()` absorvido por `accum()`**: `accum()` agora faz fallback para `config.transforms.accum_window` quando frequencia nao pode ser inferida, cobrindo o caso de uso de `compound_rolling`
- **Config `rolling_window` renomeado para `accum_window`**: Reflete a consolidacao de transforms -- campo agora pertence exclusivamente ao `accum()`
- **`MetricRegistry` usa `_MetricEntry` NamedTuple**: Substitui tuple crua por tipo nomeado com `func`, `param_names`, `required_params`, `uses_series`. Introspecao de parametros obrigatorios via `inspect.signature`
- **`accum()` usa `np.prod` em vez de `np.nanprod`**: Semantica mais correta -- NaN propagado em vez de silenciosamente ignorado

### Added
- **Validacao de parametros obrigatorios em metricas**: `MetricRegistry.parse()` agora levanta `ValueError` com mensagem descritiva quando params obrigatorios estao ausentes (ex: `"Metrica 'ma' requer parametro(s): window"`)
- **Guard clauses em overlays**: `add_moving_average` valida `window >= 1`, `add_std_band` valida `window >= 2` e `num_std > 0`
- **Protecao contra valores nao-finitos nos formatters**: Todos os formatadores (currency, compact, %, human, points) retornam `""` para `inf`/`NaN`, evitando crashes no matplotlib

### Removed
- **`yoy()`**: Substituido por `variation(horizon='year')`
- **`mom()`**: Substituido por `variation(horizon='month')`
- **`compound_rolling()`**: Caso de uso coberto por `accum()` com fallback para config
