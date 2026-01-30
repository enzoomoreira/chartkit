"""
Descoberta de project root e arquivos de configuracao.

Fornece funcoes para localizar a raiz do projeto e encontrar
arquivos de configuracao em ordem de precedencia.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from .defaults import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

# Cache module-level para evitar I/O redundante em find_project_root
# Mapeia start_path -> project_root encontrado (ou None)
_project_root_cache: dict[Path, Optional[Path]] = {}


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Busca recursiva pelo project root usando markers comuns.

    Sobe a arvore de diretorios a partir de start_path (ou cwd) procurando
    por markers que indicam a raiz de um projeto Python.

    Utiliza cache module-level para evitar I/O redundante em chamadas
    repetidas com o mesmo start_path.

    Args:
        start_path: Diretorio inicial da busca. Se None, usa cwd.

    Returns:
        Path do project root se encontrado, None caso contrario.
    """
    markers = DEFAULT_CONFIG.paths.project_root_markers

    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Verifica cache antes de fazer I/O
    if current in _project_root_cache:
        logger.debug("find_project_root: cache hit para %s", current)
        return _project_root_cache[current]

    logger.debug("find_project_root: cache miss para %s, iniciando busca", current)

    # Sobe a arvore de diretorios ate a raiz do filesystem
    search_start = current
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                # Armazena no cache e retorna
                _project_root_cache[search_start] = current
                logger.debug("find_project_root: encontrado %s", current)
                return current
        current = current.parent

    # Nao encontrado - armazena None no cache
    _project_root_cache[search_start] = None
    logger.debug("find_project_root: nenhum project root encontrado")
    return None


def reset_project_root_cache() -> None:
    """
    Limpa o cache de project root.

    Util para testes ou quando o diretorio de trabalho muda.
    """
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
