# Project Changelog

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
