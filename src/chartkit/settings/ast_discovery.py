"""
Auto-discovery de OUTPUTS_PATH e ASSETS_PATH via AST parsing.

Analisa arquivos config.py de projetos host sem importar modulos,
evitando side effects e permitindo descoberta segura de paths.
"""

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredPaths:
    """Resultado do auto-discovery de paths."""

    outputs_path: Optional[Path] = None
    assets_path: Optional[Path] = None


class ASTPathDiscovery:
    """
    Descobre OUTPUTS_PATH e ASSETS_PATH de projetos host via AST.

    Analisa arquivos config.py sem importar modulos (evita side effects).
    Suporta padroes comuns de definicao de paths em projetos Python,
    incluindo variaveis intermediarias.

    Padroes suportados:
        - PROJECT_ROOT / 'data' / 'outputs'
        - DATA_PATH / 'outputs' (onde DATA_PATH = PROJECT_ROOT / 'data')
        - Path('data/outputs')
        - Path(__file__).parent / 'assets'
        - Constantes de string simples

    Example:
        >>> discovery = ASTPathDiscovery(project_root)
        >>> paths = discovery.discover()
        >>> print(paths.outputs_path)
    """

    # Padroes de arquivos config.py a procurar
    CONFIG_PATTERNS = [
        "src/*/core/config.py",
        "src/*/config.py",
        "*/core/config.py",
        "*/config.py",
        "config.py",
    ]

    def __init__(self, project_root: Path):
        """
        Inicializa o discoverer.

        Args:
            project_root: Raiz do projeto onde procurar config.py.
        """
        self._root = project_root
        self._cache: Optional[DiscoveredPaths] = None

    def discover(self) -> DiscoveredPaths:
        """
        Executa discovery e retorna paths encontrados.

        Usa cache para evitar reprocessamento de AST.

        Returns:
            DiscoveredPaths com outputs_path e assets_path encontrados.
        """
        if self._cache is not None:
            return self._cache

        self._cache = DiscoveredPaths()
        self._scan_config_files()
        return self._cache

    def _scan_config_files(self) -> None:
        """
        Escaneia arquivos config.py procurando por OUTPUTS_PATH e ASSETS_PATH.

        Procura em padroes comuns de localizacao e extrai as variaveis
        via parsing AST, resolvendo variaveis intermediarias.
        """
        for pattern in self.CONFIG_PATTERNS:
            for config_file in self._root.glob(pattern):
                try:
                    source = config_file.read_text(encoding="utf-8")

                    # Constroi mapa de variaveis para resolver referencias
                    var_map = self._build_path_var_map(source)

                    # Busca OUTPUTS_PATH e ASSETS_PATH no mapa
                    if "OUTPUTS_PATH" in var_map:
                        self._cache.outputs_path = var_map["OUTPUTS_PATH"]
                        logger.debug(
                            f"OUTPUTS_PATH descoberto via AST: {self._cache.outputs_path}"
                        )

                    if "ASSETS_PATH" in var_map:
                        self._cache.assets_path = var_map["ASSETS_PATH"]
                        logger.debug(
                            f"ASSETS_PATH descoberto via AST: {self._cache.assets_path}"
                        )

                    # Se encontrou ambos, para de procurar
                    if self._cache.outputs_path and self._cache.assets_path:
                        return

                except Exception as e:
                    logger.debug(f"Erro ao analisar {config_file}: {e}")
                    continue

    def _build_path_var_map(self, source: str) -> dict[str, Path]:
        """
        Constroi mapa de variaveis que representam Paths no arquivo.

        Analisa o arquivo e resolve variaveis na ordem de definicao.
        Variaveis como PROJECT_ROOT, DATA_PATH, etc sao mapeadas para Paths reais.

        Args:
            source: Codigo fonte do arquivo.

        Returns:
            Dicionario mapeando nome da variavel para Path resolvido.
        """
        # Variaveis conhecidas que apontam para root
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

            # Processa atribuicoes na ordem em que aparecem no arquivo
            # Usamos ast.walk que percorre todos os nodes, mas precisamos
            # processar na ordem correta. Vamos iterar pelo body do modulo.
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id

                            # Tenta resolver o valor usando variaveis ja conhecidas
                            resolved = self._resolve_path_expression(
                                node.value, var_map
                            )
                            if resolved:
                                var_map[var_name] = resolved

        except Exception as e:
            logger.debug(f"Erro ao construir mapa de variaveis: {e}")

        return var_map

    def _resolve_path_expression(
        self, node: ast.expr, var_map: dict[str, Path]
    ) -> Optional[Path]:
        """
        Resolve uma expressao AST para um Path usando mapa de variaveis.

        Args:
            node: Node AST a resolver.
            var_map: Mapa de variaveis ja resolvidas.

        Returns:
            Path resolvido ou None se nao conseguir.
        """
        try:
            # Caso: Nome de variavel simples
            if isinstance(node, ast.Name):
                if node.id in var_map:
                    return var_map[node.id]
                # Variavel desconhecida que parece ser root
                if "ROOT" in node.id.upper() or "BASE" in node.id.upper():
                    return self._root
                return None

            # Caso: String literal
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                path = Path(node.value)
                if path.is_absolute():
                    return path
                return self._root / path

            # Caso: BinOp com / (divisao de Path)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                # Resolve lado esquerdo recursivamente
                left_path = self._resolve_path_expression(node.left, var_map)
                if left_path is None:
                    return None

                # Resolve lado direito
                if isinstance(node.right, ast.Constant) and isinstance(
                    node.right.value, str
                ):
                    return left_path / node.right.value
                elif isinstance(node.right, ast.Name):
                    # Lado direito e uma variavel
                    if node.right.id in var_map:
                        right_path = var_map[node.right.id]
                        # Tenta usar como caminho relativo
                        try:
                            return left_path / str(right_path.relative_to(self._root))
                        except ValueError:
                            return left_path / right_path.name
                    return None

                return None

            # Caso: Chamada Path()
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "Path":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        path_str = node.args[0].value
                        if isinstance(path_str, str):
                            path = Path(path_str)
                            if path.is_absolute():
                                return path
                            return self._root / path

            # Caso: Chamada get_project_root() ou similar
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id.lower()
                    if "root" in func_name or "project" in func_name:
                        return self._root

            # Caso: Atributo (ex: Path(__file__).parent)
            if isinstance(node, ast.Attribute):
                # Para Path(__file__).parent, assumimos que aponta para o diretorio
                # do arquivo, que e uma aproximacao do root
                if node.attr in ("parent", "resolve"):
                    return self._root

        except Exception as e:
            logger.debug(f"Erro ao resolver expressao: {e}")

        return None
