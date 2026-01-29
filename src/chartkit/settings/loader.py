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

import os
import sys
from copy import deepcopy
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, Optional, TypeVar

from .defaults import DEFAULT_CONFIG, create_default_config
from .schema import (
    BandsConfig,
    BarsConfig,
    BrandingConfig,
    ChartingConfig,
    CollisionConfig,
    ColorsConfig,
    CurrencyConfig,
    FontsConfig,
    FontSizesConfig,
    FooterConfig,
    FormattersConfig,
    FrequencyDetectionConfig,
    LabelsConfig,
    LayoutConfig,
    LegendConfig,
    LinesConfig,
    LocaleConfig,
    MagnitudeConfig,
    MarkersConfig,
    PathsConfig,
    TitleConfig,
    TransformsConfig,
)


# Compatibilidade com Python < 3.11
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore


T = TypeVar("T")


def deep_merge(base: dict, override: dict) -> dict:
    """
    Faz merge profundo de dois dicionarios.

    Valores em override sobrescrevem valores em base. Para dicionarios
    aninhados, o merge e feito recursivamente.

    Args:
        base: Dicionario base com valores default.
        override: Dicionario com valores para sobrescrever.

    Returns:
        Novo dicionario com merge dos dois.

    Example:
        >>> base = {'colors': {'primary': '#000'}, 'layout': {'dpi': 100}}
        >>> override = {'colors': {'primary': '#FFF'}}
        >>> deep_merge(base, override)
        {'colors': {'primary': '#FFF'}, 'layout': {'dpi': 100}}
    """
    result = deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result


def load_toml(path: Path) -> dict:
    """
    Carrega arquivo TOML e retorna como dicionario.

    Args:
        path: Caminho para o arquivo TOML.

    Returns:
        Dicionario com conteudo do arquivo, ou {} se nao existir
        ou tomllib nao estiver disponivel.
    """
    if tomllib is None:
        return {}

    if not path.exists():
        return {}

    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def load_pyproject_section(path: Path) -> dict:
    """
    Carrega secao [tool.charting] de um pyproject.toml.

    Args:
        path: Caminho para o pyproject.toml.

    Returns:
        Dicionario com conteudo de [tool.charting], ou {} se nao existir.
    """
    data = load_toml(path)
    return data.get("tool", {}).get("charting", {})


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Busca recursiva pelo project root usando markers comuns.

    Sobe a arvore de diretorios a partir de start_path (ou cwd) procurando
    por markers que indicam a raiz de um projeto Python.

    Args:
        start_path: Diretorio inicial da busca. Se None, usa cwd.

    Returns:
        Path do project root se encontrado, None caso contrario.
    """
    # Usa markers do DEFAULT_CONFIG
    markers = DEFAULT_CONFIG.paths.project_root_markers

    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Sobe a arvore de diretorios ate a raiz do filesystem
    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    return None


def find_outputs_dir(root: Path) -> Path:
    """
    Encontra diretorio de outputs seguindo convencoes comuns.

    Args:
        root: Path do project root.

    Returns:
        Path para o diretorio de outputs (existente ou default).
    """
    # Usa convencoes do DEFAULT_CONFIG
    conventions = DEFAULT_CONFIG.paths.output_conventions
    default_dir = DEFAULT_CONFIG.paths.default_output_dir

    for convention in conventions:
        candidate = root / convention
        if candidate.exists() and candidate.is_dir():
            return candidate

    return root / default_dir


def find_config_files() -> list[Path]:
    """
    Encontra arquivos de configuracao em ordem de precedencia.

    Procura em:
        1. Diretorio atual e project root (.charting.toml, charting.toml)
        2. pyproject.toml no project root
        3. Diretorio de configuracao do usuario

    Returns:
        Lista de paths de arquivos existentes, em ordem de precedencia
        (primeiro = maior prioridade).
    """
    config_files = []

    # 1. Projeto local
    project_root = find_project_root()
    search_dirs = [Path.cwd()]
    if project_root and project_root != Path.cwd():
        search_dirs.append(project_root)

    for dir_path in search_dirs:
        for name in [".charting.toml", "charting.toml"]:
            candidate = dir_path / name
            if candidate.exists():
                config_files.append(candidate)

    # 2. pyproject.toml (verificado separadamente pois precisa da secao [tool.charting])
    if project_root:
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            config_files.append(pyproject)

    # 3. Diretorio de configuracao do usuario
    if sys.platform == "win32":
        # Windows: %APPDATA%/charting/config.toml
        appdata = os.environ.get("APPDATA")
        if appdata:
            user_config = Path(appdata) / "charting" / "config.toml"
            if user_config.exists():
                config_files.append(user_config)
    else:
        # Linux/Mac: ~/.config/charting/config.toml
        home = Path.home()
        user_config = home / ".config" / "charting" / "config.toml"
        if user_config.exists():
            config_files.append(user_config)

    return config_files


def _dict_to_dataclass(cls: type[T], data: dict) -> T:
    """
    Converte dicionario para dataclass recursivamente.

    Args:
        cls: Classe dataclass de destino.
        data: Dicionario com dados.

    Returns:
        Instancia da dataclass preenchida com dados do dicionario.
    """
    if not is_dataclass(cls):
        return data  # type: ignore

    field_values = {}
    for f in fields(cls):
        if f.name in data:
            value = data[f.name]
            # Se o campo e uma dataclass, converte recursivamente
            if is_dataclass(f.type) and isinstance(value, dict):
                field_values[f.name] = _dict_to_dataclass(f.type, value)
            elif f.type == tuple[float, float] and isinstance(value, (list, tuple)):
                # Converte lista para tupla (para figsize)
                field_values[f.name] = tuple(value)
            else:
                field_values[f.name] = value

    return cls(**field_values)


def _dataclass_to_dict(obj: Any) -> dict:
    """
    Converte dataclass para dicionario recursivamente.

    Args:
        obj: Instancia de dataclass.

    Returns:
        Dicionario com dados da dataclass.
    """
    if not is_dataclass(obj):
        return obj

    result = {}
    for f in fields(obj):
        value = getattr(obj, f.name)
        if is_dataclass(value):
            result[f.name] = _dataclass_to_dict(value)
        elif isinstance(value, tuple):
            result[f.name] = list(value)
        else:
            result[f.name] = value

    return result


class ConfigLoader:
    """
    Carregador de configuracoes com cache.

    Gerencia o carregamento de configuracoes de multiplas fontes,
    fazendo merge e mantendo cache para evitar recarregamentos.

    Attributes:
        _config: Configuracao atual cacheada.
        _config_path: Caminho explicito para arquivo de configuracao.
        _overrides: Overrides programaticos via configure().
    """

    def __init__(self) -> None:
        """Inicializa o loader sem configuracao carregada."""
        self._config: Optional[ChartingConfig] = None
        self._config_path: Optional[Path] = None
        self._overrides: dict = {}
        self._outputs_path: Optional[Path] = None

    def configure(
        self,
        config_path: Optional[Path] = None,
        outputs_path: Optional[Path] = None,
        **overrides: Any,
    ) -> "ConfigLoader":
        """
        Configura o carregador com opcoes explicitas.

        Args:
            config_path: Caminho explicito para arquivo TOML de configuracao.
            outputs_path: Caminho explicito para diretorio de outputs.
            **overrides: Overrides para secoes especificas da configuracao.
                        Aceita dicionarios aninhados que serao merged.
                        Ex: branding={'company_name': 'Minha Empresa'}

        Returns:
            Self para encadeamento.

        Example:
            >>> configure(branding={'company_name': 'Banco XYZ'})
            >>> configure(config_path=Path('./minha-config.toml'))
        """
        if config_path is not None:
            self._config_path = Path(config_path)

        if outputs_path is not None:
            self._outputs_path = Path(outputs_path)

        if overrides:
            self._overrides = deep_merge(self._overrides, overrides)

        # Invalida cache para forcar recarga
        self._config = None

        return self

    def reset(self) -> "ConfigLoader":
        """
        Reseta todas as configuracoes para o estado inicial.

        Returns:
            Self para encadeamento.
        """
        self._config = None
        self._config_path = None
        self._overrides = {}
        self._outputs_path = None
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

        # Comeca com defaults
        config_dict = _dataclass_to_dict(DEFAULT_CONFIG)

        # Carrega arquivos de configuracao (em ordem de precedencia reversa)
        config_files = find_config_files()

        # Arquivo explicito tem maior prioridade que auto-descobertos
        if self._config_path and self._config_path.exists():
            config_files.insert(0, self._config_path)

        # Merge em ordem reversa (menor prioridade primeiro)
        for config_file in reversed(config_files):
            if config_file.name == "pyproject.toml":
                file_config = load_pyproject_section(config_file)
            else:
                file_config = load_toml(config_file)

            if file_config:
                config_dict = deep_merge(config_dict, file_config)

        # Overrides programaticos tem maior prioridade
        if self._overrides:
            config_dict = deep_merge(config_dict, self._overrides)

        # Converte para dataclass
        self._config = _dict_to_dataclass(ChartingConfig, config_dict)

        return self._config

    @property
    def outputs_path(self) -> Path:
        """
        Retorna o path base para outputs.

        Ordem de precedencia:
            1. Configuracao explicita via configure(outputs_path=...)
            2. Variavel de ambiente CHARTING_OUTPUTS_PATH
            3. Auto-discovery baseado no project root
            4. Fallback: cwd/outputs
        """
        # 1. Configuracao explicita
        if self._outputs_path is not None:
            return self._outputs_path

        # 2. Variavel de ambiente
        env_path = os.environ.get("CHARTING_OUTPUTS_PATH")
        if env_path:
            return Path(env_path)

        # 3. Auto-discovery
        root = find_project_root()
        if root:
            return find_outputs_dir(root)

        # 4. Fallback
        config = self.get_config()
        return Path.cwd() / config.paths.default_output_dir

    @property
    def charts_path(self) -> Path:
        """Retorna o caminho completo para salvar graficos."""
        config = self.get_config()
        return self.outputs_path / config.paths.charts_subdir

    @property
    def project_root(self) -> Optional[Path]:
        """Retorna o project root detectado."""
        return find_project_root()


# Instancia singleton global
_loader = ConfigLoader()


def configure(
    config_path: Optional[Path] = None,
    outputs_path: Optional[Path] = None,
    **overrides: Any,
) -> ConfigLoader:
    """
    Configura o modulo chartkit.

    Esta funcao permite configuracao explicita, sobrescrevendo
    auto-discovery de arquivos TOML.

    Args:
        config_path: Caminho explicito para arquivo TOML de configuracao.
        outputs_path: Caminho explicito para diretorio de outputs.
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


def reset_config() -> ConfigLoader:
    """
    Reseta todas as configuracoes para o estado inicial.

    Util para testes ou quando precisar reconfigurar do zero.

    Returns:
        Instancia do ConfigLoader resetado.
    """
    return _loader.reset()
