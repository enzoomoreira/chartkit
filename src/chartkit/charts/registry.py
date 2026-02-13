from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Protocol

import pandas as pd
from matplotlib.axes import Axes

from ..exceptions import RegistryError

if TYPE_CHECKING:
    from ..overlays import HighlightMode

__all__ = ["ChartFunc", "ChartRegistry"]


class ChartFunc(Protocol):
    """Standard signature for chart type functions."""

    def __call__(
        self,
        ax: Axes,
        x: pd.Index | pd.Series,
        y_data: pd.Series | pd.DataFrame,
        highlight: list[HighlightMode],
        **kwargs: Any,
    ) -> None: ...


class ChartRegistry:
    """Central chart type registry with name-based dispatch."""

    _charts: dict[str, ChartFunc] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[ChartFunc], ChartFunc]:
        """Decorator to register a chart type.

        Args:
            name: Identifier used in ``kind='name'``.
        """

        def decorator(func: ChartFunc) -> ChartFunc:
            cls._charts[name] = func
            return func

        return decorator

    @classmethod
    def get(cls, name: str) -> ChartFunc:
        """Return the rendering function for a chart type.

        Raises:
            RegistryError: Unregistered chart type.
        """
        if name not in cls._charts:
            available = ", ".join(sorted(cls._charts.keys()))
            raise RegistryError(
                f"Chart type '{name}' not supported. Available: {available}"
            )
        return cls._charts[name]

    @classmethod
    def available(cls) -> list[str]:
        return sorted(cls._charts.keys())
