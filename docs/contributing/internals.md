# Internals

Detalhes de implementacao interna do chartkit para desenvolvedores avancados.

Este documento cobre decisoes de design, mecanismos de performance,
e padroes internos que nao afetam a API publica mas sao importantes
para contribuir com o codigo.

---

## Thread-Safety

A biblioteca e thread-safe para uso concorrente. Todos os caches
compartilhados usam locks para evitar race conditions.

### Locks Utilizados

| Modulo | Lock | Protege |
|--------|------|---------|
| `discovery.py` | `RLock` | `_project_root_cache` (LRUCache) |
| `loader.py` | `RLock` | `_path_cache` (TTLCache) |

### Padrao de Uso

Usamos `RLock` (reentrant lock) em vez de `Lock` simples porque:
- Permite que a mesma thread adquira o lock multiplas vezes
- Evita deadlocks em chamadas recursivas (ex: `get_config()` -> `find_project_root()`)

```python
from threading import RLock
from cachetools import LRUCache, cached

_lock = RLock()
_cache: LRUCache = LRUCache(maxsize=32)

@cached(cache=_cache, lock=_lock)
def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    ...
```

### Limpeza de Cache Thread-Safe

A funcao `reset_project_root_cache()` adquire o lock antes de limpar:

```python
def reset_project_root_cache() -> None:
    with _project_root_lock:
        _project_root_cache.clear()
```

Isso evita race conditions onde uma thread limpa o cache enquanto
outra insere/le valores.

### Testando Thread-Safety

```python
import threading
from chartkit.settings import get_config

def test_concurrent_access():
    errors = []

    def worker():
        try:
            for _ in range(100):
                config = get_config()
                assert config is not None
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
```

---

## Sistema de Caching

### Niveis de Cache

A biblioteca implementa multiplos niveis de cache para minimizar I/O:

```
+---------------------------+
|  ConfigLoader._path_cache |  TTLCache (1h TTL, 3 entries)
+---------------------------+
            |
            v
+---------------------------+
|  _project_root_cache      |  LRUCache (32 entries)
+---------------------------+
            |
            v
+---------------------------+
|  Filesystem               |  I/O real
+---------------------------+
```

### Cache de Project Root

**Tipo:** `LRUCache(maxsize=32)`

**Chave:** Path absoluto normalizado (start_path ou cwd)

**Razao:**
- Evita traversal repetido do filesystem
- Ganho de 45-85x em chamadas repetidas
- 32 entries suficiente para maioria dos casos

```python
# Primeira chamada: ~1-5ms (filesystem walk)
root = find_project_root()

# Chamadas subsequentes: ~0.01ms (cache hit)
root = find_project_root()
```

### Cache de Paths Resolvidos

**Tipo:** `TTLCache(maxsize=3, ttl=3600)`

**Entries:**
- `outputs_path`
- `assets_path`
- (reserva para extensao)

**Razao para TTL de 1 hora:**
- Paths raramente mudam durante uma sessao
- TTL permite recarregar se arquivos de config mudarem
- 1 hora balanceia performance vs freshness

### Invalidacao de Cache

O `ConfigLoader` usa versionamento para invalidacao:

```python
class ConfigLoader:
    def __init__(self):
        self._cache_version = 0

    def _cache_key(self, name: str) -> tuple:
        return (name, self._cache_version)

    def _clear_caches(self) -> None:
        self._path_cache.clear()
        self._cache_version += 1  # Invalida chaves antigas
```

Quando `configure()` ou `reset()` sao chamados:
1. Caches sao limpos
2. Versao e incrementada
3. Proximas chamadas tem cache miss

### Benchmarks Tipicos

| Operacao | Primeiro acesso | Cached |
|----------|-----------------|--------|
| `find_project_root()` | 1-5ms | 0.01ms |
| `get_config()` | 5-20ms | 0.01ms |
| `get_outputs_path()` | 2-10ms | 0.01ms |

---

## Sistema de Logging

### Biblioteca: loguru

Usamos `loguru` em vez de `logging` stdlib por:
- API mais simples (`logger.debug()` vs `logging.getLogger().debug()`)
- Lazy evaluation built-in (evita formatacao desnecessaria)
- Melhor suporte a Unicode e cores no terminal

### Desabilitado por Padrao

Seguindo best practices para bibliotecas Python, logging esta
desabilitado por padrao:

```python
# Em __init__.py
from loguru import logger
logger.disable("chartkit")
```

### Ativando Logs

```python
from chartkit import configure_logging

# Ativa logs DEBUG
configure_logging(level="DEBUG")

# Ativa logs INFO para stderr
configure_logging(level="INFO")

# Direciona para arquivo
configure_logging(level="DEBUG", sink="chartkit.log")
```

### Implementacao de configure_logging()

```python
def configure_logging(level: str = "DEBUG", sink=None) -> None:
    """
    Ativa logging da biblioteca chartkit.

    Args:
        level: Nivel minimo (DEBUG, INFO, WARNING, ERROR).
        sink: Destino opcional (arquivo, stream). Se None, usa stderr.

    Example:
        >>> from chartkit import configure_logging
        >>> configure_logging(level="DEBUG")
    """
    logger.enable("chartkit")
    if sink:
        logger.add(sink, level=level)
```

### Lazy Evaluation

Usamos placeholders `{}` em vez de f-strings para evitar formatacao
desnecessaria quando log esta desabilitado:

```python
# CORRETO: lazy evaluation
logger.debug("find_project_root: encontrado {}", current)

# INCORRETO: formata sempre, mesmo se DEBUG desabilitado
logger.debug(f"find_project_root: encontrado {current}")
```

### Niveis de Log por Modulo

| Modulo | DEBUG | INFO | WARNING |
|--------|-------|------|---------|
| `discovery.py` | Cache hits/misses, paths encontrados | - | - |
| `loader.py` | Config files merged, cache stats | - | - |
| `paths.py` | Resolucao de paths, fallbacks | - | Paths nao encontrados |
| `toml.py` | - | - | Erros de parsing |
| `fonts.py` | - | - | Fonte nao encontrada |

### Logging Conservador

Logs excessivos dentro de loops foram removidos para reduzir ruido:

```python
# ANTES (excessivo)
def dict_to_dataclass(cls, data):
    for field in fields(cls):
        logger.debug("Convertendo campo {}", field.name)  # N logs por chamada
        ...

# DEPOIS (conservador)
def dict_to_dataclass(cls, data):
    logger.debug("Convertendo {} campos", len(fields(cls)))  # 1 log por chamada
    ...
```

---

## Auto-Discovery de Paths via AST

O chartkit pode descobrir automaticamente OUTPUTS_PATH e ASSETS_PATH
de projetos host sem importar modulos (evitando side effects).

### Classe ASTPathDiscovery

```python
from chartkit.settings.ast_discovery import ASTPathDiscovery, DiscoveredPaths

discovery = ASTPathDiscovery(project_root)
paths = discovery.discover()

print(paths.outputs_path)  # Path ou None
print(paths.assets_path)   # Path ou None
```

### Padroes de Arquivos Procurados

```python
CONFIG_PATTERNS = [
    "src/*/core/config.py",
    "src/*/config.py",
    "*/core/config.py",
    "*/config.py",
    "config.py",
]
```

### Padroes de Codigo Suportados

O parser AST reconhece varios padroes comuns:

```python
# Path com operador /
OUTPUTS_PATH = PROJECT_ROOT / 'data' / 'outputs'

# Via variavel intermediaria
DATA_PATH = PROJECT_ROOT / 'data'
OUTPUTS_PATH = DATA_PATH / 'outputs'

# Path() explicito
ASSETS_PATH = Path('assets')

# Path relativo a __file__
ASSETS_PATH = Path(__file__).parent / 'assets'

# Funcoes get_*_root()
PROJECT_ROOT = get_project_root()
```

### Variaveis de Root Conhecidas

O parser reconhece automaticamente estas variaveis como apontando para root:

```python
_ROOT_VARS = {
    "PROJECT_ROOT",
    "ROOT",
    "BASE_DIR",
    "BASE_PATH",
    "ROOT_DIR",
    "ROOT_PATH",
}
```

### Cadeia de Precedencia para Paths

O `PathResolver` resolve paths na seguinte ordem:

1. **Configuracao explicita** via `configure(outputs_path=...)`
2. **TOML** (`[paths].outputs_dir` ou `[fonts].assets_path`)
3. **Auto-discovery AST**
4. **Fallback** (`project_root / subdir`)

```python
# Em loader.py
resolver = PathResolver(
    name="OUTPUTS_PATH",
    explicit_path=self._outputs_path,            # 1. Explicito
    toml_getters=[lambda: config.paths.outputs_dir],  # 2. TOML
    discovery_getter=lambda: self._get_ast_discovery().outputs_path,  # 3. AST
    fallback_subdir="outputs",                   # 4. Fallback
    project_root=self.project_root,
)
return resolver.resolve()
```

---

## Formatadores Babel

O chartkit usa a biblioteca Babel para internacionalizacao de
formatadores monetarios e numericos.

### Por que Babel?

- Suporte a qualquer codigo ISO 4217 (BRL, USD, EUR, GBP, JPY, etc.)
- Formatacao correta por locale (separadores, posicao do simbolo)
- Notacao compacta nativa (1k, 1mi, 1bi)

### Formatadores Disponiveis

| Formatador | Uso | Exemplo |
|------------|-----|---------|
| `currency_formatter('BRL')` | Valores monetarios | R$ 1.234,56 |
| `currency_formatter('USD')` | Dolares | US$ 1,234.56 |
| `compact_currency_formatter('BRL')` | Valores grandes | R$ 1,2 mi |
| `percent_formatter()` | Porcentagens | 10,5% |
| `human_readable_formatter()` | Notacao K/M/B | 1,5M |
| `points_formatter()` | Numeros com milhar | 1.234.567 |

### Configuracao de Locale

O locale e configurado via settings:

```toml
# .charting.toml
[formatters.locale]
babel_locale = "pt_BR"
decimal = ","
thousands = "."
```

```python
# Acesso programatico
config = get_config()
locale = config.formatters.locale.babel_locale  # "pt_BR"
```

### Implementacao de currency_formatter

```python
from babel.numbers import format_currency as babel_format_currency
from matplotlib.ticker import FuncFormatter
from ..settings import get_config

def currency_formatter(currency: str = "BRL"):
    """
    Formatador para valores monetarios usando Babel.

    Args:
        currency: Codigo ISO 4217 da moeda.

    Returns:
        FuncFormatter para uso com matplotlib.
    """
    config = get_config()
    locale = config.formatters.locale.babel_locale

    def _format(x, pos):
        return babel_format_currency(
            x,
            currency,
            locale=locale,
            currency_digits=True,
            group_separator=True,
        )

    return FuncFormatter(_format)
```

### Formatadores Compactos

Para valores grandes (milhoes, bilhoes), use formatadores compactos:

```python
from chartkit.styling import compact_currency_formatter

# R$ 1,2 mi (para 1.234.567)
ax.yaxis.set_major_formatter(compact_currency_formatter('BRL'))
```

---

## Decisoes de Design

### Por que cachetools em vez de functools.lru_cache?

| Aspecto | functools.lru_cache | cachetools |
|---------|---------------------|------------|
| Thread-safety | Nao built-in | Lock parameter |
| TTL | Nao suporta | TTLCache |
| Controle de cache | Limitado | clear(), maxsize, etc |
| Typed keys | Nao | Sim |

Para uma biblioteca que pode ser usada em contextos multi-thread
(Jupyter notebooks, web servers), cachetools oferece garantias mais fortes.

### Por que RLock em vez de Lock?

`RLock` permite reentrancia - a mesma thread pode adquirir o lock
multiplas vezes. Necessario porque:

```python
def get_config():
    # Pode chamar find_project_root() internamente
    # que tambem usa lock pattern
    ...
```

Com `Lock` simples, isso causaria deadlock.

### Por que nao usar singleton pattern classico?

Em vez de:

```python
class ConfigLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

Usamos module-level instance:

```python
_loader = ConfigLoader()

def get_config():
    return _loader.get_config()
```

Razoes:
- Mais simples e explicito
- Facilita testes (pode criar instancias isoladas)
- Evita problemas com heranca

### Por que loguru em vez de logging stdlib?

- Menos boilerplate (um import, pronto para usar)
- Lazy evaluation nativa com `{}`
- Melhor formatacao default
- Facil de desabilitar (`logger.disable()`)

---

## Limpando Caches em Testes

Testes que mudam diretorio de trabalho ou arquivos de config devem limpar caches:

```python
import pytest
from chartkit.settings import reset_config
from chartkit.settings.discovery import reset_project_root_cache

@pytest.fixture(autouse=True)
def clean_state():
    yield
    reset_config()
    reset_project_root_cache()
```

### Quando Limpar Caches

- **Testes**: Sempre limpar entre testes
- **Hot reload**: Chamar `reset_config()` se arquivos TOML mudarem
- **Mudanca de cwd**: Chamar `reset_project_root_cache()`

---

## Performance

### Otimizacoes Aplicadas

1. **Lazy init**: Nada e carregado ate primeiro uso
2. **Dependency injection**: PathResolver recebe project_root para evitar lookups
3. **TTL cache**: Paths resolvidos tem TTL de 1 hora
4. **Versionamento**: Invalidacao seletiva em vez de limpar tudo
5. **AST discovery cacheado**: Parsing AST acontece uma vez por sessao

### Dicas para Contribuidores

- Use `get_config()` dentro de funcoes, nao no modulo level
- Evite loops com I/O dentro de funcoes frequentes
- Prefira lazy evaluation para valores opcionais
- Documente complexidade (O(n)) quando relevante
