from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Protocol

import pandas as pd
from matplotlib.axes import Axes

from ..exceptions import RegistryError

if TYPE_CHECKING:
    from ..overlays.markers import HighlightMode

__all__ = ["ChartFunc", "ChartRegistry"]


class ChartFunc(Protocol):
    """Assinatura padrao para funcoes de chart type."""

    def __call__(
        self,
        ax: Axes,
        x: pd.Index | pd.Series,
        y_data: pd.Series | pd.DataFrame,
        highlight: list[HighlightMode],
        **kwargs: Any,
    ) -> None: ...


class ChartRegistry:
    """Registro central de chart types com dispatch por nome."""

    _charts: dict[str, ChartFunc] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[ChartFunc], ChartFunc]:
        """Decorator para registrar um chart type.

        Args:
            name: Identificador usado em ``kind='name'``.
        """

        def decorator(func: ChartFunc) -> ChartFunc:
            cls._charts[name] = func
            return func

        return decorator

    @classmethod
    def get(cls, name: str) -> ChartFunc:
        """Retorna a funcao de rendering para o chart type.

        Raises:
            RegistryError: Chart type nao registrado.
        """
        if name not in cls._charts:
            available = ", ".join(sorted(cls._charts.keys()))
            raise RegistryError(
                f"Chart type '{name}' nao suportado. Disponiveis: {available}"
            )
        return cls._charts[name]

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._charts.keys())
