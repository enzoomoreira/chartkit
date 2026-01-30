"""
Estrategia unificada para resolucao de paths.

Fornece a classe PathResolver que implementa a cadeia de precedencia
para resolver paths de outputs e assets de forma DRY.
"""

from pathlib import Path
from typing import Callable, Optional

from loguru import logger

from .discovery import find_project_root

__all__ = ["PathResolver"]


class PathResolver:
    """
    Resolve paths usando cadeia de precedencia.

    Ordem de precedencia:
        1. Configuracao explicita via API (configure)
        2. Configuracao no TOML
        3. Runtime discovery via sys.modules
        4. Auto-discovery via AST
        5. Fallback silencioso (sem warning, logado em DEBUG)

    Esta classe elimina a duplicacao de logica entre outputs_path e assets_path,
    encapsulando o padrao comum de resolucao.

    Example:
        >>> resolver = PathResolver(
        ...     name="OUTPUTS_PATH",
        ...     explicit_path=None,
        ...     toml_getters=[lambda: config.paths.outputs_dir],
        ...     runtime_getter=lambda: runtime.discover_outputs_path(),
        ...     ast_getter=lambda: discovery.outputs_path,
        ...     fallback_subdir="outputs",
        ... )
        >>> path = resolver.resolve()
    """

    def __init__(
        self,
        name: str,
        explicit_path: Optional[Path],
        toml_getters: list[Callable[[], Optional[str]]],
        runtime_getter: Callable[[], Optional[Path]],
        ast_getter: Callable[[], Optional[Path]],
        fallback_subdir: str,
        project_root: Optional[Path] = None,
    ):
        """
        Inicializa o resolver.

        Args:
            name: Nome do path para mensagens de warning (ex: "OUTPUTS_PATH").
            explicit_path: Path configurado explicitamente via API.
            toml_getters: Lista de funcoes que retornam path do TOML.
                         Sao chamadas em ordem ate encontrar um valor nao-vazio.
            runtime_getter: Funcao que retorna path via runtime discovery (sys.modules).
            ast_getter: Funcao que retorna path via AST auto-discovery.
            fallback_subdir: Subdiretorio para fallback (ex: "outputs", "assets").
            project_root: Project root injetado. Se None, sera descoberto uma unica vez.
        """
        self._name = name
        self._explicit = explicit_path
        self._toml_getters = toml_getters
        self._runtime_getter = runtime_getter
        self._ast_getter = ast_getter
        self._fallback_subdir = fallback_subdir
        # Resolve project_root uma unica vez no construtor (DI ou discovery)
        self._project_root = (
            project_root if project_root is not None else find_project_root()
        )

    def resolve(self) -> Path:
        """
        Resolve o path usando a cadeia de precedencia.

        Returns:
            Path resolvido. Sempre retorna um Path valido.

        Note:
            Nao levanta excecoes. Se nenhuma fonte encontrada,
            retorna fallback silenciosamente (logado em DEBUG).
        """
        # 1. Configuracao explicita via API
        if self._explicit is not None:
            return self._explicit

        # 2. Configuracao no TOML (tenta cada getter em ordem)
        for getter in self._toml_getters:
            try:
                toml_value = getter()
                if toml_value:
                    return self._resolve_relative(Path(toml_value))
            except (KeyError, AttributeError, TypeError) as e:
                # Getter pode falhar se config nao tiver a chave esperada
                logger.debug("{}: getter TOML falhou: {}", self._name, e)
                continue

        # 3. Runtime discovery via sys.modules
        try:
            runtime_path = self._runtime_getter()
            if runtime_path:
                logger.debug("{}: encontrado via runtime discovery", self._name)
                return runtime_path
        except Exception as e:
            # Runtime discovery nao deve quebrar o fluxo
            logger.debug("{}: runtime discovery falhou: {}", self._name, e)

        # 4. Auto-discovery via AST
        try:
            ast_path = self._ast_getter()
            if ast_path:
                return ast_path
        except (OSError, ValueError) as e:
            # AST discovery pode falhar em casos de I/O ou paths invalidos
            logger.debug("{}: AST discovery falhou: {}", self._name, e)

        # 5. Fallback silencioso (pasta sera criada quando necessario)
        fallback_path = (self._project_root or Path.cwd()) / self._fallback_subdir
        logger.debug("{}: usando fallback silencioso: {}", self._name, fallback_path)
        return fallback_path

    def _resolve_relative(self, path: Path) -> Path:
        """
        Resolve path relativo a partir do project root.

        Args:
            path: Path a resolver (pode ser absoluto ou relativo).

        Returns:
            Path absoluto resolvido.
        """
        if path.is_absolute():
            return path
        # Usa project_root cacheado no construtor
        if self._project_root:
            return self._project_root / path
        return Path.cwd() / path
