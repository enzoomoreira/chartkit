# Project Changelog

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
