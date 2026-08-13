"""Step function drawn with ``ax.stairs()``, with edges derived from the x data."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from matplotlib.axes import Axes

from ...overlays import add_highlight
from .._helpers import prepare_render_context, resolve_color
from ..renderer import ChartRenderer

if TYPE_CHECKING:
    from ...overlays import HighlightMode

__all__ = ["plot_stairs"]


@ChartRenderer.register_enhancer("stairs")
def plot_stairs(
    ax: Axes,
    x: pd.Index | pd.Series,
    y_data: pd.Series | pd.DataFrame,
    highlight: list[HighlightMode],
    **kwargs: Any,
) -> None:
    """Plot step-function chart using ``ax.stairs()``.

    ``ax.stairs(values, edges)`` expects values (heights) as the first
    positional arg. Without explicit edges matplotlib auto-generates
    ``range(len(values) + 1)``.
    """
    ctx = prepare_render_context(y_data, kwargs)
    edges = _edges_from_x(x, len(ctx.y_data))

    for i, col in enumerate(ctx.y_data.columns):
        c = resolve_color(ctx, i)
        args = (ctx.y_data[col],) if edges is None else (ctx.y_data[col], edges)
        ax.stairs(
            *args,
            color=c,
            label=str(col),
            zorder=ctx.zorder,
            **kwargs,
        )

    if highlight and ctx.y_data.shape[1] == 1:
        col = ctx.y_data.columns[0]
        c = resolve_color(ctx, 0)
        add_highlight(ax, ctx.y_data[col], style="line", color=c, x=x, modes=highlight)


def _edges_from_x(x: pd.Index | pd.Series, n_values: int) -> np.ndarray | None:
    """Build the ``n_values + 1`` bin edges ``ax.stairs`` needs from *x*.

    Without edges matplotlib generates ``range(n + 1)``, which silently
    replaces the caller's dates with positions 0..n.  Categorical x has no
    numeric position to derive, so it keeps the default.
    """
    idx = pd.Index(x)
    if len(idx) != n_values or n_values == 0:
        return None

    if pd.api.types.is_datetime64_any_dtype(idx):
        positions = mdates.date2num(idx.to_numpy())
    elif pd.api.types.is_numeric_dtype(idx):
        positions = idx.to_numpy(dtype=float)
    else:
        return None

    # Each stair spans [x_i, x_i+1); the last one needs a closing edge, taken
    # from the final spacing so it matches the width of its neighbour.
    last_step = positions[-1] - positions[-2] if n_values > 1 else 1.0
    return np.append(positions, positions[-1] + last_step)
