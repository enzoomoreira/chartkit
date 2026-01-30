"""
Descobre paths de outputs e assets em modulos ja importados.

Este modulo implementa runtime discovery, que busca variaveis OUTPUTS_PATH
e ASSETS_PATH em sys.modules - modulos que ja foram importados pelo processo.

Isso permite que bibliotecas host (como adb) exponham seus paths automaticamente
ao serem importadas, sem necessidade de configuracao explicita.

Exemplo de uso esperado:
    # Em adb/__init__.py
    from adb.config import OUTPUTS_PATH  # Expoe no namespace

    # Em qualquer script
    import adb          # OUTPUTS_PATH ja esta em sys.modules['adb']
    import chartkit     # chartkit.OUTPUTS_PATH pega de adb automaticamente
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

__all__ = ["RuntimePathDiscovery"]


class RuntimePathDiscovery:
    """
    Descobre OUTPUTS_PATH e ASSETS_PATH de modulos ja importados.

    Busca em sys.modules por atributos definidos em runtime,
    permitindo que bibliotecas host exponham seus paths
    automaticamente ao serem importadas.

    A busca ignora modulos internos do Python (stdlib) e pacotes
    conhecidos que nao devem conter paths de projeto.

    Attributes:
        SKIP_PREFIXES: Prefixos de modulos a ignorar na busca.
        SKIP_MODULES: Nomes exatos de modulos a ignorar.
    """

    # Prefixos de modulos a ignorar (stdlib, internos)
    SKIP_PREFIXES: tuple[str, ...] = (
        "_",
        "builtins",
        "sys",
        "os",
        "pathlib",
        "typing",
        "collections",
        "functools",
        "itertools",
        "importlib",
        "abc",
        "io",
        "re",
        "json",
        "logging",
        "warnings",
        "traceback",
        "inspect",
        "types",
        "copy",
        "weakref",
        "contextlib",
        "dataclasses",
        "enum",
        "threading",
        "multiprocessing",
        "concurrent",
        "asyncio",
        "socket",
        "ssl",
        "http",
        "urllib",
        "email",
        "html",
        "xml",
        "sqlite3",
        "hashlib",
        "hmac",
        "secrets",
        "random",
        "statistics",
        "math",
        "decimal",
        "fractions",
        "datetime",
        "time",
        "calendar",
        "zoneinfo",
        "locale",
        "gettext",
        "struct",
        "codecs",
        "unicodedata",
        "pickle",
        "shelve",
        "marshal",
        "dbm",
        "csv",
        "configparser",
        "tomllib",
        "netrc",
        "plistlib",
        "errno",
        "ctypes",
        "platform",
        "shutil",
        "tempfile",
        "glob",
        "fnmatch",
        "linecache",
        "token",
        "tokenize",
        "ast",
        "dis",
        "pdb",
        "profile",
        "pstats",
        "timeit",
        "unittest",
        "doctest",
        "test",
        "argparse",
        "textwrap",
        "difflib",
        "string",
        "operator",
        # Pacotes de terceiros comuns que nao tem paths de projeto
        "numpy",
        "pandas",
        "matplotlib",
        "plotly",
        "seaborn",
        "scipy",
        "sklearn",
        "PIL",
        "cv2",
        "requests",
        "httpx",
        "aiohttp",
        "flask",
        "fastapi",
        "django",
        "starlette",
        "uvicorn",
        "gunicorn",
        "celery",
        "redis",
        "sqlalchemy",
        "alembic",
        "pydantic",
        "attrs",
        "loguru",
        "rich",
        "click",
        "typer",
        "pytest",
        "coverage",
        "setuptools",
        "pip",
        "wheel",
        "pkg_resources",
        "cachetools",
        "toml",
        "tomli",
        "yaml",
        "dotenv",
        "babel",
        # O proprio chartkit nao deve ser fonte
        "chartkit",
    )

    # Modulos exatos a ignorar
    SKIP_MODULES: frozenset[str] = frozenset(
        {
            "antigravity",
            "this",
            "__main__",
            "__mp_main__",
            "site",
            "sitecustomize",
            "usercustomize",
        }
    )

    def __init__(self) -> None:
        """Inicializa o descobridor com cache vazio."""
        self._cache: dict[str, Optional[Path]] = {}

    def discover_outputs_path(self) -> Optional[Path]:
        """
        Busca OUTPUTS_PATH em modulos importados.

        Returns:
            Path descoberto ou None se nao encontrado.
        """
        return self._discover_var("OUTPUTS_PATH")

    def discover_assets_path(self) -> Optional[Path]:
        """
        Busca ASSETS_PATH em modulos importados.

        Returns:
            Path descoberto ou None se nao encontrado.
        """
        return self._discover_var("ASSETS_PATH")

    def _should_skip_module(self, module_name: str) -> bool:
        """
        Verifica se um modulo deve ser ignorado na busca.

        Args:
            module_name: Nome do modulo a verificar.

        Returns:
            True se o modulo deve ser ignorado.
        """
        # Modulos exatos a ignorar
        if module_name in self.SKIP_MODULES:
            return True

        # Modulos com prefixos conhecidos
        for prefix in self.SKIP_PREFIXES:
            if module_name == prefix or module_name.startswith(f"{prefix}."):
                return True

        return False

    def _discover_var(self, var_name: str) -> Optional[Path]:
        """
        Busca uma variavel em todos os modulos importados.

        Args:
            var_name: Nome da variavel a buscar (ex: "OUTPUTS_PATH").

        Returns:
            Path descoberto ou None se nao encontrado.
        """
        if var_name in self._cache:
            logger.debug("{}: usando cache ({})", var_name, self._cache[var_name])
            return self._cache[var_name]

        # Itera sobre copia da lista para evitar RuntimeError
        for module_name, module in list(sys.modules.items()):
            # Pula modulos internos/stdlib/terceiros conhecidos
            if self._should_skip_module(module_name):
                continue

            # Modulos podem ser None durante import
            if module is None:
                continue

            # Procura o atributo no modulo
            value = getattr(module, var_name, None)

            if value is not None:
                # Aceita Path ou str
                if isinstance(value, Path):
                    path = value
                elif isinstance(value, str):
                    path = Path(value)
                else:
                    continue

                # Valida que e um path razoavel (nao vazio)
                if str(path):
                    logger.debug(
                        "{} descoberto via runtime em modulo '{}': {}",
                        var_name,
                        module_name,
                        path,
                    )
                    self._cache[var_name] = path
                    return path

        # Nao encontrado em nenhum modulo
        logger.debug("{}: nao encontrado em sys.modules", var_name)
        self._cache[var_name] = None
        return None

    def clear_cache(self) -> None:
        """Limpa o cache de descoberta."""
        self._cache.clear()
        logger.debug("RuntimePathDiscovery: cache limpo")
