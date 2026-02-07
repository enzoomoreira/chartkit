"""Biblioteca de charting padronizado via Pandas accessor.

import chartkit
df.chartkit.plot(metrics=['ath', 'ma:12'], units='%')
df.chartkit.yoy().plot(title='YoY').save('chart.png')
"""

from ._internal import register_fixed, register_moveable, register_passive
from ._logging import configure_logging
from .accessor import ChartingAccessor
from .charts import ChartRegistry
from .engine import ChartingPlotter
from .exceptions import ChartKitError, TransformError
from .metrics import MetricRegistry
from .result import PlotResult
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
from .transforms import TransformAccessor
from .transforms import (
    accum,
    annualize_daily,
    compound_rolling,
    diff,
    drawdown,
    mom,
    normalize,
    to_month_end,
    yoy,
    zscore,
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
    "CHARTS_PATH",  # pyright: ignore[reportUnsupportedDunderAll]
    "OUTPUTS_PATH",  # pyright: ignore[reportUnsupportedDunderAll]
    "ASSETS_PATH",  # pyright: ignore[reportUnsupportedDunderAll]
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
    # Exceptions
    "ChartKitError",
    "TransformError",
    # Transforms
    "yoy",
    "mom",
    "accum",
    "diff",
    "normalize",
    "annualize_daily",
    "compound_rolling",
    "drawdown",
    "zscore",
    "to_month_end",
]
