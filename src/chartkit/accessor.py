from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pandas as pd

from .engine import ChartingPlotter
from .transforms.accessor import TransformAccessor

if TYPE_CHECKING:
    from ._internal.plot_validation import AxisLimits
    from .composing.layer import AxisSide, Layer
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
        """Percentage change between periods.

        Args:
            horizon: Comparison horizon (``'month'`` or ``'year'``).
            periods: Explicit number of periods. Mutually exclusive with ``freq``.
            freq: Data frequency (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``,
                ``'Y'``). Mutually exclusive with ``periods``.
        """
        return TransformAccessor(self._obj).variation(horizon, periods, freq)

    def accum(
        self, window: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Cumulative change via compound product in rolling window.

        Args:
            window: Window size in number of periods. Mutually exclusive
                with ``freq``. ``None`` auto-detects from data frequency.
            freq: Data frequency (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``,
                ``'Y'``). Mutually exclusive with ``window``.
        """
        return TransformAccessor(self._obj).accum(window, freq)

    def diff(self, periods: int = 1) -> TransformAccessor:
        """Absolute difference between periods.

        Args:
            periods: Number of periods for the diff. Negative for forward diff.
        """
        return TransformAccessor(self._obj).diff(periods)

    def normalize(
        self, base: int | None = None, base_date: str | None = None
    ) -> TransformAccessor:
        """Normalize series to a base value at a specific date.

        Args:
            base: Base value for normalization. ``None`` uses config
                ``transforms.normalize_base`` (default ``100``).
            base_date: Reference date (parseable by ``pd.Timestamp``).
                ``None`` uses the first non-NaN value.
        """
        return TransformAccessor(self._obj).normalize(base, base_date)

    def annualize(
        self, periods: int | None = None, freq: str | None = None
    ) -> TransformAccessor:
        """Annualize periodic rate via compound interest.

        Args:
            periods: Number of periods per year for compounding.
                Mutually exclusive with ``freq``.
            freq: Data frequency (``'D'``, ``'B'``, ``'W'``, ``'M'``, ``'Q'``,
                ``'Y'``). Mutually exclusive with ``periods``.
        """
        return TransformAccessor(self._obj).annualize(periods, freq)

    def drawdown(self) -> TransformAccessor:
        """Percentage distance from historical peak."""
        return TransformAccessor(self._obj).drawdown()

    def zscore(self, window: int | None = None) -> TransformAccessor:
        """Statistical standardization (z-score).

        Args:
            window: Rolling window size. ``None`` computes z-score over the
                entire series (global mean and std).
        """
        return TransformAccessor(self._obj).zscore(window)

    def despike(
        self,
        window: int = 21,
        threshold: float = 5.0,
        method: str = "median",
    ) -> TransformAccessor:
        """Detect and normalize aggressive data spikes (Hampel filter).

        Args:
            window: Rolling window size (odd, >= 3). Centered on each point.
            threshold: MADs above which a point is considered a spike.
                Default ``5.0`` (~5 sigma, very conservative).
            method: ``'median'`` replaces with rolling median;
                ``'interpolate'`` interpolates linearly.
        """
        return TransformAccessor(self._obj).despike(window, threshold, method)

    def resample(
        self,
        freq: str = "month",
        method: str = "last",
    ) -> TransformAccessor:
        """Resample to a target frequency.

        Args:
            freq: Target frequency (``'day'``, ``'week'``, ``'month'``,
                ``'quarter'``, ``'year'``) or short codes (``'D'``, ``'W'``,
                ``'M'``, ``'Q'``, ``'Y'``).
            method: Aggregation -- ``'last'``, ``'first'``, ``'mean'``,
                or ``'sum'``.
        """
        return TransformAccessor(self._obj).resample(freq, method)

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
        legend: bool | None = None,
        xlabel: str | None = None,
        ylabel: str | None = None,
        xlim: AxisLimits | None = None,
        ylim: AxisLimits | None = None,
        grid: bool | None = None,
        tick_rotation: int | Literal["auto"] | None = None,
        tick_format: str | None = None,
        tick_freq: str | None = None,
        collision: bool = True,
        debug: bool = False,
        **kwargs,
    ) -> PlotResult:
        """Create standardized chart.

        Args:
            x: Column for the X axis. ``None`` uses the DataFrame index.
            y: Column(s) for the Y axis. ``None`` uses all numeric columns.
            kind: Chart type (``'line'``, ``'bar'``, ``'barh'``, ``'area'``,
                ``'scatter'``, ``'hist'``, ``'pie'``, etc.).
            title: Title displayed above the chart.
            units: Y-axis formatting (``'BRL'``, ``'USD'``, ``'%'``,
                ``'human'``, ``'points'``, etc.).
            source: Data source for the footer. Overrides
                ``branding.default_source`` from config when provided.
            highlight: Data point highlight. ``True`` or ``'last'`` highlights
                the last point; ``'max'``/``'min'`` highlights extremes.
                Accepts a list to combine modes.
            metrics: Declarative metric(s) (``'ath'``, ``'ma:12'``,
                ``'band:1.5:4.5'``, etc.). Use ``|`` for custom label
                (e.g. ``'ath|Maximum'``).
            legend: ``None`` = auto (2+ labeled artists), ``True`` = force,
                ``False`` = suppress.
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
            legend=legend,
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
        kind: ChartKind = "line",
        x: str | None = None,
        y: str | list[str] | None = None,
        *,
        units: UnitFormat | None = None,
        highlight: HighlightInput = False,
        metrics: str | list[str] | None = None,
        axis: AxisSide = "left",
        **kwargs,
    ) -> Layer:
        """Create a Layer for use with ``compose()``.

        Args:
            kind: Chart type (``'line'``, ``'bar'``, ``'area'``, etc.).
            x: Column for the X axis. ``None`` uses the DataFrame index.
            y: Column(s) for the Y axis. ``None`` uses all numeric columns.
            units: Y-axis formatting (``'BRL'``, ``'USD'``, ``'%'``, etc.).
            highlight: Data point highlight mode(s).
            metrics: Declarative metric(s).
            axis: Which Y axis to use (``'left'`` or ``'right'``).
            **kwargs: Extra matplotlib parameters passed to the renderer.

        Note:
            Chart-level options (title, source, legend, xlabel, ylabel,
            xlim, ylim, grid, tick_*, collision, debug) are passed to
            ``compose()`` instead.
        """
        from .composing import create_layer

        return create_layer(
            self._obj,
            kind,
            x,
            y,
            units=units,
            highlight=highlight,
            metrics=metrics,
            axis=axis,
            **kwargs,
        )
