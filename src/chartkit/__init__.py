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
    import chartkit  # Registra o accessor 'chartkit'

    # Plotagem simples
    df.chartkit.plot()
    df.chartkit.plot(kind='bar', title='Titulo', units='%')

    # Plotagem com metricas
    df.chartkit.plot(metrics=['ath', 'atl', 'ma:12'])

    # Transforms encadeados
    df.chartkit.annualize_daily().plot(metrics=['ath']).save('chart.png')

    # Transformacoes standalone
    from chartkit import yoy, mom, accum_12m, annualize_daily
    df_yoy = yoy(df)
    cdi_anual = annualize_daily(cdi_diario)
"""

from loguru import logger

# Desabilita logging por padrao (best practice para bibliotecas)
logger.disable("chartkit")


def configure_logging(level: str = "DEBUG", sink=None) -> None:
    """
    Ativa logging da biblioteca chartkit.

    Args:
        level: Nivel minimo (DEBUG, INFO, WARNING, ERROR).
        sink: Destino opcional (arquivo, stream). Se None, usa stderr.

    Example:
        >>> from chartkit import configure_logging
        >>> configure_logging(level="DEBUG")
    """
    logger.enable("chartkit")
    if sink:
        logger.add(sink, level=level)


from .accessor import ChartingAccessor
from .engine import ChartingPlotter
from .metrics import MetricRegistry
from .result import PlotResult
from .transforms import TransformAccessor
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
    "configure_logging",
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
    "PlotResult",
    "TransformAccessor",
    "MetricRegistry",
    "theme",
    # Transforms
    "yoy",
    "mom",
    "accum_12m",
    "diff",
    "normalize",
    "annualize_daily",
    "compound_rolling",
    "to_month_end",
]
