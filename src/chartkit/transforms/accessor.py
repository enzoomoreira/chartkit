from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from .temporal import (
    accum,
    annualize,
    diff,
    drawdown,
    normalize,
    to_month_end,
    variation,
    zscore,
)

if TYPE_CHECKING:
    from ..composing.layer import AxisSide, Layer
    from ..engine import ChartKind, HighlightInput, UnitFormat
    from ..result import PlotResult


class TransformAccessor:
    """Chainable accessor for transforms on DataFrames and Series.

    Each method returns a new TransformAccessor, enabling chaining.
    Finalize with ``.plot()`` to generate the chart or ``.df`` to get the data.
    Series are converted to DataFrame internally.

    Example:
        >>> df.chartkit.variation(horizon='year').plot(title="YoY Variation")
        >>> transformed = df.chartkit.normalize().df
    """

    def __init__(self, df: pd.DataFrame | pd.Series) -> None:
        self._df = df.to_frame() if isinstance(df, pd.Series) else df

    def variation(
        self,
        horizon: str = "month",
        periods: int | None = None,
        freq: str | None = None,
    ) -> TransformAccessor:
        """Percentage change between periods."""
        return TransformAccessor(variation(self._df, horizon, periods, freq))

    def accum(
        self, window: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Cumulative change via compound product in rolling window."""
        return TransformAccessor(accum(self._df, window, freq))

    def diff(self, periods: int = 1) -> TransformAccessor:
        """Absolute difference between periods."""
        return TransformAccessor(diff(self._df, periods))

    def normalize(
        self, base: int | None = None, base_date: str | None = None
    ) -> TransformAccessor:
        """Normalize series to a base value at a specific date."""
        return TransformAccessor(normalize(self._df, base, base_date))

    def annualize(
        self, periods: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Annualize periodic rate via compound interest."""
        return TransformAccessor(annualize(self._df, periods, freq))

    def drawdown(self) -> TransformAccessor:
        """Percentage distance from historical peak."""
        return TransformAccessor(drawdown(self._df))

    def zscore(self, window: int | None = None) -> TransformAccessor:
        """Statistical standardization (z-score)."""
        return TransformAccessor(zscore(self._df, window))

    def to_month_end(self) -> TransformAccessor:
        """Align index to month-end keeping the last observation per month."""
        return TransformAccessor(to_month_end(self._df))

    def plot(self, **kwargs) -> PlotResult:
        """Finalize the transform chain and plot the DataFrame."""
        from ..engine import ChartingPlotter

        plotter = ChartingPlotter(self._df)
        return plotter.plot(**kwargs)

    def layer(
        self,
        kind: ChartKind = "line",
        x: str | None = None,
        y: str | list[str] | None = None,
        *,
        units: UnitFormat | None = None,
        highlight: HighlightInput = False,
        metrics: str | list[str] | None = None,
        fill_between: tuple[str, str] | None = None,
        axis: AxisSide = "left",
        **kwargs,
    ) -> Layer:
        """Create a Layer from the transformed DataFrame for use with ``compose()``."""
        from ..composing import create_layer

        return create_layer(
            self._df,
            kind,
            x,
            y,
            units=units,
            highlight=highlight,
            metrics=metrics,
            fill_between=fill_between,
            axis=axis,
            **kwargs,
        )

    @property
    def df(self) -> pd.DataFrame:
        return self._df

    def __repr__(self) -> str:
        shape = self._df.shape
        return f"<TransformAccessor: {shape[0]} rows x {shape[1]} cols>"
