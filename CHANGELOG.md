# Project Changelog

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
