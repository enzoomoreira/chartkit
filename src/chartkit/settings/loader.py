from pathlib import Path
from threading import RLock
from typing import Any, Optional

from cachetools import TTLCache, cachedmethod
from loguru import logger

from .ast_discovery import ASTPathDiscovery, DiscoveredPaths
from .converters import dataclass_to_dict, dict_to_dataclass
from .defaults import DEFAULT_CONFIG
from .discovery import find_config_files, find_project_root, reset_project_root_cache
from .paths import PathResolver
from .runtime_discovery import RuntimePathDiscovery
from .schema import ChartingConfig
from .toml import deep_merge, load_pyproject_section, load_toml

__all__ = [
    "ConfigLoader",
    "configure",
    "get_config",
    "reset_config",
    "get_outputs_path",
    "get_charts_path",
    "get_assets_path",
]


class ConfigLoader:
    """Carregador de configuracoes com cache, merge multi-fonte e path resolution."""

    def __init__(self) -> None:
        self._config: Optional[ChartingConfig] = None
        self._config_path: Optional[Path] = None
        self._overrides: dict = {}
        self._outputs_path: Optional[Path] = None
        self._assets_path: Optional[Path] = None
        self._ast_discovery: Optional[ASTPathDiscovery] = None
        self._runtime_discovery: RuntimePathDiscovery = RuntimePathDiscovery()

        self._project_root: Optional[Path] = None
        self._project_root_resolved: bool = False

        self._path_cache: TTLCache = TTLCache(maxsize=3, ttl=3600)
        self._cache_lock = RLock()
        self._cache_version = 0

    def _cache_key(self, name: str) -> tuple:
        return (name, self._cache_version)

    @cachedmethod(
        cache=lambda self: self._path_cache,
        key=lambda self: self._cache_key("outputs"),
        lock=lambda self: self._cache_lock,
    )
    def _resolve_outputs_path(self) -> Path:
        logger.debug("Resolvendo outputs_path (cache miss)")
        config = self.get_config()
        resolver = PathResolver(
            name="OUTPUTS_PATH",
            explicit_path=self._outputs_path,
            toml_getters=[lambda: config.paths.outputs_dir],
            runtime_getter=self._runtime_discovery.discover_outputs_path,
            ast_getter=lambda: self._get_ast_discovery().outputs_path,
            fallback_subdir="outputs",
            project_root=self.project_root,
        )
        return resolver.resolve()

    @cachedmethod(
        cache=lambda self: self._path_cache,
        key=lambda self: self._cache_key("assets"),
        lock=lambda self: self._cache_lock,
    )
    def _resolve_assets_path(self) -> Path:
        logger.debug("Resolvendo assets_path (cache miss)")
        config = self.get_config()
        resolver = PathResolver(
            name="ASSETS_PATH",
            explicit_path=self._assets_path,
            toml_getters=[
                lambda: config.fonts.assets_path,
                lambda: config.paths.assets_dir,
            ],
            runtime_getter=self._runtime_discovery.discover_assets_path,
            ast_getter=lambda: self._get_ast_discovery().assets_path,
            fallback_subdir="assets",
            project_root=self.project_root,
        )
        return resolver.resolve()

    def _clear_caches(self) -> None:
        self._path_cache.clear()
        self._config = None
        self._ast_discovery = None
        self._runtime_discovery.clear_cache()
        self._project_root = None
        self._project_root_resolved = False
        self._cache_version += 1
        logger.debug("Caches do ConfigLoader limpos (versao={})", self._cache_version)

    def configure(
        self,
        config_path: Optional[Path] = None,
        outputs_path: Optional[Path] = None,
        assets_path: Optional[Path] = None,
        **overrides: Any,
    ) -> "ConfigLoader":
        """Configura o carregador com opcoes explicitas.

        Args:
            **overrides: Dicts aninhados merged na config.
                Ex: ``branding={'company_name': 'Banco XYZ'}``
        """
        logger.debug(
            "configure() chamado: config_path={}, outputs_path={}, assets_path={}",
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
            self._overrides = deep_merge(self._overrides, overrides)
            logger.debug("Overrides aplicados: {}", list(overrides.keys()))

        self._clear_caches()

        return self

    def reset(self) -> "ConfigLoader":
        """Reseta todas as configuracoes para o estado inicial."""
        logger.debug("reset() chamado - limpando todas as configuracoes")

        self._config_path = None
        self._overrides = {}
        self._outputs_path = None
        self._assets_path = None

        self._clear_caches()
        reset_project_root_cache()

        return self

    def get_config(self) -> ChartingConfig:
        """Retorna a configuracao atual, carregando e mergeando se necessario."""
        if self._config is not None:
            return self._config

        logger.debug("Carregando configuracoes (cache miss)")

        config_dict = dataclass_to_dict(DEFAULT_CONFIG)

        config_files = find_config_files()

        if self._config_path and self._config_path.exists():
            config_files.insert(0, self._config_path)
            logger.debug("Arquivo de config explicito: {}", self._config_path)

        # Merge em ordem reversa (menor prioridade primeiro)
        for config_file in reversed(config_files):
            if config_file.name == "pyproject.toml":
                file_config = load_pyproject_section(config_file)
            else:
                file_config = load_toml(config_file)

            if file_config:
                config_dict = deep_merge(config_dict, file_config)
                logger.debug("Config merged de: {}", config_file)

        if self._overrides:
            config_dict = deep_merge(config_dict, self._overrides)
            logger.debug("Overrides programaticos aplicados")

        self._config = dict_to_dataclass(ChartingConfig, config_dict)

        return self._config

    def _get_ast_discovery(self) -> DiscoveredPaths:
        root = find_project_root()
        if not root:
            return DiscoveredPaths()

        if self._ast_discovery is None:
            logger.debug("Inicializando ASTPathDiscovery para: {}", root)
            self._ast_discovery = ASTPathDiscovery(root)

        return self._ast_discovery.discover()

    @property
    def outputs_path(self) -> Path:
        """Resolve outputs_path via cadeia: API > TOML > runtime > AST > fallback."""
        return self._resolve_outputs_path()

    @property
    def assets_path(self) -> Path:
        """Resolve assets_path via cadeia: API > TOML > runtime > AST > fallback."""
        return self._resolve_assets_path()

    @property
    def charts_path(self) -> Path:
        config = self.get_config()
        return self.outputs_path / config.paths.charts_subdir

    @property
    def project_root(self) -> Optional[Path]:
        if not self._project_root_resolved:
            self._project_root = find_project_root()
            self._project_root_resolved = True
        return self._project_root


_loader = ConfigLoader()


def configure(
    config_path: Optional[Path] = None,
    outputs_path: Optional[Path] = None,
    assets_path: Optional[Path] = None,
    **overrides: Any,
) -> ConfigLoader:
    """Configura o chartkit com paths explicitos e/ou overrides de secoes.

    Args:
        **overrides: Dicts aninhados merged na config.
            Ex: ``branding={'company_name': 'Banco XYZ'}``
    """
    return _loader.configure(
        config_path=config_path,
        outputs_path=outputs_path,
        assets_path=assets_path,
        **overrides,
    )


def get_config() -> ChartingConfig:
    """Retorna a configuracao atual (carrega automaticamente na primeira chamada)."""
    return _loader.get_config()


def get_outputs_path() -> Path:
    return _loader.outputs_path


def get_charts_path() -> Path:
    return _loader.charts_path


def get_assets_path() -> Path:
    return _loader.assets_path


def reset_config() -> ConfigLoader:
    """Reseta todas as configuracoes para o estado inicial."""
    return _loader.reset()
