import pandas as pd
from matplotlib.axes import Axes

from .._internal.collision import register_passive
from ..exceptions import ValidationError
from ..settings import get_config
from ..styling.theme import theme

__all__ = ["add_std_band"]


def add_std_band(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    window: int,
    num_std: float = 2.0,
    color: str | None = None,
    alpha: float | None = None,
    label: str | None = None,
    show_center: bool = True,
    series: str | None = None,
) -> None:
    """Add standard deviation band (Bollinger Bands) over the data.

    Computes moving average and N standard deviations in a rolling window,
    plotting the area between upper and lower bands.

    Args:
        window: Rolling window size.
        num_std: Number of standard deviations for the bands.
        show_center: Whether to plot the center line (moving average).
        series: Column to use if y_data is DataFrame (default: first).
    """
    if window < 2:
        raise ValidationError(f"window must be >= 2, got {window}")
    if num_std <= 0:
        raise ValidationError(f"num_std must be positive, got {num_std}")

    config = get_config()

    if isinstance(y_data, pd.DataFrame):
        col = series if series is not None else y_data.columns[0]
        y_data = y_data[col]

    min_periods = config.lines.moving_avg_min_periods
    rolling = y_data.rolling(window=window, min_periods=min_periods)
    ma = rolling.mean()
    std = rolling.std()

    upper = ma + num_std * std
    lower = ma - num_std * std

    band_color = color if color is not None else theme.colors.grid
    band_alpha = alpha if alpha is not None else config.bands.alpha
    band_label = (
        label
        if label is not None
        else config.labels.std_band_format.format(window=window, num_std=num_std)
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
        register_passive(ax, lines[0])
