"""
Utilitarios para parsing de arquivos TOML.

Fornece funcoes para carregar arquivos TOML e fazer merge
profundo de dicionarios de configuracao.
"""

import sys
from copy import deepcopy
from pathlib import Path

from loguru import logger

__all__ = ["deep_merge", "load_toml", "load_pyproject_section"]

# Compatibilidade com Python < 3.11
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore


def deep_merge(base: dict, override: dict) -> dict:
    """
    Faz merge profundo de dois dicionarios.

    Valores em override sobrescrevem valores em base. Para dicionarios
    aninhados, o merge e feito recursivamente.

    Args:
        base: Dicionario base com valores default.
        override: Dicionario com valores para sobrescrever.

    Returns:
        Novo dicionario com merge dos dois.

    Example:
        >>> base = {'colors': {'primary': '#000'}, 'layout': {'dpi': 100}}
        >>> override = {'colors': {'primary': '#FFF'}}
        >>> deep_merge(base, override)
        {'colors': {'primary': '#FFF'}, 'layout': {'dpi': 100}}
    """
    result = deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def load_toml(path: Path) -> dict:
    """
    Carrega arquivo TOML e retorna como dicionario.

    Args:
        path: Caminho para o arquivo TOML.

    Returns:
        Dicionario com conteudo do arquivo, ou {} se nao existir,
        tomllib nao estiver disponivel, ou ocorrer erro de parsing/I/O.
    """
    if tomllib is None:
        logger.warning("tomllib nao disponivel - instale tomli para Python < 3.11")
        return {}

    if not path.exists():
        return {}

    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        # Erro de sintaxe no TOML - usuario precisa corrigir
        logger.warning("Erro de sintaxe TOML em {}: {}", path, e)
        return {}
    except (OSError, IOError) as e:
        # Erro de I/O (permissao, arquivo corrompido, etc)
        logger.warning("Erro ao ler arquivo TOML {}: {}", path, e)
        return {}


def load_pyproject_section(path: Path, section: str = "charting") -> dict:
    """
    Carrega secao [tool.{section}] de um pyproject.toml.

    Args:
        path: Caminho para o pyproject.toml.
        section: Nome da secao dentro de [tool]. Default: "charting".

    Returns:
        Dicionario com conteudo de [tool.{section}], ou {} se nao existir.
    """
    data = load_toml(path)
    return data.get("tool", {}).get(section, {})
