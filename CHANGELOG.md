# Project Changelog

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

## [2026-02-10 04:33]
### Changed
- **Valores hardcoded extraidos para config**: Parametros que antes viviam diretamente no codigo agora sao configuraveis via TOML/env vars:
  - `base_style` e `grid` no layout (matplotlib style e visibilidade do grid)
  - `spines` (top/right/left/bottom) como sub-config de layout
  - `target_style` em lines (estilo da linha de meta, default `"-."`)
  - `warning_threshold` em bars (limiar de pontos para aviso de legibilidade)
  - `font_weight` em markers (peso da fonte dos labels de destaque)
  - `connector_width` em collision (espessura dos conectores)
  - `target_format` e `std_band_format` em labels (templates de formatacao)
- **`std_band` usa `reference_style` da config**: Linha central do Bollinger Band agora respeita `lines.reference_style` em vez de `"--"` hardcoded

### Added
- **`SpinesConfig`**: Novo sub-model para controle granular de visibilidade das bordas do grafico
- **Novas opcoes no `charting.example.toml`**: Todas as novas configs documentadas como referencia comentada

## [2026-02-10 04:01]
### Changed
- **`charting.example.toml` reorganizado por nivel de necessidade**: Parametros separados em 3 secoes -- Essencial (branding, locale), Identidade Visual (cores, fonte), e Ajuste Fino (todo o resto comentado como referencia)
- **Resolucao de `assets_path` consolidada em `PathsConfig`**: Campo duplicado `FontsConfig.assets_path` removido, resolucao agora segue o mesmo padrao de `outputs_path` (`configure() > paths.assets_dir > project_root/assets`)

### Removed
- **`FontsConfig.assets_path`**: Campo redundante com `PathsConfig.assets_dir` -- ambos apontavam para o mesmo diretorio, quebrando o padrao de resolucao de paths do projeto

## [2026-02-10 03:43]
### Changed
- **`highlight` agora suporta modos `last`, `max`, `min`**: Parametro aceita `bool`, string ou lista de modos (ex: `highlight=['max', 'min']`). `True` continua funcionando como atalho para `'last'`
  - Novo tipo `HighlightInput = bool | HighlightMode | list[HighlightMode]` exportado na API publica
  - Normalizacao e validacao centralizada em `_normalize_highlight()` no engine
- **`annualize_daily` renomeado para `annualize`**: Funcao generalizada para qualquer frequencia temporal, nao apenas diaria
  - Agora aceita `periods=` (override direto) ou `freq=` (resolve via `FREQ_PERIODS_MAP`) em vez de `trading_days=`
  - Reutiliza `_PctChangeParams` + `resolve_periods()` em vez de validacao propria
- **Highlight rendering refatorado**: `add_highlight()` agora itera sobre lista de modos, com deduplicacao por indice e posicionamento especifico por modo (max=acima, min=abaixo, last=estilo do chart type)

### Fixed
- **`_VALID_HIGHLIGHT_MODES` derivado do Literal**: Set agora usa `get_args(HighlightMode)` em vez de valores hardcoded, eliminando duplicacao e risco de dessincronizacao ao adicionar novos modos
- **Mutable default `[]` em bar/stacked_bar**: Parametro `highlight` trocado de `list = []` (`# noqa: B006`) para `list | None = None` com normalizacao interna, seguindo padrao idiomatico Python
- **Docstrings de `_PctChangeParams` e modulo `temporal.py`**: Atualizadas para refletir uso por `annualize` alem de `mom`/`yoy`

### Removed
- **`trading_days_per_year` removido da config**: Campo `TransformsConfig.trading_days_per_year` e `charting.example.toml` `[transforms].trading_days_per_year` eliminados -- resolucao de periodos agora e automatica via frequencia dos dados
- **`_AnnualizeParams` removido**: Validacao de `annualize` agora usa `_PctChangeParams` existente
- **`highlight` removido de `_PlotParams`**: Validacao do highlight movida para `_normalize_highlight()` com mensagens de erro especificas

## [2026-02-10 03:33]
### Added
- **Validacao runtime de parametros do `plot()`**: `highlight`, `units` e `legend` validados via Pydantic `StrictBool`/`Literal` antes de qualquer side effect
  - Valores truthy nao-bool (ex: `highlight="banana"`, `legend=1`) agora geram `ValueError` claro
- **Validacao de `y_origin` em bar/stacked_bar**: Type hint `Literal["zero", "auto"]` + check runtime com mensagem descritiva
- **Validacao de `style` em `add_highlight()`**: Mensagem de erro explicita com estilos disponiveis em vez de `KeyError` crua

## [2026-02-10 02:56]
### Changed
- **`highlight_last` renomeado para `highlight`**: Parametro de destaque do ultimo valor simplificado em `plot()`
- **`save_path` removido de `plot()`**: Salvar graficos agora e exclusivamente via `PlotResult.save()`
- **Parametros keyword-only**: `plot()` agora exige keyword args apos `x`/`y` (separador `*`)
- **Tipos Literal para `kind` e `units`**: Novos type aliases `ChartKind` e `UnitFormat` com autocomplete e validacao estatica
  - `ChartKind = Literal["line", "bar", "stacked_bar"]`
  - `UnitFormat = Literal["BRL", "USD", "BRL_compact", "USD_compact", "%", "human", "points"]`
- **`source` com fallback para `branding.default_source`**: Quando `source=None`, footer usa `default_source` da config

### Added
- **`branding.default_source`**: Novo campo de configuracao para fonte padrao no rodape
- **`ChartKind` e `UnitFormat` exportados**: Disponiveis via `from chartkit import ChartKind, UnitFormat`

## [2026-02-10 02:25]
### Added
- **Labels customizaveis em metricas**: Sintaxe `|` para definir nome na legenda (ex: `'ath|Maximo'`, `'ma:12@col|Media 12M'`, `'hline:100|Meta: Q1'`)
  - Parse seguro: `|` extraido antes de `@` e `:`, permitindo caracteres especiais no label
  - `MetricSpec.label` flui automaticamente via `**kwargs` ate os overlays do matplotlib

## [2026-02-09 02:19]
### Added
- **Metrica `avg`**: Linha horizontal na media (mean) dos dados via `metrics=['avg']`
  - Usa cor `colors.grid` e label configuravel via `labels.avg`
- **Parametro `legend` em `plot()`**: Controle explicito da legenda (`None` = auto, `True` = forca, `False` = suprime)
- **Suporte a `pd.Series` no accessor**: `df["col"].chartkit.plot()` funciona diretamente (Series convertida para DataFrame internamente)
- **`LegendConfig` top-level**: Nova secao `[legend]` na config com campos `loc`, `alpha`, `frameon`

### Changed
- **Legend system unificado**: Legenda movida de per-chart (line.py, stacked_bar.py) para `engine._apply_legend()`
  - Auto-detecta quando mostrar (2+ artists rotulados) em vez de depender de cada chart type
- **`LegendConfig` movido de `lines.legend` para `legend`**: Secao top-level no config e TOML
- **`detect_bar_width()` extraido para `charts/_helpers.py`**: Logica de largura automatica compartilhada entre `bar.py` e `stacked_bar.py`
- **`_add_extreme_line` renomeado para `_add_stat_line`**: Funcao interna generalizada para suportar `max`, `min` e `mean`

### Removed
- **Legenda per-chart em `line.py` e `stacked_bar.py`**: Substituida pelo sistema unificado no engine

## [2026-02-07 04:27]
### Added
- **Transforms: `drawdown()`**: Distancia percentual do pico historico via `(data / cummax - 1) * 100`
  - Guarda contra dados nao-positivos (zero ou negativos) com `TransformError` explicito
- **Transforms: `zscore()`**: Padronizacao estatistica com suporte a z-score global e rolling (janela movel)
  - Permite comparar series com unidades diferentes no mesmo grafico
- **Transforms: `accum()`**: Substitui `accum_12m()` com janela configuravel e auto-detect de frequencia
  - Usa `np.nanprod` com `raw=True` para performance e tolerancia a NaN
- **Frequency auto-detection**: Transforms `mom`, `yoy`, `accum`, `compound_rolling` agora detectam a frequencia dos dados automaticamente via `pd.infer_freq`
  - Novo parametro `freq=` como alternativa a `periods=`/`window=` (mutuamente exclusivos)
  - Mapeamento completo: D, B, W, M, Q, Y (incluindo aliases amigaveis e freq codes ancorados)
- **Validation layer (`transforms/_validation.py`)**: Modulo interno de validacao, coercao e resolucao de frequencia
  - Coercao automatica: dict, list, ndarray convertidos para DataFrame/Series
  - Validacao numerica com filtragem de colunas non-numeric e warning
  - Sanitizacao de resultado: inf/-inf substituidos por NaN
  - Pydantic models para validacao de parametros escalares (`_PctChangeParams`, `_RollingParams`, etc.)
- **Exception hierarchy (`exceptions.py`)**: `ChartKitError` (base) e `TransformError` para erros de validacao/execucao
- **Chart type: `stacked_bar`**: Grafico de barras empilhadas via `plot(kind='stacked_bar')`
  - Cores da paleta por camada, largura automatica por frequencia, legenda automatica para multi-serie
- **Overlay: `add_fill_between()`**: Area sombreada entre duas series (spreads, intervalos de confianca)
  - Parametro `fill_between=(col1, col2)` no `plot()` para uso direto
- **Overlay: `add_std_band()`**: Banda de desvio padrao (Bollinger Bands) com media movel central opcional
  - Metrica declarativa: `metrics=['std_band:20:2']` (janela 20, 2 desvios padrao)
- **Overlay: `add_vband()`**: Banda vertical sombreada entre duas datas (recessoes, crises, periodos)
  - Metrica declarativa: `metrics=['vband:2020-03-01:2020-06-30']`
- **Overlay: `add_target_line()`**: Linha horizontal de meta com estilo diferenciado (cor secondary, dash-dot)
  - Label automatico com valor formatado: "Meta: R$ 1.000,00"
  - Metrica declarativa: `metrics=['target:1000']`

### Changed
- **Transforms reescritos com contrato unificado**: Todas as funcoes agora aceitam DataFrame, Series, dict, list ou ndarray
  - Validacao e coercao centralizadas via `_validation.py`
  - Protecao contra inf em todos os resultados via `sanitize_result()`
- **`mom()` e `yoy()` sem defaults hardcoded**: Periods resolvidos via auto-detect em vez de config `mom_periods`/`yoy_periods`
- **`compound_rolling()` com auto-detect de frequencia**: Novo parametro `freq=` alem de `window=`
- **`normalize()` robusto**: Usa primeiro valor nao-NaN como referencia, `base_date` com busca nearest, validacao de base zero/NaN por coluna
- **`to_month_end()` com validacao de index**: Raises `TypeError` se index nao for DatetimeIndex
- **`ChartingAccessor` e `TransformAccessor` atualizados**: Novos parametros `freq=` propagados, novos metodos `drawdown()` e `zscore()`
- **`ChartingAccessor.plot()` aceita `fill_between`**: Parametro propagado para `ChartingPlotter.plot()`

### Removed
- **`accum_12m()`**: Substituido por `accum()` com janela configuravel
- **Config `mom_periods` e `yoy_periods`**: Removidos de `TransformsConfig` e `charting.example.toml` (substituidos por auto-detect)

## [2026-02-07 03:05]
### Added
- **`_logging.py` modulo dedicado**: `configure_logging()` extraido de `__init__.py` para modulo proprio
  - Isola side effect (`logger.disable`) do namespace principal
  - Modulo segue convencao do projeto com `__all__` definido
- **`PositionableArtist` Protocol**: Tipagem estrutural para artists reposicionaveis na collision engine
  - `runtime_checkable` permite filtragem segura com `isinstance` antes de chamar `get/set_position`
  - Substitui uso implicito de duck typing sem garantias
- **`@overload` em todas as transform functions**: Return-type narrowing para DataFrame/Series
  - `mom`, `yoy`, `accum_12m`, `diff`, `normalize`, `annualize_daily`, `compound_rolling`, `to_month_end`
  - Type checkers agora inferem o tipo correto baseado no input
- **`pyrightconfig.json`**: Configuracao de type checking com modo `basic` para o projeto
- **Type annotations com `cast()`**: Narrowing explicito em `engine.py`, `bar.py`, `line.py`, `markers.py`
  - Resolve warnings de pyright em operacoes com tipos union do pandas

### Changed
- **Collision engine: monkey-patching -> WeakKeyDictionary**: Estado por-Axes migrado de `ax._charting_*` para `WeakKeyDictionary` module-level
  - Elimina poluicao de namespace em objetos matplotlib
  - Limpeza automatica via GC quando Axes sao destruidos
- **`_pos_to_numeric`: `Number` ABC -> `isinstance(x, (int, float))`**: Check mais preciso para contexto de matplotlib dates
- **`MetricRegistry.apply()` aceita `Sequence` em vez de `list`**: Tipo mais permissivo para specs
- **`normalize()`: variavel `base_date` nao mais reatribuida**: Nova variavel `ts` para o `pd.Timestamp` convertido
- **Formatacao de codigo**: Line breaks em chamadas longas (`line.py`, `collision.py`, `markers.py`)

### Fixed
- **Variable shadowing em `markers.py`**: `x_pos` usado para index posicional e coordenada X renomeado para `loc_idx`

## [2026-02-07 02:22]
### Added
- **ChartRegistry**: Sistema plugavel de chart types via decorator `@ChartRegistry.register("name")`
  - Engine agora despacha via registry em vez de if/elif hardcoded
  - Chart functions registradas automaticamente ao importar o modulo
  - `ChartRegistry` exposto na API publica (`from chartkit import ChartRegistry`)
- **Highlight system unificado**: `HighlightStyle` dataclass + `HIGHLIGHT_STYLES` dict em `overlays/markers.py`
  - Substitui `highlight_last_point` e `highlight_last_bar` por funcao unica `highlight_last(style="line"|"bar")`
  - Extensivel para novos chart types via registro no dict
- **`_ipython_display_` em PlotResult**: Evita rendering duplicado em notebooks Jupyter
- **`uses_series` em MetricRegistry**: Flag que indica se metrica usa parametro `series` para selecionar coluna
  - `hline` e `band` registrados com `uses_series=False` (eliminam `kwargs.pop("series")` manual)
  - Warn de parametros extras ignorados no parse de specs
- **`__all__` em `charts/registry.py` e `styling/__init__.py`**: Exports explicitamente definidos
- **`PROJECT_ROOT_MARKERS` como constante**: Tuple hardcoded em `discovery.py` substitui campo configuravel de PathsConfig

### Changed
- **Settings migrado para pydantic-settings**: Schema inteiro reescrito de dataclasses para pydantic BaseModel/BaseSettings
  - `ChartingConfig` agora herda de `BaseSettings` com suporte a env vars (`CHARTKIT_*`, nested `__`)
  - Novo `_DictSource` custom source para injecao de TOML data no pipeline pydantic-settings
  - Precedencia: init_settings > env vars > TOML files > field defaults
- **ConfigLoader simplificado**: Removidas camadas de indirection (PathResolver, TTLCache, cachedmethod)
  - Path resolution inline com cadeia 3-tier: API explicita > Config (TOML/env) > Fallback
  - TOML loading e deep merge agora como funcoes module-level (`_load_toml`, `_deep_merge`)
- **Engine usa ChartRegistry.get()**: Dispatch generico substitui bloco if/elif para chart types
- **`y_origin` removido de engine e accessor**: Agora flui via `**kwargs` (chart-specific, nao generico)
- **Correcao `is not None`**: Todos os comparativos falsy (`if color`, `if series`) corrigidos para `is not None` em overlays (reference_lines, moving_average, bands)
  - Permite valores como `color=""`, `linewidth=0` serem respeitados
- **line.py: kwargs.pop() para color/linewidth/zorder**: Corrige TypeError quando usuario passa esses parametros via kwargs
- **Type hints adicionados**: `ax: Axes`, `x: pd.Index | pd.Series`, `fig: Figure`, `sink: Any`, `field: FieldInfo` em multiplos modulos
- **PEP 604 union syntax**: `Optional[X]` substituido por `X | None` em `discovery.py` e `loader.py`
- **Exception handling refinado**: `except Exception` substituido por `except (tomllib.TOMLDecodeError, OSError)` em `_load_toml`
- **Moving average registrado como passive**: `register_passive(ax, lines[0])` para participar do collision system
- **MetricRegistry.apply() type hints**: Parametros `ax`, `x_data`, `y_data` agora tipados com Axes, pd.Index, pd.Series/DataFrame

### Removed
- **5 modulos de settings deletados**: `ast_discovery.py`, `runtime_discovery.py`, `paths.py`, `converters.py`, `defaults.py`
  - AST discovery e runtime discovery eliminados (complexidade desproporcional ao beneficio)
  - `PathResolver` inline no `ConfigLoader` (3-tier simples)
  - `converters.py` (dict_to_dataclass/dataclass_to_dict) desnecessario com pydantic
  - `defaults.py` (DEFAULT_CONFIG) desnecessario com pydantic field defaults
- **`toml.py` modulo separado**: Funcoes absorvidas no `loader.py` (simplificacao)
- **`highlight_last_point` e `highlight_last_bar`**: Substituidos por `highlight_last` unificado
- **`project_root_markers` de PathsConfig**: Agora constante `PROJECT_ROOT_MARKERS` em `discovery.py`
- **Comentarios inline no schema**: Removidos comentarios redundantes em campos de dataclass/model

### Dependencies
- Adicionado `pydantic-settings>=2.12.0` (traz pydantic e pydantic-core como transitivas)

## [2026-02-05 01:54]
### Added
- **Sintaxe `@` para metricas**: Direciona metrica para coluna especifica de um DataFrame
  - `'ath@revenue'`, `'ma:12@costs'` aplicam metrica apenas na coluna indicada
  - `rsplit("@", 1)` preserva `:` em nomes de coluna
  - `MetricSpec(name, series='col@weird')` como escape hatch para colunas com `@` no nome
  - Metricas data-independent (`hline`, `band`) ignoram `@` silenciosamente via `kwargs.pop`
- **`metrics` aceita string unica**: `plot(metrics='ath')` alem de lista
  - Normalizacao automatica via `isinstance(metrics, str)` no engine
- **`zorder.data` explicito**: `ax.bar()` e `ax.plot()` agora passam `config.layout.zorder.data`

### Changed
- **Transforms config-driven**: Defaults de `yoy`, `mom`, `normalize`, `annualize_daily` e `compound_rolling` lidos de `get_config().transforms.*` em vez de hardcoded
  - Pattern consistente: `if param is None: param = get_config().transforms.<field>`
  - Assinaturas atualizadas em `temporal.py`, `transforms/accessor.py` e `accessor.py`
- **Type hint corrigido**: `base_date: str = None` -> `base_date: str | None = None` em `normalize()`

### Removed
- **`CurrencyConfig`**: Dataclass removida de `schema.py` e `defaults.py` (substituida por Babel via `babel_locale`)
- **`[formatters.currency]`**: Secao removida do `charting.example.toml`
- **`project_root_markers`**: Removido do TOML de exemplo (configuracao interna, nao exposta ao usuario)

## [2026-01-30 14:29]
### Added
- **Runtime path discovery** (`runtime_discovery.py`): Nova estrategia de descoberta de paths via `sys.modules`
  - Busca `OUTPUTS_PATH` e `ASSETS_PATH` em modulos ja importados pelo processo
  - Permite que bibliotecas host exponham paths automaticamente ao serem importadas
  - Classe `RuntimePathDiscovery` com cache interno e filtragem de stdlib/terceiros
  - Prioridade maior que AST discovery (mais rapido, nao requer I/O)

### Changed
- **Cadeia de precedencia de paths atualizada**: Nova ordem com 5 niveis
  1. Configuracao explicita via `configure()`
  2. Configuracao no TOML
  3. Runtime discovery via `sys.modules` (novo)
  4. Auto-discovery via AST
  5. Fallback silencioso
- **`PathResolver` refatorado**: Agora aceita `runtime_getter` alem de `ast_getter`
  - Separacao clara entre runtime discovery (rapido) e AST discovery (I/O)
- **`ASTPathDiscovery` melhorado**: Busca recursiva de `config.py` com ordenacao por profundidade
  - Substituidos padroes glob estaticos por `rglob("config.py")` + filtragem
  - Ignora diretorios comuns: `.venv`, `node_modules`, `__pycache__`, `chartkit`, etc
  - Arquivos mais proximos da raiz sao processados primeiro

## [2026-01-30 05:20]
### Added
- **Novo modulo `metrics/`**: Sistema declarativo de metricas para graficos
  - Substitui flags booleanas (`show_ath=True`) por lista de metricas: `plot(metrics=['ath', 'ma:12'])`
  - `MetricRegistry`: Registro central com decorator para metricas customizadas
  - Metricas built-in: `ath`, `atl`, `ma:N`, `hline:V`, `band:L:U`
  - Sintaxe com parametros: `'ma:12'` (media movel 12 periodos), `'band:1.5:4.5'` (banda entre valores)
- **Novo `PlotResult`**: Resultado de plotagem que permite method chaining
  - `df.chartkit.plot().save('chart.png').show()`
  - Properties `.axes` e `.figure` para acesso direto ao matplotlib
- **Novo `TransformAccessor`**: Accessor encadeavel para transforms
  - Permite encadeamento completo: `df.chartkit.yoy().mom().plot()`
  - Property `.df` para acessar DataFrame transformado
- **Transforms expostos no accessor principal**: `df.chartkit.yoy()`, `df.chartkit.mom()`, etc.
  - Cada transform retorna `TransformAccessor` para encadeamento

### Changed
- **API de plotagem simplificada**: Argumentos `moving_avg`, `show_ath`, `show_atl`, `overlays` substituidos por `metrics: list[str]`
- **Retorno de `plot()`**: Agora retorna `PlotResult` em vez de `Axes` diretamente
  - Acesso ao axes via `result.axes` (backwards compatible)
- **Accessor refatorado**: Metodos de transform agora retornam `TransformAccessor` para encadeamento
  - Cada acesso ao accessor cria nova instancia (removido cache de plotter)

### Removed
- **`real_rate()` de transforms**: Funcao removida do modulo temporal
- **Metodo `save()` do accessor**: Removido em favor de `plot().save()`
- **Cache de plotter no accessor**: Removido `_PLOTTER_ATTR` (criava complexidade desnecessaria)

## [2026-01-30 02:10]
### Added
- **Formatador de moeda compacto**: Nova funcao `compact_currency_formatter()` para notacao abreviada
  - Exibe valores grandes como "R$ 1,2 mi" em vez de "R$ 1.234.567,00"
  - Ideal para graficos com valores na casa dos milhoes ou bilhoes
  - Novos units `BRL_compact` e `USD_compact` disponiveis no `ChartingPlotter.plot()`
- **Campo `babel_locale` em LocaleConfig**: Configura locale para formatacao Babel (default: `pt_BR`)
  - Permite trocar para `en_US`, `es_ES`, etc. via TOML

### Changed
- **Formatador de moeda reescrito com Babel**: `currency_formatter()` agora usa `babel.numbers`
  - Suporta qualquer codigo de moeda ISO 4217 (BRL, USD, EUR, GBP, JPY, etc.)
  - Formatacao automatica baseada no locale configurado
  - Substitui implementacao manual que so suportava BRL e USD

### Dependencies
- Adicionado `babel>=2.17.0` para formatacao i18n de moedas

## [2026-01-30 01:46]
### Fixed
- **Thread-safety em `reset_project_root_cache()`**: Adicionado lock antes de `cache.clear()`
  - Corrige race condition potencial com operacoes concorrentes de cache
  - Segue recomendacao da documentacao do cachetools

### Removed
- **Codigo morto em `converters.py`**: Removida funcao `_is_tuple_of_floats()` nao utilizada
- **Logs excessivos em `converters.py`**: Removidos `logger.debug()` dentro do loop de conversao
  - Logs de conversao ja existem em nivel mais alto no `loader.py`
  - Reduz ruido seguindo best practice de logging conservador em bibliotecas

## [2026-01-30 01:38]
### Added
- **Loguru logging**: Substituido `logging` stdlib por `loguru` em todos os modulos
  - Nova funcao `configure_logging()` na API publica para ativar logs
  - Logging desabilitado por padrao (best practice para bibliotecas)
  - Logs usam lazy evaluation (`{}`) em vez de f-strings para evitar problemas de encoding
- **Caching com cachetools**: Sistema de cache robusto e thread-safe
  - `find_project_root()` usa `LRUCache(maxsize=32)` com decorator `@cached`
  - `ConfigLoader` usa `TTLCache(maxsize=3, ttl=3600)` para paths resolvidos
  - Thread-safety via `RLock` em todas as operacoes de cache
- **`__all__` em todos os modulos**: Exports publicos explicitamente definidos
  - `loader.py`, `discovery.py`, `paths.py`, `converters.py`, `toml.py`
  - `ast_discovery.py`, `schema.py`, `defaults.py`
- **Documentacao de dependencias**: Grafo de dependencias internas no `settings/__init__.py`

### Changed
- **Type hints em `converters.py`**: Usa `get_origin()`/`get_args()` para deteccao de generics
  - Funciona corretamente com `tuple[float, float]` e `list[str]` (Python 3.9+)
  - Removida comparacao direta que nao funcionava com tipos genericos
- **Imports em `fonts.py`**: Consolidados para usar `from ..settings import get_config, get_assets_path`
- **Docstrings atualizadas**: Documentacao alinhada com comportamento de fallback silencioso

### Removed
- Dependencia de `logging` stdlib (substituido por `loguru`)
- Cache manual em `discovery.py` (substituido por `cachetools`)
- Cache manual em `loader.py` (substituido por `@cachedmethod`)

### Dependencies
- Adicionado `loguru>=0.7.3`
- Adicionado `cachetools>=6.2.6`

## [2026-01-30 01:09]
### Changed
- **Performance**: Adicionado cache module-level em `find_project_root()` para evitar I/O redundante
  - Ganho de 45-85x em chamadas repetidas (cache hit vs filesystem walk)
  - Nova funcao `reset_project_root_cache()` para limpeza em testes
- **Dependency Injection**: `PathResolver` agora aceita `project_root` injetado no construtor
  - Elimina chamadas repetidas a `find_project_root()` durante resolucao de paths
  - `ConfigLoader` passa `project_root` cacheado via property para os resolvers
- **Cache interno em ConfigLoader**: Property `project_root` agora usa lazy init com cache
  - Resolve project root uma unica vez por sessao

### Fixed
- **Exception handling em `toml.py`**: Erros de parsing/I/O agora sao logados em vez de silenciados
  - Captura `tomllib.TOMLDecodeError` para erros de sintaxe TOML
  - Captura `OSError/IOError` para erros de leitura de arquivo
  - Warnings visiveis ajudam usuario a identificar problemas em configs
- **Exception handling em `paths.py`**: Excecoes especificadas em vez de `except Exception`
  - TOML getters: `(KeyError, AttributeError, TypeError)`
  - Auto-discovery: `(OSError, ValueError)`
- **Dead code removido**: `import logging` e `logger` em `loader.py` (nunca eram usados)

### Added
- Logging em `discovery.py`, `toml.py` e `paths.py` para debugging
- Logs de debug mostram cache hits/misses e falhas de resolucao

## [2026-01-30 00:50]
### Added
- Sistema de auto-discovery de paths via AST parsing (`ast_discovery.py`)
  - Detecta `OUTPUTS_PATH` e `ASSETS_PATH` de projetos host analisando `config.py`
  - Suporta padroes comuns: `PROJECT_ROOT / 'data' / 'outputs'`, `Path('assets')`, etc
  - Parsing seguro sem importar modulos (evita side effects)
- Novo campo `assets_path` na configuracao `[fonts]` e `[paths].assets_dir`
- Funcao `get_assets_path()` exposta na API publica
- Constante `ASSETS_PATH` acessivel via `from chartkit import ASSETS_PATH`
- Classe `PathResolver` para resolucao unificada de paths com cadeia de precedencia

### Changed
- **Refatoracao do modulo settings**: loader.py dividido em modulos especializados
  - `toml.py`: utilitarios de parsing TOML e deep merge
  - `converters.py`: conversao dataclass <-> dict
  - `discovery.py`: descoberta de project root e arquivos de config
  - `paths.py`: estrategia unificada de resolucao de paths
  - `ast_discovery.py`: auto-discovery via AST
- Campo `[paths].default_output_dir` renomeado para `[paths].outputs_dir`
- Campo `[fonts].file` agora e relativo ao `assets_path` (antes era relativo a `assets/`)
- Removido campo `output_conventions` de PathsConfig (substituido por auto-discovery)

### Fixed
- Carregamento de fontes agora usa logging adequado em vez de falhar silenciosamente
- Mensagens de erro mais claras quando fonte nao e encontrada

### Docs
- Documentacao `configuration.md` atualizada com nova secao de auto-discovery
- Novos exemplos de configuracao explicita de paths
- Documentacao das funcoes `get_assets_path()` e `get_outputs_path()`
