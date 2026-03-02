import pandas as pd
from matplotlib.axes import Axes

from .._internal.collision import register_artist_obstacle, register_passive
from .._internal.extraction import resolve_series
from .._internal.frequency import freq_display_label
from ..exceptions import ValidationError
from ..settings import get_config
from ..styling.theme import theme

__all__ = ["add_std_band"]


def add_std_band(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    window: int = 0,
    deviations: float = 2.0,
    color: str | None = None,
    alpha: float | None = None,
    label: str | None = None,
    show_center: bool = True,
    series: str | None = None,
    detected_freq: str | None = None,
) -> None:
    """Add standard deviation band over the data.

    When ``window > 0``, computes rolling mean and std (Bollinger Bands).
    When ``window == 0``, computes mean and std of the entire series,
    producing flat horizontal bands.

    Args:
        window: Rolling window size. ``0`` uses the entire series.
        deviations: Number of standard deviations for the bands.
        show_center: Whether to plot the center line (mean/moving average).
        series: Column to use if y_data is DataFrame (default: first).
        detected_freq: Detected frequency code for label formatting.
    """
    if window < 0:
        raise ValidationError(f"window must be >= 0, got {window}")
    if window == 1:
        raise ValidationError(f"window must be 0 (full series) or >= 2, got {window}")
    if deviations <= 0:
        raise ValidationError(f"deviations must be positive, got {deviations}")

    config = get_config()
    y_data = resolve_series(y_data, series)

    if window == 0:
        ma = pd.Series(y_data.mean(), index=y_data.index)
        std = pd.Series(y_data.std(), index=y_data.index)
    else:
        min_periods = config.lines.moving_avg_min_periods
        rolling = y_data.rolling(window=window, min_periods=min_periods)
        ma = rolling.mean()
        std = rolling.std()

    upper = ma + deviations * std
    lower = ma - deviations * std

    band_color = color if color is not None else theme.colors.grid
    band_alpha = alpha if alpha is not None else config.bands.alpha
    freq = freq_display_label(detected_freq)

    if label is not None:
        band_label = label
    elif window == 0:
        band_label = config.labels.std_band_full_format.format(deviations=deviations)
    else:
        band_label = config.labels.std_band_format.format(
            window=window, deviations=deviations, freq=freq
        )

    patch = ax.fill_between(
        x,
        lower,
        upper,
        color=band_color,
        alpha=band_alpha,
        label=band_label,
        zorder=config.layout.zorder.bands,
    )
    register_passive(ax, patch)

    if show_center:
        lines = ax.plot(
            x,
            ma,
            color=band_color,
            linewidth=config.lines.overlay_width,
            linestyle=config.lines.reference_style,
            zorder=config.layout.zorder.moving_average,
        )
        register_artist_obstacle(ax, lines[0], filled=False)
