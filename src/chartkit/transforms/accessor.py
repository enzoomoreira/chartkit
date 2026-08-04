from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

import pandas as pd

from .temporal import (
    accum,
    annualize,
    despike,
    diff,
    drawdown,
    normalize,
    resample,
    variation,
    zscore,
)
from .types import (
    DespikeMethod,
    Freq,
    Horizon,
    ResampleFreq,
    ResampleMethod,
)

if TYPE_CHECKING:
    from .._internal.plot_validation import AxisLimits, TickFreq
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
        horizon: Horizon = "month",
        periods: int | None = None,
        freq: Freq | None = None,
    ) -> TransformAccessor:
        """Percentage change between periods.

        Args:
            horizon: Comparison horizon (``'month'`` or ``'year'``).
            periods: Explicit number of periods. Must be positive --
                unlike ``diff()``, where a negative value flips the
                direction. Mutually exclusive with ``freq``.
            freq: Data frequency (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``,
                ``'Y'``). Mutually exclusive with ``periods``.
        """
        return TransformAccessor(variation(self._df, horizon, periods, freq))

    def accum(
        self, window: int | None = None, freq: Freq | None = None
    ) -> TransformAccessor:
        """Cumulative change via compound product in rolling window.

        Args:
            window: Window size in number of periods. Mutually exclusive
                with ``freq``. ``None`` auto-detects from data frequency.
            freq: Data frequency (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``,
                ``'Y'``). Mutually exclusive with ``window``.
        """
        return TransformAccessor(accum(self._df, window, freq))

    def diff(self, periods: int = 1) -> TransformAccessor:
        """Absolute difference between periods.

        Args:
            periods: Number of periods for the diff. Negative for forward diff.
        """
        return TransformAccessor(diff(self._df, periods))

    def normalize(
        self, base: float | None = None, base_date: str | None = None
    ) -> TransformAccessor:
        """Normalize series to a base value at a specific date.

        Args:
            base: Base value for normalization, e.g. ``100`` or ``1.0``.
                ``None`` uses config ``transforms.normalize_base``
                (default ``100``).
            base_date: Reference date (parseable by ``pd.Timestamp``).
                ``None`` uses the first non-NaN value.
        """
        return TransformAccessor(normalize(self._df, base, base_date))

    def annualize(
        self, periods: int | None = None, freq: Freq | None = None
    ) -> TransformAccessor:
        """Annualize periodic rate via compound interest.

        Args:
            periods: Number of periods per year for compounding. Must be
                positive, unlike the ``periods`` of ``diff()``.
                Mutually exclusive with ``freq``.
            freq: Data frequency (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``,
                ``'Y'``). Mutually exclusive with ``periods``.
        """
        return TransformAccessor(annualize(self._df, periods, freq))

    def drawdown(self) -> TransformAccessor:
        """Percentage distance from historical peak."""
        return TransformAccessor(drawdown(self._df))

    def zscore(self, window: int | None = None) -> TransformAccessor:
        """Statistical standardization (z-score).

        Args:
            window: Rolling window size. ``None`` computes z-score over the
                entire series (global mean and std).
        """
        return TransformAccessor(zscore(self._df, window))

    def despike(
        self,
        window: int = 21,
        threshold: float = 5.0,
        method: DespikeMethod = "median",
    ) -> TransformAccessor:
        """Detect and normalize aggressive data spikes (Hampel filter).

        Args:
            window: Rolling window size (odd, >= 3). Centered on each point.
            threshold: MADs above which a point is considered a spike.
                Default ``5.0`` (~5 sigma, very conservative).
            method: ``'median'`` replaces with rolling median;
                ``'interpolate'`` interpolates linearly.
        """
        return TransformAccessor(despike(self._df, window, threshold, method))

    def resample(
        self,
        freq: ResampleFreq = "month",
        method: ResampleMethod = "last",
    ) -> TransformAccessor:
        """Resample to a target frequency.

        Args:
            freq: Target frequency (``'day'``, ``'week'``, ``'month'``,
                ``'quarter'``, ``'year'``) or short codes (``'D'``, ``'W'``,
                ``'M'``, ``'Q'``, ``'Y'``).
            method: Aggregation -- ``'last'``, ``'first'``, ``'mean'``,
                or ``'sum'``.
        """
        return TransformAccessor(resample(self._df, freq, method))

    def plot(
        self,
        x: str | None = None,
        y: str | list[str] | None = None,
        *,
        kind: ChartKind = "line",
        title: str | None = None,
        units: UnitFormat | None = None,
        decimals: int | None = None,
        source: str | None = None,
        highlight: HighlightInput = False,
        metrics: str | list[str] | None = None,
        legend: bool | None = None,
        figsize: tuple[float, float] | None = None,
        xlabel: str | None = None,
        ylabel: str | None = None,
        xlim: AxisLimits | None = None,
        ylim: AxisLimits | None = None,
        grid: bool | None = None,
        tick_rotation: int | Literal["auto"] | None = None,
        tick_format: str | None = None,
        tick_freq: TickFreq | None = None,
        collision: bool = True,
        debug: bool = False,
        **kwargs: Any,
    ) -> PlotResult:
        """Finalize the transform chain and plot the DataFrame.

        Args:
            x: Column for the X axis. ``None`` uses the DataFrame index.
            y: Column(s) for the Y axis. ``None`` uses all numeric columns.
            kind: Chart type (``'line'``, ``'bar'``, ``'barh'``, ``'area'``,
                ``'scatter'``, ``'hist'``, ``'pie'``, etc.).
            title: Title displayed above the chart.
            units: Y-axis formatting (``'BRL'``, ``'USD'``, ``'%'``,
                ``'human'``, ``'points'``, etc.).
            decimals: Decimal places for axis tick labels and highlight labels.
                Overrides the formatter default. Has no effect when *units*
                is ``None``.
            source: Data source for the footer.
            highlight: Data point highlight. ``True`` or ``'last'`` highlights
                the last point; ``'max'``/``'min'`` highlights extremes.
                Accepts a list to combine modes.
            metrics: Declarative metric(s) (``'ath'``, ``'ma:12'``,
                ``'band:1.5:4.5'``, etc.). Use ``|`` for custom label.
            legend: ``None`` = auto, ``True`` = force, ``False`` = suppress.
            figsize: Override figure size ``(width, height)`` in inches.
                ``None`` uses ``layout.figsize`` from config.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            xlim: X-axis limits as ``(min, max)``. Accepts strings
                (``"2024-01-01"``), datetime, or numeric.
            ylim: Y-axis limits as ``(min, max)``.
            grid: ``None`` uses config, ``True``/``False`` overrides.
            tick_rotation: X-axis tick rotation. ``"auto"`` detects overlap;
                ``int`` forces angle. ``None`` uses config.
            tick_format: Date format for X-axis ticks (e.g. ``"%b/%Y"``).
            tick_freq: Tick frequency (``"day"``, ``"week"``, ``"month"``,
                ``"quarter"``, ``"semester"``, ``"year"``).
            collision: Enable label collision resolution.
            debug: Show collision debug overlay.
            **kwargs: Extra matplotlib parameters passed to the renderer.
        """
        from ..engine import ChartingPlotter

        plotter = ChartingPlotter(self._df)
        return plotter.plot(
            x=x,
            y=y,
            kind=kind,
            title=title,
            units=units,
            decimals=decimals,
            source=source,
            highlight=highlight,
            metrics=metrics,
            legend=legend,
            figsize=figsize,
            xlabel=xlabel,
            ylabel=ylabel,
            xlim=xlim,
            ylim=ylim,
            grid=grid,
            tick_rotation=tick_rotation,
            tick_format=tick_format,
            tick_freq=tick_freq,
            collision=collision,
            debug=debug,
            **kwargs,
        )

    def layer(
        self,
        x: str | None = None,
        y: str | list[str] | None = None,
        *,
        kind: ChartKind = "line",
        units: UnitFormat | None = None,
        decimals: int | None = None,
        highlight: HighlightInput = False,
        metrics: str | list[str] | None = None,
        axis: AxisSide = "left",
        **kwargs: Any,
    ) -> Layer:
        """Create a Layer from the transformed DataFrame for use with ``compose()``.

        Args:
            x: Column for the X axis. ``None`` uses the DataFrame index.
            y: Column(s) for the Y axis. ``None`` uses all numeric columns.
            kind: Chart type (``'line'``, ``'bar'``, ``'area'``, etc.).
            units: Y-axis formatting (``'BRL'``, ``'USD'``, ``'%'``, etc.).
            decimals: Decimal places for this layer's axis tick labels. Has no
                effect when *units* is ``None``.
            highlight: Data point highlight mode(s).
            metrics: Declarative metric(s).
            axis: Which Y axis to use (``'left'`` or ``'right'``).
            **kwargs: Extra matplotlib parameters passed to the renderer.
        """
        from ..composing import create_layer

        return create_layer(
            self._df,
            x,
            y,
            kind=kind,
            units=units,
            decimals=decimals,
            highlight=highlight,
            metrics=metrics,
            axis=axis,
            **kwargs,
        )

    @property
    def df(self) -> pd.DataFrame:
        """Return the transformed DataFrame."""
        return self._df

    def __repr__(self) -> str:
        shape = self._df.shape
        return f"<TransformAccessor: {shape[0]} rows x {shape[1]} cols>"
