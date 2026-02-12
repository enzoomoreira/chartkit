from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

import numpy as np
import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from .._internal.collision import register_moveable
from ..exceptions import RegistryError
from ..settings import get_config
from ..styling.theme import theme

HighlightMode = Literal["last", "max", "min", "all"]

__all__ = [
    "HighlightMode",
    "HighlightStyle",
    "HIGHLIGHT_STYLES",
    "add_highlight",
]


@dataclass(frozen=True)
class HighlightStyle:
    """Positioning strategy for highlight by chart type."""

    ha: str
    va: str | None  # None = auto-detect by value sign
    label_prefix: str
    show_scatter: bool


HIGHLIGHT_STYLES: dict[str, HighlightStyle] = {
    "line": HighlightStyle(
        ha="left", va="center", label_prefix="  ", show_scatter=True
    ),
    "bar": HighlightStyle(ha="center", va=None, label_prefix="", show_scatter=False),
}


def _resolve_target(
    valid_series: pd.Series, mode: HighlightMode
) -> tuple[Any, float] | None:
    """Resolve the target (index, value) for a highlight mode.

    Returns ``None`` if the value is not finite.
    """
    if mode == "last":
        idx = valid_series.index[-1]
        val = valid_series.iloc[-1]
    elif mode == "max":
        idx = valid_series.idxmax()
        val = valid_series[idx]
    else:  # min
        idx = valid_series.idxmin()
        val = valid_series[idx]

    if not np.isfinite(val):
        logger.debug("Highlight mode '{}': target value is not finite, skipping", mode)
        return None
    return idx, float(val)


def _resolve_x_position(x: pd.Index | pd.Series, idx: Any) -> Any:
    """Map an index label to its X-axis coordinate.

    Handles duplicated indices by returning the first matching scalar.
    """
    if isinstance(x, pd.Series):
        result = x.loc[idx]
        return result.iloc[0] if isinstance(result, pd.Series) else result
    if hasattr(x, "get_loc"):
        loc = x.get_loc(idx)
        if isinstance(loc, int):
            return x[loc]
        # Duplicated index: get_loc returns slice or mask
        return idx
    return idx


def _apply_label_offset(ax: Axes, y_pos: float, va: str, fraction: float) -> float:
    """Add vertical breathing room between label and its data point."""
    if va not in ("bottom", "top") or fraction <= 0:
        return y_pos
    y0, y1 = ax.get_ylim()
    y_range = y1 - y0
    if y_range <= 0:
        return y_pos
    offset = y_range * fraction
    return y_pos + offset if va == "bottom" else y_pos - offset


def _render_point(
    ax: Axes,
    idx: Any,
    val: float,
    x: pd.Index | pd.Series | None,
    ha: str,
    va: str,
    label_prefix: str,
    show_scatter: bool,
    color: str,
) -> None:
    """Render scatter marker + text label for a highlight point."""
    config = get_config()

    # Resolve X position
    if x is not None:
        try:
            x_val = _resolve_x_position(x, idx)
        except (KeyError, IndexError):
            x_val = idx
    else:
        x_val = idx

    if isinstance(x_val, str):
        x_val = ax.convert_xunits(x_val)

    x_pos = cast(float, x_val)
    y_pos = cast(float, val)

    if show_scatter:
        ax.scatter(
            [x_pos],
            [y_pos],
            color=color,
            s=config.markers.scatter_size,
            zorder=config.layout.zorder.markers,
        )

    y_fmt = ax.yaxis.get_major_formatter()
    label_text = y_fmt(val, None)

    if not label_text:
        label_text = f"{val:.2f}"

    label_y = _apply_label_offset(ax, y_pos, va, config.markers.label_offset_fraction)

    text = ax.text(
        x_pos,
        label_y,
        f"{label_prefix}{label_text}",
        ha=ha,
        va=va,
        color=color,
        fontproperties=theme.font,
        fontweight=config.markers.font_weight,
        zorder=config.layout.zorder.markers,
    )

    register_moveable(ax, text)


def add_highlight(
    ax: Axes,
    series: pd.Series,
    style: str | HighlightStyle = "line",
    color: str | None = None,
    x: pd.Index | pd.Series | None = None,
    modes: list[HighlightMode] | None = None,
) -> None:
    """Highlight data points with formatted label.

    Supports multiple selection modes (last, max, min). Duplicate indices
    are rendered only once. Silently ignores empty series, all-NaN,
    or series with non-finite values.

    Args:
        style: Name of a style registered in ``HIGHLIGHT_STYLES`` or
            a ``HighlightStyle`` instance.
        x: Explicit X data. Required when X position needs
            resolution (e.g.: bar charts with DatetimeIndex).
        modes: Highlight modes to apply. ``None`` = ``["last"]``.
    """
    if series.empty:
        logger.warning("Highlight skipped: series is empty")
        return

    valid_series = series.dropna()
    if valid_series.empty:
        logger.warning("Highlight skipped: all values are NaN")
        return

    if modes is None:
        modes = ["last"]

    if color is None:
        color = theme.colors.primary

    if isinstance(style, str):
        if style not in HIGHLIGHT_STYLES:
            available = ", ".join(sorted(HIGHLIGHT_STYLES))
            raise RegistryError(
                f"Highlight style '{style}' not supported. Available: {available}"
            )
        style = HIGHLIGHT_STYLES[style]

    seen_indices: set[object] = set()

    for mode in modes:
        if mode == "all":
            for idx_val in valid_series.index:
                val = valid_series[idx_val]
                if not np.isfinite(val):
                    continue
                if idx_val in seen_indices:
                    continue
                seen_indices.add(idx_val)
                va = (
                    style.va
                    if style.va is not None
                    else ("bottom" if val >= 0 else "top")
                )
                _render_point(
                    ax,
                    idx_val,
                    float(val),
                    x,
                    style.ha,
                    va,
                    style.label_prefix,
                    style.show_scatter,
                    color,
                )
            continue

        target = _resolve_target(valid_series, mode)
        if target is None:
            continue

        idx, val = target
        if idx in seen_indices:
            continue
        seen_indices.add(idx)

        # Positioning: max/min use center above/below; last uses chart-type style
        if mode in ("max", "min"):
            ha = "center"
            va = "bottom" if mode == "max" else "top"
            prefix = ""
        else:
            ha = style.ha
            prefix = style.label_prefix
            va = style.va if style.va is not None else ("bottom" if val >= 0 else "top")

        _render_point(ax, idx, val, x, ha, va, prefix, style.show_scatter, color)
