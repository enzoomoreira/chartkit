"""Project root and config file discovery."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from threading import RLock

from cachetools import LRUCache, cached
from loguru import logger

__all__ = [
    "find_project_root",
    "find_config_files",
    "get_user_config_dir",
    "reset_project_root_cache",
]

PROJECT_ROOT_MARKERS: tuple[str, ...] = (
    ".git",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    ".project-root",
)

_project_root_lock = RLock()
_project_root_cache: LRUCache = LRUCache(maxsize=32)


def _cache_key(start_path: Path | None = None) -> Path:
    if start_path is None:
        return Path.cwd().resolve()
    return start_path.resolve()


@cached(cache=_project_root_cache, key=_cache_key, lock=_project_root_lock)
def find_project_root(start_path: Path | None = None) -> Path | None:
    """Walk up the directory tree looking for project markers (cached)."""
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    logger.debug("find_project_root: starting search from {}", current)

    while current != current.parent:
        for marker in PROJECT_ROOT_MARKERS:
            if (current / marker).exists():
                logger.debug("find_project_root: found {}", current)
                return current
        current = current.parent

    logger.debug("find_project_root: no project root found")
    return None


def reset_project_root_cache() -> None:
    with _project_root_lock:
        _project_root_cache.clear()
    logger.debug("find_project_root: cache cleared")


def get_user_config_dir() -> Path | None:
    """Return user config dir (Windows: %APPDATA%/charting, Linux: ~/.config/charting)."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "charting"
        return None
    return Path.home() / ".config" / "charting"


def find_config_files(project_root: Path | None = None) -> list[Path]:
    """Find config files in precedence order.

    Searches: .charting.toml/charting.toml in project, pyproject.toml [tool.charting],
    and user config.
    """
    config_files = []

    if project_root is None:
        project_root = find_project_root()

    search_dirs = [Path.cwd()]
    if project_root and project_root != Path.cwd():
        search_dirs.append(project_root)

    for dir_path in search_dirs:
        for name in [".charting.toml", "charting.toml"]:
            candidate = dir_path / name
            if candidate.exists():
                config_files.append(candidate)

    if project_root:
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            config_files.append(pyproject)

    user_config_dir = get_user_config_dir()
    if user_config_dir:
        user_config = user_config_dir / "config.toml"
        if user_config.exists():
            config_files.append(user_config)

    return config_files
