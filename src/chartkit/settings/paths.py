"""Estrategia unificada para resolucao de paths."""

from pathlib import Path
from typing import Callable, Optional

from loguru import logger

from .discovery import find_project_root

__all__ = ["PathResolver"]


class PathResolver:
    """Resolve paths usando cadeia de precedencia.

    Ordem: API explicita > TOML > runtime discovery > AST discovery > fallback.
    Nunca levanta excecoes; retorna fallback silenciosamente se nenhuma fonte encontrada.
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
        self._name = name
        self._explicit = explicit_path
        self._toml_getters = toml_getters
        self._runtime_getter = runtime_getter
        self._ast_getter = ast_getter
        self._fallback_subdir = fallback_subdir
        self._project_root = (
            project_root if project_root is not None else find_project_root()
        )

    def resolve(self) -> Path:
        # 1. Configuracao explicita via API
        if self._explicit is not None:
            return self._explicit

        # 2. Configuracao no TOML
        for getter in self._toml_getters:
            try:
                toml_value = getter()
                if toml_value:
                    return self._resolve_relative(Path(toml_value))
            except (KeyError, AttributeError, TypeError) as e:
                logger.debug("{}: getter TOML falhou: {}", self._name, e)
                continue

        # 3. Runtime discovery via sys.modules
        try:
            runtime_path = self._runtime_getter()
            if runtime_path:
                logger.debug("{}: encontrado via runtime discovery", self._name)
                return runtime_path
        except Exception as e:
            logger.debug("{}: runtime discovery falhou: {}", self._name, e)

        # 4. Auto-discovery via AST
        try:
            ast_path = self._ast_getter()
            if ast_path:
                return ast_path
        except (OSError, ValueError) as e:
            logger.debug("{}: AST discovery falhou: {}", self._name, e)

        # 5. Fallback silencioso
        fallback_path = (self._project_root or Path.cwd()) / self._fallback_subdir
        logger.debug("{}: usando fallback silencioso: {}", self._name, fallback_path)
        return fallback_path

    def _resolve_relative(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        if self._project_root:
            return self._project_root / path
        return Path.cwd() / path
