"""Utilitarios para parsing de arquivos TOML."""

import sys
from copy import deepcopy
from pathlib import Path

from loguru import logger

__all__ = ["deep_merge", "load_toml", "load_pyproject_section"]

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore


def deep_merge(base: dict, override: dict) -> dict:
    """Merge profundo de dicts (override sobrescreve base, recursivo para sub-dicts)."""
    result = deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def load_toml(path: Path) -> dict:
    """Carrega TOML. Retorna ``{}`` se nao existir ou houver erro."""
    if tomllib is None:
        logger.warning("tomllib nao disponivel - instale tomli para Python < 3.11")
        return {}

    if not path.exists():
        return {}

    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        logger.warning("Erro de sintaxe TOML em {}: {}", path, e)
        return {}
    except (OSError, IOError) as e:
        logger.warning("Erro ao ler arquivo TOML {}: {}", path, e)
        return {}


def load_pyproject_section(path: Path, section: str = "charting") -> dict:
    """Carrega secao ``[tool.{section}]`` de um pyproject.toml."""
    data = load_toml(path)
    return data.get("tool", {}).get(section, {})
