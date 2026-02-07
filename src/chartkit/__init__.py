"""Biblioteca de charting padronizado via Pandas accessor.

    import chartkit
    df.chartkit.plot(metrics=['ath', 'ma:12'], units='%')
    df.chartkit.yoy().plot(title='YoY').save('chart.png')
"""

from typing import Any

from loguru import logger

logger.disable("chartkit")


def configure_logging(level: str = "DEBUG", sink: Any = None) -> None:
    """Ativa logging da biblioteca chartkit.

    Args:
        sink: Destino opcional (arquivo, stream). Se None, usa stderr.
    """
    logger.enable("chartkit")
    if sink:
        logger.add(sink, level=level)


from ._internal import register_fixed, register_moveable, register_passive
from .accessor import ChartingAccessor
from .charts import ChartRegistry
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
)


def __getattr__(name: str):
    """Lazy evaluation de CHARTS_PATH, OUTPUTS_PATH e ASSETS_PATH."""
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
    # Collision API
    "register_fixed",
    "register_moveable",
    "register_passive",
    # Classes principais
    "ChartingAccessor",
    "ChartingPlotter",
    "ChartRegistry",
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
