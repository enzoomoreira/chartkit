# Internals

Detalhes de implementacao para desenvolvedores e contribuidores.

Este documento cobre decisoes de design, trade-offs e padroes internos
que nao afetam a API publica mas sao importantes para entender e
contribuir com o codigo.

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

Isso evita race conditions onde uma thread esta limpando o cache
enquanto outra esta inserindo/lendo valores.

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
- 32 entries suficiente para maioria dos casos de uso

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

---

## Estrategia de Logging

### Biblioteca: loguru

Usamos `loguru` em vez de `logging` stdlib por:
- API mais simples (`logger.debug()` vs `logging.getLogger().debug()`)
- Lazy evaluation built-in (evita formatacao desnecessaria)
- Melhor suporte a Unicode e cores no terminal

### Logging Desabilitado por Padrao

Seguindo best practices para bibliotecas Python, logging esta
desabilitado por padrao. Usuarios ativam explicitamente:

```python
from chartkit import configure_logging

# Ativa logs DEBUG
configure_logging(level="DEBUG")

# Ativa logs INFO
configure_logging(level="INFO")
```

### Lazy Evaluation

Usamos placeholders `{}` em vez de f-strings para evitar:
1. Formatacao desnecessaria quando log esta desabilitado
2. Problemas de encoding com caracteres especiais

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

Removemos logs excessivos dentro de loops para reduzir ruido:

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

Logs de operacoes repetitivas existem em nivel mais alto (ex: `loader.py`
loga o merge, nao cada campo individual).

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
(ex: Jupyter notebooks, web servers), cachetools oferece garantias
mais fortes.

### Por que RLock em vez de Lock?

`RLock` permite reentrancia - a mesma thread pode adquirir o lock
multiplas vezes. Isso e necessario porque:

```python
def get_config():
    # Pode chamar find_project_root() internamente
    # que tambem usa o mesmo lock pattern
    ...
```

Com `Lock` simples, isso causaria deadlock.

### Por que remover codigo morto agressivamente?

Codigo nao utilizado:
- Aumenta superficie de manutencao
- Confunde contribuidores ("isso e usado?")
- Pode ter bugs nao detectados

Funcoes internas como `_is_tuple_of_floats()` foram removidas quando
a implementacao foi refatorada para usar `get_origin()`/`get_args()`.

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

Usamos modulo-level instance:

```python
_loader = ConfigLoader()

def get_config():
    return _loader.get_config()
```

Razoes:
- Mais simples e explicito
- Facilita testes (pode criar instancias isoladas)
- Evita problemas com heranca

---

## Testes

### Limpando Caches em Testes

Testes que mudam diretorio de trabalho ou arquivos de config devem
limpar caches:

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

### Testando Thread-Safety

Para verificar comportamento concorrente:

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

## Performance

### Benchmarks Tipicos

| Operacao | Primeiro acesso | Cached |
|----------|-----------------|--------|
| `find_project_root()` | 1-5ms | 0.01ms |
| `get_config()` | 5-20ms | 0.01ms |
| `get_outputs_path()` | 2-10ms | 0.01ms |

### Otimizacoes Aplicadas

1. **Lazy init**: Nada e carregado ate primeiro uso
2. **Dependency injection**: `PathResolver` recebe `project_root` para evitar lookups repetidos
3. **TTL cache**: Paths resolvidos tem TTL de 1 hora
4. **Versionamento**: Invalidacao seletiva em vez de limpar tudo

### Quando Limpar Caches

- **Testes**: Sempre limpar entre testes
- **Hot reload**: Chamar `reset_config()` se arquivos TOML mudarem
- **Mudanca de cwd**: Chamar `reset_project_root_cache()`
