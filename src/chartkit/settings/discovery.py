"""
Descoberta de project root e arquivos de configuracao.

Fornece funcoes para localizar a raiz do projeto e encontrar
arquivos de configuracao em ordem de precedencia.
"""

import os
import sys
from pathlib import Path
from threading import RLock
from typing import Optional

from cachetools import LRUCache, cached
from loguru import logger

from .defaults import DEFAULT_CONFIG

__all__ = [
    "find_project_root",
    "find_config_files",
    "get_user_config_dir",
    "reset_project_root_cache",
]

# Cache thread-safe com limite de 32 entries
_project_root_lock = RLock()
_project_root_cache: LRUCache = LRUCache(maxsize=32)


def _cache_key(start_path: Optional[Path] = None) -> Path:
    """Gera chave de cache normalizada."""
    if start_path is None:
        return Path.cwd().resolve()
    return start_path.resolve()


@cached(cache=_project_root_cache, key=_cache_key, lock=_project_root_lock)
def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Busca recursiva pelo project root usando markers comuns.

    Sobe a arvore de diretorios a partir de start_path (ou cwd) procurando
    por markers que indicam a raiz de um projeto Python.

    Cache e automaticamente gerenciado pelo decorator @cached.
    Use reset_project_root_cache() para limpar manualmente.

    Args:
        start_path: Diretorio inicial da busca. Se None, usa cwd.

    Returns:
        Path do project root se encontrado, None caso contrario.
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    markers = DEFAULT_CONFIG.paths.project_root_markers

    logger.debug("find_project_root: iniciando busca a partir de {}", current)

    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                logger.debug("find_project_root: encontrado {}", current)
                return current
        current = current.parent

    logger.debug("find_project_root: nenhum project root encontrado")
    return None


def reset_project_root_cache() -> None:
    """
    Limpa o cache de project root.

    Util para testes ou quando o diretorio de trabalho muda.
    """
    with _project_root_lock:
        _project_root_cache.clear()
    logger.debug("find_project_root: cache limpo")


def get_user_config_dir() -> Optional[Path]:
    """
    Retorna diretorio de configuracao do usuario baseado no OS.

    Returns:
        Path para diretorio de config do usuario, ou None se nao disponivel.
        - Windows: %APPDATA%/charting
        - Linux/Mac: ~/.config/charting
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "charting"
        return None
    return Path.home() / ".config" / "charting"


def find_config_files(project_root: Optional[Path] = None) -> list[Path]:
    """
    Encontra arquivos de configuracao em ordem de precedencia.

    Procura em:
        1. Diretorio atual e project root (.charting.toml, charting.toml)
        2. pyproject.toml no project root
        3. Diretorio de configuracao do usuario

    Args:
        project_root: Raiz do projeto. Se None, sera detectada automaticamente.

    Returns:
        Lista de paths de arquivos existentes, em ordem de precedencia
        (primeiro = maior prioridade).
    """
    config_files = []

    # Detecta project root se nao fornecido
    if project_root is None:
        project_root = find_project_root()

    # 1. Projeto local
    search_dirs = [Path.cwd()]
    if project_root and project_root != Path.cwd():
        search_dirs.append(project_root)

    for dir_path in search_dirs:
        for name in [".charting.toml", "charting.toml"]:
            candidate = dir_path / name
            if candidate.exists():
                config_files.append(candidate)

    # 2. pyproject.toml (verificado separadamente pois precisa da secao [tool.charting])
    if project_root:
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            config_files.append(pyproject)

    # 3. Diretorio de configuracao do usuario
    user_config_dir = get_user_config_dir()
    if user_config_dir:
        user_config = user_config_dir / "config.toml"
        if user_config.exists():
            config_files.append(user_config)

    return config_files
