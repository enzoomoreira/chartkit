"""Signature parity between the public facades and the functions they delegate to.

``plot()`` and ``layer()`` are each spelled out three times: once on the engine
and once per accessor.  Explicit signatures are what give editors autocomplete
and keep ``**kwargs`` free for matplotlib passthrough, but nothing forces the
copies to stay in sync -- ``decimals`` lived on ``ChartingPlotter.plot`` alone
for several releases.  These tests are that force.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, Literal, get_args, get_origin

import pandas as pd
import pytest

from chartkit.accessor import ChartingAccessor
from chartkit.composing import compose, create_layer
from chartkit.engine import ChartingPlotter
from chartkit.transforms.accessor import TransformAccessor

# Options that configure the chart as a whole rather than a single series.
# ``plot()`` and ``compose()`` are both chart-level entry points, so these must
# mean the same thing -- and default the same way -- in either one.
CHART_LEVEL_OPTIONS = frozenset(
    {
        "title",
        "source",
        "legend",
        "figsize",
        "xlabel",
        "ylabel",
        "xlim",
        "ylim",
        "grid",
        "tick_rotation",
        "tick_format",
        "tick_freq",
        "collision",
        "debug",
    }
)


def _params(
    func: Callable[..., Any], drop: frozenset[str]
) -> dict[str, tuple[Any, ...]]:
    """Map parameter name to the traits a caller can observe."""
    signature = inspect.signature(func)
    return {
        name: (param.kind, param.default, param.annotation)
        for name, param in signature.parameters.items()
        if name not in drop
    }


def _assert_same_signature(
    facade: Callable[..., Any],
    canonical: Callable[..., Any],
    drop: frozenset[str] = frozenset({"self"}),
) -> None:
    facade_params = _params(facade, drop)
    canonical_params = _params(canonical, drop)

    missing = sorted(set(canonical_params) - set(facade_params))
    extra = sorted(set(facade_params) - set(canonical_params))
    assert not missing, f"{facade.__qualname__} is missing: {missing}"
    assert not extra, f"{facade.__qualname__} has parameters that do not exist: {extra}"

    # Order matters: a caller may pass x and y positionally.
    assert list(facade_params) == list(canonical_params), (
        f"{facade.__qualname__} orders parameters differently from "
        f"{canonical.__qualname__}"
    )

    divergent = {
        name: (facade_params[name], canonical_params[name])
        for name in canonical_params
        if facade_params[name] != canonical_params[name]
    }
    assert not divergent, (
        f"{facade.__qualname__} diverges from {canonical.__qualname__}: {divergent}"
    )


class TestPlotParity:
    """Both accessor facades must expose the engine's full plot signature."""

    @pytest.mark.parametrize(
        "facade",
        [ChartingAccessor.plot, TransformAccessor.plot],
        ids=["ChartingAccessor", "TransformAccessor"],
    )
    def test_signature_matches_engine(self, facade: Callable[..., Any]) -> None:
        _assert_same_signature(facade, ChartingPlotter.plot)

    @pytest.mark.parametrize(
        "accessor_cls",
        [ChartingAccessor, TransformAccessor],
        ids=["ChartingAccessor", "TransformAccessor"],
    )
    def test_every_parameter_is_forwarded(
        self,
        accessor_cls: type[ChartingAccessor] | type[TransformAccessor],
        monkeypatch: pytest.MonkeyPatch,
        monthly_rates: pd.DataFrame,
    ) -> None:
        """A parameter in the signature that never reaches the engine is a lie."""
        received: dict[str, Any] = {}

        def capture(self: ChartingPlotter, **kwargs: Any) -> None:
            received.update(kwargs)

        monkeypatch.setattr(ChartingPlotter, "plot", capture)

        signature = inspect.signature(accessor_cls.plot)
        sentinels = {
            name: object()
            for name, param in signature.parameters.items()
            if name != "self" and param.kind is not param.VAR_KEYWORD
        }
        accessor_cls(monthly_rates).plot(**sentinels)

        unforwarded = sorted(
            name
            for name, sentinel in sentinels.items()
            if received.get(name) is not sentinel
        )
        assert not unforwarded, (
            f"{accessor_cls.__name__}.plot accepts but silently drops: {unforwarded}"
        )


class TestLayerParity:
    """Both accessor facades must expose the full create_layer signature."""

    @pytest.mark.parametrize(
        "facade",
        [ChartingAccessor.layer, TransformAccessor.layer],
        ids=["ChartingAccessor", "TransformAccessor"],
    )
    def test_signature_matches_create_layer(self, facade: Callable[..., Any]) -> None:
        _assert_same_signature(facade, create_layer, drop=frozenset({"self", "df"}))

    def test_layer_mirrors_plot_positional_order(self) -> None:
        """``layer('date', 'value')`` must mean what ``plot('date', 'value')`` means."""
        plot_positional = [
            name
            for name, param in inspect.signature(
                ChartingPlotter.plot
            ).parameters.items()
            if param.kind is param.POSITIONAL_OR_KEYWORD and name != "self"
        ]
        layer_positional = [
            name
            for name, param in inspect.signature(create_layer).parameters.items()
            if param.kind is param.POSITIONAL_OR_KEYWORD and name != "df"
        ]
        assert layer_positional == plot_positional


class TestChartLevelOptionParity:
    """Chart-level options must behave identically in plot() and compose()."""

    def test_compose_accepts_the_same_chart_level_options(self) -> None:
        plot_params = inspect.signature(ChartingPlotter.plot).parameters
        compose_params = inspect.signature(compose).parameters

        expected = CHART_LEVEL_OPTIONS & set(plot_params)
        missing = sorted(expected - set(compose_params))
        assert not missing, f"compose() is missing chart-level options: {missing}"

        divergent = {
            name: (compose_params[name].default, plot_params[name].default)
            for name in expected
            if compose_params[name].default != plot_params[name].default
        }
        assert not divergent, f"compose() defaults diverge from plot(): {divergent}"

    def test_plot_accepts_every_chart_level_option_compose_has(self) -> None:
        plot_params = inspect.signature(ChartingPlotter.plot).parameters
        compose_params = inspect.signature(compose).parameters

        missing = sorted(
            (CHART_LEVEL_OPTIONS & set(compose_params)) - set(plot_params),
        )
        assert not missing, f"plot() is missing chart-level options: {missing}"


class TestChartKindLiteral:
    """The autocomplete list must describe the kinds that actually exist."""

    def test_chart_kind_literal_is_current(self) -> None:
        from chartkit.charts import ChartRenderer
        from chartkit.engine import ChartKind

        literal_arm = next(
            arm for arm in get_args(ChartKind) if get_origin(arm) is Literal
        )
        assert sorted(get_args(literal_arm)) == ChartRenderer.available()


class TestLayerCoversPerSeriesOptions:
    """Every per-series option on plot() must be expressible as a Layer."""

    def test_layer_exposes_per_series_options(self) -> None:
        plot_params = set(inspect.signature(ChartingPlotter.plot).parameters)
        layer_params = set(inspect.signature(create_layer).parameters)

        per_series = plot_params - CHART_LEVEL_OPTIONS - {"self", "kwargs"}
        missing = sorted(per_series - layer_params)
        assert not missing, f"create_layer() cannot express: {missing}"
