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
    from chartkit import configure
    configure(branding={'company_name': 'Minha Empresa'})

    # Opcao 4: Path explicito para arquivo TOML
    from chartkit import configure
    from pathlib import Path
    configure(config_path=Path('./minha-config.toml'))

    # Opcao 5: Variavel de ambiente para outputs
    # $env:CHARTING_OUTPUTS_PATH = "C:/caminho/outputs"

Uso:
    import chartkit  # Registra o accessor 'charting'

    # Plotagem
    df.chartkit.plot()
    df.chartkit.plot(kind='bar', title='Titulo', units='%')

    # Transformacoes
    from chartkit import yoy, mom, accum_12m, annualize_daily
    df_yoy = yoy(df)
    cdi_anual = annualize_daily(cdi_diario)
"""

from .accessor import ChartingAccessor
from .engine import ChartingPlotter
from .settings import (
    ChartingConfig,
    configure,
    get_assets_path,
    get_charts_path,
    get_config,
    get_outputs_path,
    reset_config,
)
from .styling.theme import theme
from .transforms import (
    accum_12m,
    annualize_daily,
    compound_rolling,
    diff,
    mom,
    normalize,
    real_rate,
    to_month_end,
    yoy,
)  # Re-exported from transforms/


# Propriedades dinamicas para CHARTS_PATH, OUTPUTS_PATH e ASSETS_PATH
def __getattr__(name: str):
    """
    Permite acesso a CHARTS_PATH, OUTPUTS_PATH e ASSETS_PATH como atributos do modulo.

    Isso permite a sintaxe:
        from chartkit import CHARTS_PATH, OUTPUTS_PATH, ASSETS_PATH

    E o valor sera calculado dinamicamente usando lazy evaluation.
    """
    if name == "CHARTS_PATH":
        return get_charts_path()
    if name == "OUTPUTS_PATH":
        return get_outputs_path()
    if name == "ASSETS_PATH":
        return get_assets_path()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Configuracao
    "configure",
    "get_config",
    "reset_config",
    "ChartingConfig",
    # Paths
    "CHARTS_PATH",
    "OUTPUTS_PATH",
    "ASSETS_PATH",
    # Classes principais
    "ChartingAccessor",
    "ChartingPlotter",
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
