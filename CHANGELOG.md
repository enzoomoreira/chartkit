# Project Changelog

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
