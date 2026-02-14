"""Generic chart renderer with enhancer-based extensibility."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Protocol, cast

import pandas as pd
from loguru import logger
from matplotlib.axes import Axes

from .._internal.collision import register_line_obstacle
from ..exceptions import ValidationError
from ..overlays import add_highlight
from ..settings import get_config
from ..styling.theme import theme

if TYPE_CHECKING:
    from ..overlays import HighlightMode

__all__ = ["ChartRenderer", "Enhancer"]


class Enhancer(Protocol):
    """Standard signature for specialized chart rendering functions."""

    def __call__(
        self,
        ax: Axes,
        x: pd.Index | pd.Series,
        y_data: pd.Series | pd.DataFrame,
        highlight: list[HighlightMode],
        **kwargs: Any,
    ) -> None: ...


class ChartRenderer:
    """Generic chart renderer that delegates to matplotlib or registered enhancers.

    Enhancers handle complex chart types (bar grouping, stacking) that need
    custom logic beyond a simple ``ax.{kind}()`` call. All other chart types
    are rendered generically by dispatching to the corresponding matplotlib
    Axes method.
    """

    _enhancers: dict[str, Enhancer] = {}

    _ALIASES: dict[str, str] = {"line": "plot"}

    _KIND_DEFAULTS: dict[str, Callable[..., dict[str, Any]]] = {
        "plot": lambda config: {"linewidth": config.lines.main_width},
    }

    @classmethod
    def register_enhancer(cls, name: str) -> Callable[[Enhancer], Enhancer]:
        """Decorator to register a specialized chart handler."""

        def decorator(func: Enhancer) -> Enhancer:
            cls._enhancers[name] = func
            return func

        return decorator

    @classmethod
    def render(
        cls,
        ax: Axes,
        kind: str,
        x: pd.Index | pd.Series,
        y_data: pd.Series | pd.DataFrame,
        highlight: list[HighlightMode],
        **kwargs: Any,
    ) -> None:
        """Render chart data onto axes.

        Dispatches to a registered enhancer if one exists for ``kind``,
        otherwise falls through to the generic matplotlib path.
        Post-render: new Line2D artists are registered as collision obstacles.
        """
        kind = cls._ALIASES.get(kind, kind)

        lines_before = set(id(line) for line in ax.lines)

        if kind in cls._enhancers:
            logger.debug("Dispatch: kind='{}' (enhancer)", kind)
            cls._enhancers[kind](ax, x, y_data, highlight=highlight, **kwargs)
        else:
            cls._validate_kind(kind)
            logger.debug("Dispatch: kind='{}' (generic)", kind)
            cls._generic_render(ax, kind, x, y_data, highlight, **kwargs)

        new_lines = [line for line in ax.lines if id(line) not in lines_before]
        for line in new_lines:
            register_line_obstacle(ax, line)

    @classmethod
    def _generic_render(
        cls,
        ax: Axes,
        kind: str,
        x: pd.Index | pd.Series,
        y_data: pd.Series | pd.DataFrame,
        highlight: list[HighlightMode],
        **kwargs: Any,
    ) -> None:
        """Render via ``ax.{kind}()`` with automatic color cycling and highlight."""
        config = get_config()

        if isinstance(y_data, pd.Series):
            y_data = y_data.to_frame()

        logger.debug(
            "generic_render: {} series, {} points", len(y_data.columns), len(y_data)
        )

        user_color = kwargs.pop("color", None)
        user_zorder = kwargs.pop("zorder", None)

        defaults = cls._KIND_DEFAULTS.get(kind, lambda _: {})(config)
        merged = {**defaults, **kwargs}

        colors = theme.colors.cycle()
        plot_method = getattr(ax, kind)

        patches_before = set(id(p) for p in ax.patches)

        for i, col in enumerate(y_data.columns):
            c = user_color if user_color is not None else colors[i % len(colors)]

            plot_method(
                x,
                y_data[col],
                color=c,
                label=str(col),
                zorder=user_zorder
                if user_zorder is not None
                else config.layout.zorder.data,
                **merged,
            )

            if highlight:
                style = cls._infer_highlight_style(ax, patches_before)
                add_highlight(
                    ax,
                    cast(pd.Series, y_data[col]),
                    style=style,
                    color=c,
                    modes=highlight,
                )

    @classmethod
    def _infer_highlight_style(
        cls,
        ax: Axes,
        patches_before: set[int],
    ) -> str:
        """Infer highlight style from newly created artists."""
        new_patches = [p for p in ax.patches if id(p) not in patches_before]
        return "bar" if new_patches else "line"

    @classmethod
    def _validate_kind(cls, kind: str) -> None:
        """Validate that ``ax.{kind}`` exists as a callable on Axes."""
        if kind.startswith("_"):
            raise ValidationError(
                f"Chart kind '{kind}' is not a valid matplotlib Axes method."
            )
        method = getattr(Axes, kind, None)
        if method is None or not callable(method):
            raise ValidationError(
                f"Chart kind '{kind}' is not a valid matplotlib Axes method."
            )

    @classmethod
    def validate_kind(cls, kind: str) -> None:
        """Public validation for use before rendering (e.g. Layer creation)."""
        resolved = cls._ALIASES.get(kind, kind)
        if resolved in cls._enhancers:
            return
        cls._validate_kind(resolved)

    @classmethod
    def available(cls) -> list[str]:
        """Return registered enhancer names (generic kinds are open-ended)."""
        return sorted(cls._enhancers.keys())
