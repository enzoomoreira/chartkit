from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from .engine import ChartingPlotter
from .transforms.accessor import TransformAccessor

if TYPE_CHECKING:
    from .engine import ChartKind, HighlightInput, UnitFormat
    from .result import PlotResult


@pd.api.extensions.register_dataframe_accessor("chartkit")
@pd.api.extensions.register_series_accessor("chartkit")
class ChartingAccessor:
    """Pandas accessor for plotting and chained transforms.

    Registered automatically when importing chartkit.
    Accepts DataFrame and Series (Series is converted to DataFrame internally).
    Transforms return ``TransformAccessor``; ``.plot()`` returns ``PlotResult``.
    """

    def __init__(self, pandas_obj: pd.DataFrame | pd.Series) -> None:
        self._obj = (
            pandas_obj.to_frame() if isinstance(pandas_obj, pd.Series) else pandas_obj
        )

    def variation(
        self,
        horizon: str = "month",
        periods: int | None = None,
        freq: str | None = None,
    ) -> TransformAccessor:
        """Percentage change between periods."""
        return TransformAccessor(self._obj).variation(horizon, periods, freq)

    def accum(
        self, window: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Cumulative change via compound product in rolling window."""
        return TransformAccessor(self._obj).accum(window, freq)

    def diff(self, periods: int = 1) -> TransformAccessor:
        """Absolute difference between periods."""
        return TransformAccessor(self._obj).diff(periods)

    def normalize(
        self, base: int | None = None, base_date: str | None = None
    ) -> TransformAccessor:
        """Normalize series to a base value at a specific date."""
        return TransformAccessor(self._obj).normalize(base, base_date)

    def annualize(
        self, periods: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Annualize periodic rate via compound interest."""
        return TransformAccessor(self._obj).annualize(periods, freq)

    def drawdown(self) -> TransformAccessor:
        """Percentage distance from historical peak."""
        return TransformAccessor(self._obj).drawdown()

    def zscore(self, window: int | None = None) -> TransformAccessor:
        """Statistical standardization (z-score)."""
        return TransformAccessor(self._obj).zscore(window)

    def to_month_end(self) -> TransformAccessor:
        """Normalize temporal index to month end."""
        return TransformAccessor(self._obj).to_month_end()

    def plot(
        self,
        x: str | None = None,
        y: str | list[str] | None = None,
        *,
        kind: ChartKind = "line",
        title: str | None = None,
        units: UnitFormat | None = None,
        source: str | None = None,
        highlight: HighlightInput = False,
        metrics: str | list[str] | None = None,
        fill_between: tuple[str, str] | None = None,
        legend: bool | None = None,
        **kwargs,
    ) -> PlotResult:
        """Create standardized chart. See ``ChartingPlotter.plot()`` for full docs."""
        plotter = ChartingPlotter(self._obj)
        return plotter.plot(
            x=x,
            y=y,
            kind=kind,
            title=title,
            units=units,
            source=source,
            highlight=highlight,
            metrics=metrics,
            fill_between=fill_between,
            legend=legend,
            **kwargs,
        )
