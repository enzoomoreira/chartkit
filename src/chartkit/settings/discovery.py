"""Project root and config file discovery."""

from __future__ import annotations

import logging
import os
import sys
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = [
    "AUTO_CONFIG_ENV_VAR",
    "auto_config_enabled",
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

# Set to disable the walk up the directory tree entirely. Discovery reads
# whatever pyproject.toml it finds above the working directory, which is
# surprising for an application that only wants its own explicit settings.
AUTO_CONFIG_ENV_VAR = "CHARTKIT_NO_AUTO_CONFIG"

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def auto_config_enabled() -> bool:
    """Whether TOML auto-discovery should run."""
    return os.environ.get(AUTO_CONFIG_ENV_VAR, "").strip().lower() not in _TRUTHY


@lru_cache(maxsize=32)
def _find_project_root_cached(start: Path) -> Path | None:
    logger.debug("find_project_root: starting search from %s", start)

    current = start
    while current != current.parent:
        for marker in PROJECT_ROOT_MARKERS:
            if (current / marker).exists():
                logger.debug("find_project_root: found %s", current)
                return current
        current = current.parent

    logger.debug("find_project_root: no project root found")
    return None


def find_project_root(start_path: Path | None = None) -> Path | None:
    """Walk up the directory tree looking for project markers (cached).

    Resolution happens here rather than inside the cached function so the
    cache key is a concrete path -- ``None`` would otherwise pin the first
    working directory the process ever used.
    """
    start = (start_path or Path.cwd()).resolve()
    return _find_project_root_cached(start)


def reset_project_root_cache() -> None:
    _find_project_root_cached.cache_clear()
    logger.debug("find_project_root: cache cleared")


def get_user_config_dir() -> Path | None:
    """Return user config dir (Windows: %APPDATA%/chartkit, Linux: ~/.config/chartkit)."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "chartkit"
        return None
    return Path.home() / ".config" / "chartkit"


def find_config_files(project_root: Path | None = None) -> list[Path]:
    """Find config files in precedence order.

    Searches: .chartkit/config.toml in project, pyproject.toml [tool.chartkit],
    and user config. Returns an empty list when ``CHARTKIT_NO_AUTO_CONFIG`` is
    set, leaving only ``configure()`` and environment variables in play.
    """
    if not auto_config_enabled():
        logger.debug("find_config_files: skipped, %s is set", AUTO_CONFIG_ENV_VAR)
        return []

    config_files = []

    if project_root is None:
        project_root = find_project_root()

    search_dirs = [Path.cwd()]
    if project_root and project_root != Path.cwd():
        search_dirs.append(project_root)

    for dir_path in search_dirs:
        candidate = dir_path / ".chartkit" / "config.toml"
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
