"""
Biblioteca de Charting padronizado.

Fornece capacidades de plotagem padronizada via Pandas Accessor.

Configuracao (opcional - funciona automaticamente na maioria dos casos):

    # Opcao 1: Arquivo TOML no projeto
    # Crie .charting.toml ou charting.toml na raiz do projeto

    # Opcao 2: Secao no pyproject.toml
    # [tool.charting]
    # [tool.charting.branding]
    # company_name = "Minha Empresa"

    # Opcao 3: Configuracao programatica
    from agora_charting import configure
    configure(branding={'company_name': 'Minha Empresa'})

    # Opcao 4: Path explicito para arquivo TOML
    from agora_charting import configure
    from pathlib import Path
    configure(config_path=Path('./minha-config.toml'))

    # Opcao 5: Variavel de ambiente para outputs
    # $env:AGORA_CHARTING_OUTPUTS_PATH = "C:/caminho/outputs"

Uso:
    import agora_charting  # Registra o accessor 'agora'

    # Plotagem
    df.agora.plot()
    df.agora.plot(kind='bar', title='Titulo', units='%')

    # Transformacoes
    from agora_charting import yoy, mom, accum_12m, annualize_daily
    df_yoy = yoy(df)
    cdi_anual = annualize_daily(cdi_diario)
"""

from .accessor import AgoraAccessor
from .engine import AgoraPlotter
from .styling.theme import theme
from .transforms import (
    yoy,
    mom,
    accum_12m,
    diff,
    normalize,
    annualize_daily,
    compound_rolling,
    real_rate,
    to_month_end,
)
from .settings import (
    configure,
    get_config,
    reset_config,
    get_charts_path,
    get_outputs_path,
    ChartingConfig,
)


# Aliases para compatibilidade
def get_settings():
    """
    Retorna a configuracao atual.

    Deprecated: Use get_config() ao inves.
    """
    return get_config()


# Propriedades dinamicas para CHARTS_PATH e OUTPUTS_PATH
def __getattr__(name: str):
    """
    Permite acesso a CHARTS_PATH e OUTPUTS_PATH como atributos do modulo.

    Isso permite a sintaxe:
        from agora_charting import CHARTS_PATH, OUTPUTS_PATH

    E o valor sera calculado dinamicamente usando lazy evaluation.
    """
    if name == "CHARTS_PATH":
        return get_charts_path()
    if name == "OUTPUTS_PATH":
        return get_outputs_path()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Configuracao
    "configure",
    "get_config",
    "get_settings",  # Deprecated, use get_config()
    "reset_config",
    "ChartingConfig",
    "CHARTS_PATH",
    "OUTPUTS_PATH",
    # Classes principais
    "AgoraAccessor",
    "AgoraPlotter",
    "theme",
    # Transforms
    "yoy",
    "mom",
    "accum_12m",
    "diff",
    "normalize",
    "annualize_daily",
    "compound_rolling",
    "real_rate",
    "to_month_end",
]
