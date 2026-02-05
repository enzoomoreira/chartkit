"""Descobre paths de outputs e assets em modulos ja importados via sys.modules."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

__all__ = ["RuntimePathDiscovery"]


class RuntimePathDiscovery:
    """Busca OUTPUTS_PATH e ASSETS_PATH em sys.modules.

    Permite que bibliotecas host exponham paths automaticamente ao serem
    importadas, sem configuracao explicita.
    """

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
        # Terceiros comuns sem paths de projeto
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
        "chartkit",
    )

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
        self._cache: dict[str, Optional[Path]] = {}

    def discover_outputs_path(self) -> Optional[Path]:
        return self._discover_var("OUTPUTS_PATH")

    def discover_assets_path(self) -> Optional[Path]:
        return self._discover_var("ASSETS_PATH")

    def _should_skip_module(self, module_name: str) -> bool:
        if module_name in self.SKIP_MODULES:
            return True

        for prefix in self.SKIP_PREFIXES:
            if module_name == prefix or module_name.startswith(f"{prefix}."):
                return True

        return False

    def _discover_var(self, var_name: str) -> Optional[Path]:
        """Busca variavel em todos os modulos importados (cacheado)."""
        if var_name in self._cache:
            logger.debug("{}: usando cache ({})", var_name, self._cache[var_name])
            return self._cache[var_name]

        for module_name, module in list(sys.modules.items()):
            if self._should_skip_module(module_name):
                continue

            if module is None:
                continue

            value = getattr(module, var_name, None)

            if value is not None:
                if isinstance(value, Path):
                    path = value
                elif isinstance(value, str):
                    path = Path(value)
                else:
                    continue

                if str(path):
                    logger.debug(
                        "{} descoberto via runtime em modulo '{}': {}",
                        var_name,
                        module_name,
                        path,
                    )
                    self._cache[var_name] = path
                    return path

        logger.debug("{}: nao encontrado em sys.modules", var_name)
        self._cache[var_name] = None
        return None

    def clear_cache(self) -> None:
        self._cache.clear()
        logger.debug("RuntimePathDiscovery: cache limpo")
