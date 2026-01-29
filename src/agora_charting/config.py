"""
Sistema de configuracao com auto-discovery.

Este modulo implementa deteccao automatica do project root usando markers
comuns (pyproject.toml, .git, etc) e convencoes de pastas de output.

Ordem de precedencia (maior para menor):
    1. configure() - Configuracao explicita pelo usuario
    2. AGORA_CHARTING_* - Variaveis de ambiente
    3. Auto-discovery - Detecta project root e usa convencoes
    4. Fallback - cwd/outputs/charts

Uso:
    # Automatico (funciona na maioria dos casos)
    from agora_charting.config import CHARTS_PATH

    # Manual (quando precisar customizar)
    from agora_charting import configure
    configure(outputs_path=Path('./meu_path'))

    # Via variavel de ambiente
    # $env:AGORA_CHARTING_OUTPUTS_PATH = "C:/custom/path"
"""

from pathlib import Path
from dataclasses import dataclass, field
import os
from typing import Optional


# Markers para detectar raiz do projeto (ordem de prioridade)
PROJECT_ROOT_MARKERS = [
    ".git",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    ".project-root",  # Marker explicito para casos especiais
]

# Convencoes de pastas de output (ordem de preferencia)
OUTPUT_DIR_CONVENTIONS = [
    "outputs",
    "data/outputs",
    "output",
    "data/output",
]


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Busca recursiva pelo project root usando markers comuns.

    Sobe a arvore de diretorios a partir de start_path (ou cwd) procurando
    por markers que indicam a raiz de um projeto Python.

    Args:
        start_path: Diretorio inicial da busca. Se None, usa cwd.

    Returns:
        Path do project root se encontrado, None caso contrario.

    Example:
        >>> find_project_root()
        PosixPath('/home/user/meu-projeto')

        >>> find_project_root(Path('/home/user/meu-projeto/src/modulo'))
        PosixPath('/home/user/meu-projeto')
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Sobe a arvore de diretorios ate a raiz do filesystem
    while current != current.parent:
        for marker in PROJECT_ROOT_MARKERS:
            if (current / marker).exists():
                return current
        current = current.parent

    return None


def find_outputs_dir(root: Path) -> Path:
    """
    Encontra diretorio de outputs seguindo convencoes comuns.

    Procura por pastas de output existentes no projeto. Se nenhuma
    for encontrada, retorna o path default 'outputs' (sem criar).

    Args:
        root: Path do project root.

    Returns:
        Path para o diretorio de outputs (existente ou default).

    Example:
        >>> find_outputs_dir(Path('/home/user/projeto'))
        PosixPath('/home/user/projeto/outputs')  # se existir

        >>> find_outputs_dir(Path('/home/user/projeto'))
        PosixPath('/home/user/projeto/data/outputs')  # se outputs/ nao existir
    """
    for convention in OUTPUT_DIR_CONVENTIONS:
        candidate = root / convention
        if candidate.exists() and candidate.is_dir():
            return candidate

    # Nenhuma convencao encontrada, usa default
    return root / "outputs"


@dataclass
class ChartingSettings:
    """
    Configuracoes globais do modulo de charting.

    Implementa lazy evaluation para paths, calculando-os apenas quando
    acessados. Suporta configuracao explicita, env vars e auto-discovery.

    Attributes:
        charts_path: Path completo para salvar graficos (read-only property)
        outputs_path: Path base para outputs (read-only property)
        project_root: Path do projeto detectado (read-only property)
    """

    _outputs_path: Optional[Path] = field(default=None, repr=False)
    _charts_subdir: str = field(default="charts")
    _project_root: Optional[Path] = field(default=None, repr=False)
    _project_root_searched: bool = field(default=False, repr=False)
    _initialized: bool = field(default=False, repr=False)

    @property
    def project_root(self) -> Optional[Path]:
        """
        Retorna o project root detectado (lazy evaluation).

        Busca uma unica vez e cacheia o resultado. Retorna None se
        nenhum marker de projeto for encontrado.
        """
        if not self._project_root_searched:
            self._project_root = find_project_root()
            self._project_root_searched = True
        return self._project_root

    @property
    def outputs_path(self) -> Path:
        """
        Retorna o path base para outputs.

        Ordem de precedencia:
            1. Configuracao explicita via configure()
            2. Variavel de ambiente AGORA_CHARTING_OUTPUTS_PATH
            3. Auto-discovery baseado no project root
            4. Fallback: cwd/outputs
        """
        # 1. Configuracao explicita
        if self._outputs_path is not None:
            return self._outputs_path

        # 2. Variavel de ambiente
        env_path = os.environ.get("AGORA_CHARTING_OUTPUTS_PATH")
        if env_path:
            return Path(env_path)

        # 3. Auto-discovery
        root = self.project_root
        if root:
            return find_outputs_dir(root)

        # 4. Fallback
        return Path.cwd() / "outputs"

    @property
    def charts_path(self) -> Path:
        """Caminho completo para salvar graficos."""
        return self.outputs_path / self._charts_subdir

    def configure(
        self,
        outputs_path: Optional[Path] = None,
        charts_subdir: Optional[str] = None,
    ) -> "ChartingSettings":
        """
        Configura os paths do modulo explicitamente.

        Configuracoes feitas aqui tem prioridade maxima sobre env vars
        e auto-discovery.

        Args:
            outputs_path: Path base para o diretorio de outputs.
            charts_subdir: Subdiretorio dentro de outputs para charts.
                          Default: 'charts'.

        Returns:
            Self para permitir encadeamento.

        Example:
            >>> from agora_charting import configure
            >>> configure(outputs_path=Path('./data'))
            >>> configure(outputs_path=Path('./data'), charts_subdir='graficos')
        """
        if outputs_path is not None:
            self._outputs_path = Path(outputs_path)
        if charts_subdir is not None:
            self._charts_subdir = charts_subdir
        self._initialized = True
        return self

    def reset(self) -> "ChartingSettings":
        """
        Reseta todas as configuracoes para o estado inicial.

        Util para testes ou quando precisar reconfigurar do zero.

        Returns:
            Self para permitir encadeamento.
        """
        self._outputs_path = None
        self._charts_subdir = "charts"
        self._project_root = None
        self._project_root_searched = False
        self._initialized = False
        return self


# Instancia global singleton
_settings = ChartingSettings()


def configure(
    outputs_path: Optional[Path] = None,
    charts_subdir: Optional[str] = None,
) -> ChartingSettings:
    """
    Configura o modulo agora_charting.

    Esta funcao permite configuracao explicita dos paths, sobrescrevendo
    auto-discovery e variaveis de ambiente.

    Args:
        outputs_path: Path base para o diretorio de outputs.
        charts_subdir: Subdiretorio dentro de outputs para charts.

    Returns:
        Instancia de ChartingSettings configurada.

    Example:
        # No inicio do seu projeto:
        from agora_charting import configure
        from pathlib import Path

        # Opcao 1: Path direto
        configure(outputs_path=Path('./meus_outputs'))

        # Opcao 2: Usar variavel de ambiente (nao requer chamada)
        # $env:AGORA_CHARTING_OUTPUTS_PATH = "C:/caminho/outputs"

        # Opcao 3: Auto-discovery (nao requer chamada)
        # Funciona automaticamente se existir pyproject.toml, .git, etc
    """
    return _settings.configure(
        outputs_path=outputs_path,
        charts_subdir=charts_subdir,
    )


def get_settings() -> ChartingSettings:
    """Retorna a instancia global de configuracoes."""
    return _settings


def __getattr__(name: str):
    """
    Permite acesso a CHARTS_PATH e OUTPUTS_PATH como atributos do modulo.

    Isso permite a sintaxe:
        from agora_charting.config import CHARTS_PATH

    E o valor sera calculado dinamicamente usando lazy evaluation.
    """
    if name == "CHARTS_PATH":
        return _settings.charts_path
    if name == "OUTPUTS_PATH":
        return _settings.outputs_path
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
