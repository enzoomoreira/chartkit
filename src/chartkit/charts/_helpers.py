"""Internal helpers shared between chart types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Literal, cast

import numpy as np
import pandas as pd

from ..exceptions import ValidationError
from ..settings import get_config
from ..settings.schema import BarsConfig, ChartingConfig
from ..styling.theme import theme

if TYPE_CHECKING:
    from matplotlib.axes import Axes

__all__ = [
    "RenderContext",
    "apply_y_origin",
    "compute_bar_offsets",
    "detect_bar_width",
    "is_categorical_index",
    "prepare_categorical_axis",
    "prepare_render_context",
    "resolve_color",
    "validate_y_origin",
]


@dataclass(frozen=True)
class RenderContext:
    """Pre-computed rendering context shared across enhancers."""

    config: ChartingConfig
    colors: list[str]
    user_color: str | None
    zorder: float
    y_data: pd.DataFrame


def prepare_render_context(
    y_data: pd.Series | pd.DataFrame,
    kwargs: dict[str, Any],
) -> RenderContext:
    """Extract common enhancer boilerplate into a context object.

    Pops ``color`` and ``zorder`` from *kwargs* (mutates in place).
    Coerces ``y_data`` from Series to single-column DataFrame.
    """
    config = get_config()
    if isinstance(y_data, pd.Series):
        y_data = y_data.to_frame()
    user_color = kwargs.pop("color", None)
    user_zorder = kwargs.pop("zorder", None)
    colors = theme.colors.cycle()
    zorder = user_zorder if user_zorder is not None else config.layout.zorder.data
    return RenderContext(
        config=config,
        colors=colors,
        user_color=user_color,
        zorder=zorder,
        y_data=y_data,
    )


def resolve_color(ctx: RenderContext, index: int) -> str:
    """Resolve color for column at *index* using user override or theme cycle."""
    if ctx.user_color is not None:
        return ctx.user_color
    return ctx.colors[index % len(ctx.colors)]


def is_categorical_index(x: pd.Index | pd.Series) -> bool:
    """Return True for string/categorical indices (non-temporal, non-numeric)."""
    idx = pd.Index(x)
    if pd.api.types.is_datetime64_any_dtype(idx) or pd.api.types.is_numeric_dtype(idx):
        return False
    if isinstance(idx.dtype, pd.CategoricalDtype) or isinstance(
        idx.dtype, pd.StringDtype
    ):
        return True
    if idx.dtype == "object":
        non_null = [v for v in idx if v is not None and not pd.isna(v)]
        return all(isinstance(v, str) for v in non_null)
    return False


def prepare_categorical_axis(
    ax: Axes,
    x: pd.Index | pd.Series,
    *,
    axis: Literal["x", "y"] = "x",
) -> np.ndarray:
    """Convert categorical index to numeric positions and set tick labels.

    Args:
        axis: Which axis receives the category labels. ``'x'`` for vertical
            bar charts, ``'y'`` for horizontal bar charts (barh).

    Returns the numeric positions (np.arange). Caller should use these
    instead of the original x for plotting.
    """
    x_numeric = np.arange(len(x))
    if axis == "y":
        ax.set_yticks(x_numeric)
        ax.set_yticklabels(list(x))
    else:
        ax.set_xticks(x_numeric)
        ax.set_xticklabels(list(x))
    return x_numeric


def validate_y_origin(y_origin: str) -> Literal["zero", "auto"]:
    if y_origin not in ("zero", "auto"):
        raise ValidationError(f"y_origin must be 'zero' or 'auto', got: {y_origin!r}")
    return y_origin  # type: ignore[return-value]


def apply_y_origin(
    ax: Axes,
    y_origin: Literal["zero", "auto"],
    values: pd.Series,
    auto_margin: float,
    *,
    axis: Literal["y", "x"] = "y",
) -> None:
    """Apply y_origin logic to the axes.

    Args:
        values: Flat series of all relevant data values (e.g. stacked totals
            or raw bar values).
        auto_margin: Fractional margin for ``'auto'`` mode (from BarsConfig).
        axis: Which axis to adjust limits on. ``'y'`` for vertical bars,
            ``'x'`` for horizontal bars (barh).
    """
    set_lim = ax.set_ylim if axis == "y" else ax.set_xlim
    get_lim = ax.get_ylim if axis == "y" else ax.get_xlim

    if y_origin == "auto":
        clean = values.dropna()
        if not clean.empty:
            vmin, vmax = clean.min(), clean.max()
            margin = (vmax - vmin) * auto_margin
            set_lim(vmin - margin, vmax + margin)
    else:
        vmin, vmax = get_lim()
        if vmin > 0:
            set_lim(0, vmax)
        elif vmax < 0:
            set_lim(vmin, 0)


def compute_bar_offsets(
    n_cols: int,
    group_width: float,
) -> tuple[float, list[float]]:
    """Compute bar width and per-column offsets for grouped bar charts.

    Returns:
        Tuple of (bar_width, offsets) where offsets[i] is the center
        displacement for column i relative to the group center.
    """
    bar_width = group_width / n_cols
    offsets = [(i - n_cols / 2 + 0.5) * bar_width for i in range(n_cols)]
    return bar_width, offsets


def _coerce_datetime_index(x: pd.Index | pd.Series) -> pd.DatetimeIndex | None:
    """Best-effort conversion to DatetimeIndex for frequency detection."""
    idx = pd.Index(x)
    if pd.api.types.is_datetime64_any_dtype(idx):
        return pd.DatetimeIndex(idx)

    if is_categorical_index(idx):
        return None

    if idx.dtype == "object":
        has_datetime_like = any(
            isinstance(v, (pd.Timestamp, datetime, date, np.datetime64))
            for v in idx
            if v is not None and not pd.isna(v)
        )
        if not has_datetime_like:
            return None

    parsed = pd.to_datetime(idx, errors="coerce")
    valid = parsed[~parsed.isna()]
    if len(valid) < 2:
        return None
    return pd.DatetimeIndex(valid)


def detect_bar_width(x: pd.Index | pd.Series, bars: BarsConfig) -> float:
    """Automatic bar width based on data frequency."""
    width: float = bars.width_default
    dt_index = _coerce_datetime_index(x)
    if dt_index is not None and len(dt_index) > 1:
        span = cast(pd.Timestamp, dt_index.max()) - cast(pd.Timestamp, dt_index.min())
        avg_diff = span / (len(dt_index) - 1)
        if avg_diff.days > bars.frequency_detection.annual_threshold:
            width = float(bars.width_annual)
        elif avg_diff.days > bars.frequency_detection.monthly_threshold:
            width = float(bars.width_monthly)
    return width
