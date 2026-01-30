"""
Carregador de configuracoes TOML.

Implementa carregamento de configuracoes de multiplas fontes com
ordem de precedencia definida e merge profundo de dicionarios.

Ordem de precedencia (maior para menor):
    1. configure() - Configuracao explicita pelo usuario
    2. .charting.toml / charting.toml - Projeto local
    3. pyproject.toml [tool.charting] - Secao no pyproject
    4. ~/.config/charting/config.toml - Usuario global (Linux/Mac)
    5. %APPDATA%/charting/config.toml - Usuario global (Windows)
    6. Defaults built-in
"""

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
    """
    Carregador de configuracoes com cache.

    Gerencia o carregamento de configuracoes de multiplas fontes,
    fazendo merge e mantendo cache para evitar recarregamentos.

    Attributes:
        _config: Configuracao atual cacheada.
        _config_path: Caminho explicito para arquivo de configuracao.
        _overrides: Overrides programaticos via configure().
        _outputs_path: Caminho explicito para outputs.
        _assets_path: Caminho explicito para assets.
    """

    def __init__(self) -> None:
        """Inicializa o loader sem configuracao carregada."""
        self._config: Optional[ChartingConfig] = None
        self._config_path: Optional[Path] = None
        self._overrides: dict = {}
        self._outputs_path: Optional[Path] = None
        self._assets_path: Optional[Path] = None
        self._ast_discovery: Optional[ASTPathDiscovery] = None
        self._runtime_discovery: RuntimePathDiscovery = RuntimePathDiscovery()

        # Cache interno para project_root (lazy init)
        self._project_root: Optional[Path] = None
        self._project_root_resolved: bool = False

        # Caches com TTL de 1 hora para paths resolvidos
        self._path_cache: TTLCache = TTLCache(maxsize=3, ttl=3600)
        self._cache_lock = RLock()

        # Versao do cache para invalidacao
        self._cache_version = 0

    def _cache_key(self, name: str) -> tuple:
        """
        Gera chave de cache baseada no estado atual.

        Inclui versao do cache para invalidacao automatica quando
        configuracoes mudam.
        """
        return (name, self._cache_version)

    @cachedmethod(
        cache=lambda self: self._path_cache,
        key=lambda self: self._cache_key("outputs"),
        lock=lambda self: self._cache_lock,
    )
    def _resolve_outputs_path(self) -> Path:
        """Resolve outputs_path (cacheado internamente)."""
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
        """Resolve assets_path (cacheado internamente)."""
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
        """Limpa todos os caches internos."""
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
        """
        Configura o carregador com opcoes explicitas.

        Args:
            config_path: Caminho explicito para arquivo TOML de configuracao.
            outputs_path: Caminho explicito para diretorio de outputs.
            assets_path: Caminho explicito para diretorio de assets.
            **overrides: Overrides para secoes especificas da configuracao.
                        Aceita dicionarios aninhados que serao merged.
                        Ex: branding={'company_name': 'Minha Empresa'}

        Returns:
            Self para encadeamento.

        Example:
            >>> configure(branding={'company_name': 'Banco XYZ'})
            >>> configure(config_path=Path('./minha-config.toml'))
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

        # Invalida caches para forcar recarga
        self._clear_caches()

        return self

    def reset(self) -> "ConfigLoader":
        """
        Reseta todas as configuracoes para o estado inicial.

        Returns:
            Self para encadeamento.
        """
        logger.debug("reset() chamado - limpando todas as configuracoes")

        self._config_path = None
        self._overrides = {}
        self._outputs_path = None
        self._assets_path = None

        # Limpa caches internos
        self._clear_caches()

        # Limpa cache global de project root
        reset_project_root_cache()

        return self

    def get_config(self) -> ChartingConfig:
        """
        Retorna a configuracao atual, carregando se necessario.

        Ordem de precedencia para merge:
            1. Overrides via configure()
            2. Arquivo explicito via config_path
            3. .charting.toml / charting.toml no projeto
            4. pyproject.toml [tool.charting]
            5. Config do usuario (~/.config/charting/config.toml)
            6. Defaults built-in

        Returns:
            ChartingConfig com todas as configuracoes merged.
        """
        if self._config is not None:
            return self._config

        logger.debug("Carregando configuracoes (cache miss)")

        # Comeca com defaults
        config_dict = dataclass_to_dict(DEFAULT_CONFIG)

        # Carrega arquivos de configuracao (em ordem de precedencia reversa)
        config_files = find_config_files()

        # Arquivo explicito tem maior prioridade que auto-descobertos
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

        # Overrides programaticos tem maior prioridade
        if self._overrides:
            config_dict = deep_merge(config_dict, self._overrides)
            logger.debug("Overrides programaticos aplicados")

        # Converte para dataclass
        self._config = dict_to_dataclass(ChartingConfig, config_dict)

        return self._config

    def _get_ast_discovery(self) -> DiscoveredPaths:
        """
        Retorna paths descobertos via AST (lazy init).

        Returns:
            DiscoveredPaths com outputs_path e assets_path descobertos.
        """
        root = find_project_root()
        if not root:
            return DiscoveredPaths()

        if self._ast_discovery is None:
            logger.debug("Inicializando ASTPathDiscovery para: {}", root)
            self._ast_discovery = ASTPathDiscovery(root)

        return self._ast_discovery.discover()

    @property
    def outputs_path(self) -> Path:
        """
        Retorna o path base para outputs.

        Ordem de precedencia:
            1. Configuracao explicita via configure(outputs_path=...)
            2. Configuracao no TOML ([paths].outputs_dir)
            3. Runtime discovery via sys.modules (busca OUTPUTS_PATH em modulos importados)
            4. Auto-discovery do OUTPUTS_PATH do projeto host via AST
            5. Fallback silencioso: project_root / 'outputs'

        Ative logging DEBUG para ver qual fonte foi usada.
        """
        return self._resolve_outputs_path()

    @property
    def assets_path(self) -> Path:
        """
        Retorna o path base para assets.

        Ordem de precedencia:
            1. Configuracao explicita via configure(assets_path=...)
            2. Configuracao no TOML ([fonts].assets_path ou [paths].assets_dir)
            3. Runtime discovery via sys.modules (busca ASSETS_PATH em modulos importados)
            4. Auto-discovery do ASSETS_PATH do projeto host via AST
            5. Fallback silencioso: project_root / 'assets'

        Ative logging DEBUG para ver qual fonte foi usada.
        """
        return self._resolve_assets_path()

    @property
    def charts_path(self) -> Path:
        """Retorna o caminho completo para salvar graficos."""
        config = self.get_config()
        return self.outputs_path / config.paths.charts_subdir

    @property
    def project_root(self) -> Optional[Path]:
        """
        Retorna o project root detectado (com cache interno).

        O project root e resolvido uma unica vez e cacheado para evitar
        chamadas repetidas a find_project_root() durante a sessao.
        """
        if not self._project_root_resolved:
            self._project_root = find_project_root()
            self._project_root_resolved = True
        return self._project_root


# Instancia singleton global
_loader = ConfigLoader()


# --- Public API ---


def configure(
    config_path: Optional[Path] = None,
    outputs_path: Optional[Path] = None,
    assets_path: Optional[Path] = None,
    **overrides: Any,
) -> ConfigLoader:
    """
    Configura o modulo chartkit.

    Esta funcao permite configuracao explicita, sobrescrevendo
    auto-discovery de arquivos TOML.

    Args:
        config_path: Caminho explicito para arquivo TOML de configuracao.
        outputs_path: Caminho explicito para diretorio de outputs.
        assets_path: Caminho explicito para diretorio de assets (fontes, etc).
        **overrides: Overrides para secoes especificas da configuracao.
                    Aceita dicionarios aninhados que serao merged.

    Returns:
        Instancia do ConfigLoader configurado.

    Example:
        # Usando arquivo de configuracao
        >>> configure(config_path=Path('./minha-config.toml'))

        # Usando overrides programaticos
        >>> configure(branding={'company_name': 'Banco XYZ'})
        >>> configure(colors={'primary': '#FF0000'})

        # Combinando ambos
        >>> configure(
        ...     config_path=Path('./base.toml'),
        ...     branding={'company_name': 'Override'}
        ... )
    """
    return _loader.configure(
        config_path=config_path,
        outputs_path=outputs_path,
        assets_path=assets_path,
        **overrides,
    )


def get_config() -> ChartingConfig:
    """
    Retorna a configuracao atual.

    Carrega configuracoes de arquivos TOML automaticamente na primeira
    chamada, fazendo merge com defaults e overrides.

    Returns:
        ChartingConfig com todas as configuracoes.

    Example:
        >>> config = get_config()
        >>> print(config.colors.primary)
        '#00464D'
    """
    return _loader.get_config()


def get_outputs_path() -> Path:
    """Retorna o path base para outputs."""
    return _loader.outputs_path


def get_charts_path() -> Path:
    """Retorna o caminho completo para salvar graficos."""
    return _loader.charts_path


def get_assets_path() -> Path:
    """Retorna o path base para assets (fontes, imagens, etc)."""
    return _loader.assets_path


def reset_config() -> ConfigLoader:
    """
    Reseta todas as configuracoes para o estado inicial.

    Util para testes ou quando precisar reconfigurar do zero.

    Returns:
        Instancia do ConfigLoader resetado.
    """
    return _loader.reset()
