"""Configuration loader with TOML loading and path resolution."""

from __future__ import annotations

import tomllib
from copy import deepcopy
from pathlib import Path
from typing import Any

from loguru import logger

from .discovery import find_config_files, find_project_root, reset_project_root_cache
from .schema import ChartingConfig

__all__ = [
    "ConfigLoader",
    "configure",
    "get_config",
    "reset_config",
    "get_outputs_path",
    "get_charts_path",
    "get_assets_path",
]


def _load_toml(path: Path) -> dict[str, Any]:
    """Load TOML, return {} on error."""
    if not path.exists():
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError) as e:
        logger.warning("Error reading {}: {}", path, e)
        return {}


def _load_pyproject_section(path: Path) -> dict[str, Any]:
    return _load_toml(path).get("tool", {}).get("charting", {})


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class ConfigLoader:
    """Configuration loader with multi-source merge and path resolution."""

    def __init__(self) -> None:
        self._config: ChartingConfig | None = None
        self._config_path: Path | None = None
        self._overrides: dict[str, Any] = {}
        self._outputs_path: Path | None = None
        self._assets_path: Path | None = None
        self._project_root: Path | None = None
        self._project_root_resolved: bool = False

    def configure(
        self,
        config_path: Path | None = None,
        outputs_path: Path | None = None,
        assets_path: Path | None = None,
        **overrides: Any,
    ) -> ConfigLoader:
        """Configure the loader with explicit options.

        Args:
            **overrides: Nested dicts merged into the config.
                Ex: ``branding={'company_name': 'Banco XYZ'}``
        """
        logger.debug(
            "configure() called: config_path={}, outputs_path={}, assets_path={}",
            config_path,
            outputs_path,
            assets_path,
        )

        if config_path is not None:
            self._config_path = Path(config_path)

        if outputs_path is not None:
            self._outputs_path = Path(outputs_path)

        if assets_path is not None:
            self._assets_path = Path(assets_path)

        if overrides:
            self._overrides = _deep_merge(self._overrides, overrides)
            logger.debug("Overrides applied: {}", list(overrides.keys()))

        self._invalidate()

        return self

    def reset(self) -> ConfigLoader:
        """Reset all settings to initial state."""
        logger.debug("reset() called - clearing all settings")

        self._config_path = None
        self._overrides = {}
        self._outputs_path = None
        self._assets_path = None

        self._invalidate()
        reset_project_root_cache()

        return self

    def get_config(self) -> ChartingConfig:
        """Return the current configuration, loading and merging if needed."""
        if self._config is not None:
            return self._config

        logger.debug("Loading settings (cache miss)")

        toml_data = self._load_merged_toml()

        ChartingConfig._toml_data = toml_data

        self._config = ChartingConfig(**self._overrides)

        return self._config

    @property
    def outputs_path(self) -> Path:
        """Resolve outputs_path: explicit API > Config (TOML/env) > Fallback."""
        if self._outputs_path is not None:
            return self._outputs_path
        config = self.get_config()
        if config.paths.outputs_dir:
            return self._resolve_relative(Path(config.paths.outputs_dir))
        return (find_project_root() or Path.cwd()) / "outputs"

    @property
    def assets_path(self) -> Path:
        """Resolve assets_path: explicit API > Config (TOML/env) > Fallback."""
        if self._assets_path is not None:
            return self._assets_path
        config = self.get_config()
        if config.paths.assets_dir:
            return self._resolve_relative(Path(config.paths.assets_dir))
        return (find_project_root() or Path.cwd()) / "assets"

    @property
    def charts_path(self) -> Path:
        config = self.get_config()
        return self.outputs_path / config.paths.charts_subdir

    @property
    def project_root(self) -> Path | None:
        if not self._project_root_resolved:
            self._project_root = find_project_root()
            self._project_root_resolved = True
        return self._project_root

    def _invalidate(self) -> None:
        self._config = None
        self._project_root = None
        self._project_root_resolved = False
        ChartingConfig._toml_data = {}

    def _load_merged_toml(self) -> dict[str, Any]:
        """Discover and merge all TOML files in precedence order."""
        config_files = find_config_files()

        if self._config_path and self._config_path.exists():
            config_files.insert(0, self._config_path)
            logger.debug("Explicit config file: {}", self._config_path)

        merged: dict[str, Any] = {}

        for config_file in reversed(config_files):
            if config_file.name == "pyproject.toml":
                file_config = _load_pyproject_section(config_file)
            else:
                file_config = _load_toml(config_file)

            if file_config:
                merged = _deep_merge(merged, file_config)
                logger.debug("Config merged from: {}", config_file)

        return merged

    def _resolve_relative(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        root = self.project_root
        if root:
            return root / path
        return Path.cwd() / path


_loader = ConfigLoader()


def configure(
    config_path: Path | None = None,
    outputs_path: Path | None = None,
    assets_path: Path | None = None,
    **overrides: Any,
) -> ConfigLoader:
    """Configure chartkit with explicit paths and/or section overrides.

    Args:
        **overrides: Nested dicts merged into the config.
            Ex: ``branding={'company_name': 'Banco XYZ'}``
    """
    return _loader.configure(
        config_path=config_path,
        outputs_path=outputs_path,
        assets_path=assets_path,
        **overrides,
    )


def get_config() -> ChartingConfig:
    """Return the current configuration (loads automatically on first call)."""
    return _loader.get_config()


def get_outputs_path() -> Path:
    return _loader.outputs_path


def get_charts_path() -> Path:
    return _loader.charts_path


def get_assets_path() -> Path:
    return _loader.assets_path


def reset_config() -> ConfigLoader:
    """Reset all settings to initial state."""
    return _loader.reset()
