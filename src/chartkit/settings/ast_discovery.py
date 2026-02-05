"""Auto-discovery de OUTPUTS_PATH e ASSETS_PATH via AST parsing.

Analisa arquivos config.py sem importar modulos, evitando side effects.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from loguru import logger

__all__ = ["ASTPathDiscovery", "DiscoveredPaths"]


@dataclass
class DiscoveredPaths:
    outputs_path: Optional[Path] = None
    assets_path: Optional[Path] = None


class ASTPathDiscovery:
    """Descobre paths de projetos host analisando config.py via AST.

    Padroes suportados: ``ROOT / 'outputs'``, ``Path('data/outputs')``,
    ``Path(__file__).parent``, variaveis intermediarias.
    """

    SKIP_DIRS: frozenset[str] = frozenset(
        {
            ".venv",
            "venv",
            ".env",
            "env",
            ".git",
            ".hg",
            ".svn",
            "__pycache__",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".tox",
            ".nox",
            "node_modules",
            "bower_components",
            "dist",
            "build",
            "eggs",
            "*.egg-info",
            ".eggs",
            "site-packages",
            "chartkit",
        }
    )

    def __init__(self, project_root: Path):
        self._root = project_root
        self._cache: Optional[DiscoveredPaths] = None

    def discover(self) -> DiscoveredPaths:
        if self._cache is not None:
            return self._cache

        self._cache = DiscoveredPaths()
        self._scan_config_files()
        return self._cache

    def _find_config_files(self) -> Iterator[Path]:
        """Busca config.py recursivamente, ordenado por profundidade (rasos primeiro)."""
        config_files: list[tuple[int, Path]] = []

        for path in self._root.rglob("config.py"):
            parts = path.relative_to(self._root).parts
            if any(part in self.SKIP_DIRS for part in parts[:-1]):
                continue

            depth = len(parts) - 1
            config_files.append((depth, path))

        config_files.sort(key=lambda x: x[0])

        for _, path in config_files:
            yield path

    def _scan_config_files(self) -> None:
        for config_file in self._find_config_files():
            try:
                source = config_file.read_text(encoding="utf-8")
                var_map = self._build_path_var_map(source)

                if "OUTPUTS_PATH" in var_map:
                    self._cache.outputs_path = var_map["OUTPUTS_PATH"]
                    logger.debug(
                        "OUTPUTS_PATH descoberto via AST em {}: {}",
                        config_file,
                        self._cache.outputs_path,
                    )

                if "ASSETS_PATH" in var_map:
                    self._cache.assets_path = var_map["ASSETS_PATH"]
                    logger.debug(
                        "ASSETS_PATH descoberto via AST em {}: {}",
                        config_file,
                        self._cache.assets_path,
                    )

                if self._cache.outputs_path and self._cache.assets_path:
                    return

            except Exception as e:
                logger.debug("Erro ao analisar {}: {}", config_file, e)
                continue

    def _build_path_var_map(self, source: str) -> dict[str, Path]:
        """Constroi mapa de variaveis que representam Paths, resolvendo referencias."""
        var_map: dict[str, Path] = {
            "PROJECT_ROOT": self._root,
            "ROOT": self._root,
            "BASE_DIR": self._root,
            "BASE_PATH": self._root,
            "ROOT_DIR": self._root,
            "ROOT_PATH": self._root,
        }

        try:
            tree = ast.parse(source)

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            resolved = self._resolve_path_expression(
                                node.value, var_map
                            )
                            if resolved:
                                var_map[target.id] = resolved

        except Exception as e:
            logger.debug("Erro ao construir mapa de variaveis: {}", e)

        return var_map

    def _resolve_path_expression(
        self, node: ast.expr, var_map: dict[str, Path]
    ) -> Optional[Path]:
        try:
            # Nome de variavel
            if isinstance(node, ast.Name):
                if node.id in var_map:
                    return var_map[node.id]
                if "ROOT" in node.id.upper() or "BASE" in node.id.upper():
                    return self._root
                return None

            # String literal
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                path = Path(node.value)
                if path.is_absolute():
                    return path
                return self._root / path

            # BinOp com / (Path division)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                left_path = self._resolve_path_expression(node.left, var_map)
                if left_path is None:
                    return None

                if isinstance(node.right, ast.Constant) and isinstance(
                    node.right.value, str
                ):
                    return left_path / node.right.value
                elif isinstance(node.right, ast.Name):
                    if node.right.id in var_map:
                        right_path = var_map[node.right.id]
                        try:
                            return left_path / str(right_path.relative_to(self._root))
                        except ValueError:
                            return left_path / right_path.name
                    return None

                return None

            # Chamada Path()
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "Path":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        path_str = node.args[0].value
                        if isinstance(path_str, str):
                            path = Path(path_str)
                            if path.is_absolute():
                                return path
                            return self._root / path

            # Chamada get_project_root() ou similar
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id.lower()
                    if "root" in func_name or "project" in func_name:
                        return self._root

            # Atributo (Path(__file__).parent)
            if isinstance(node, ast.Attribute):
                if node.attr in ("parent", "resolve"):
                    return self._root

        except Exception as e:
            logger.debug("Erro ao resolver expressao: {}", e)

        return None
