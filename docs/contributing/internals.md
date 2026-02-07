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
def find_project_root(start_path: Path | None = None) -> Path | None:
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

A biblioteca usa cache simples com invalidacao por flag:

```
+---------------------------+
|  ConfigLoader._config     |  None flag (invalida via _invalidate())
+---------------------------+
            |
            v
+---------------------------+
|  _project_root_cache      |  LRUCache (32 entries, thread-safe)
+---------------------------+
            |
            v
+---------------------------+
|  Filesystem               |  I/O real
+---------------------------+
```

### Cache de Project Root

**Tipo:** `LRUCache(maxsize=32)` com `RLock`

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

### Cache de Config

**Tipo:** Flag simples (`_config: ChartingConfig | None`)

O `ConfigLoader` usa `_config = None` como flag de invalidacao. Quando
`configure()` ou `reset()` sao chamados, `_invalidate()` seta `_config = None`
e a proxima chamada a `get_config()` reconstroi o objeto pydantic:

```python
def _invalidate(self) -> None:
    self._config = None
    self._project_root = None
    self._project_root_resolved = False
    ChartingConfig._toml_data = {}
```

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
| `loader.py` | Config files merged, overrides aplicados | - | Erros de TOML parsing |
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

## Resolucao de Paths

O `ConfigLoader` resolve paths usando uma cadeia 3-tier inline:

1. **Configuracao explicita** via `configure(outputs_path=...)`
2. **Config (TOML/env)** (`[paths].outputs_dir` ou `CHARTKIT_PATHS__OUTPUTS_DIR`)
3. **Fallback** (`project_root / subdir`)

```python
# Em loader.py
@property
def outputs_path(self) -> Path:
    if self._outputs_path is not None:
        return self._outputs_path                    # 1. Explicito
    config = self.get_config()
    if config.paths.outputs_dir:
        return self._resolve_relative(Path(config.paths.outputs_dir))  # 2. Config
    return (find_project_root() or Path.cwd()) / "outputs"  # 3. Fallback
```

Paths relativos sao resolvidos contra o project root via `_resolve_relative()`.

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
2. **LRUCache**: `find_project_root()` cacheado com 32 entries
3. **Flag simples**: `_config = None` evita reconstrucao desnecessaria do objeto pydantic
4. **Lazy project_root**: Property no ConfigLoader com flag `_project_root_resolved`

### Dicas para Contribuidores

- Use `get_config()` dentro de funcoes, nao no modulo level
- Evite loops com I/O dentro de funcoes frequentes
- Prefira lazy evaluation para valores opcionais
- Documente complexidade (O(n)) quando relevante
