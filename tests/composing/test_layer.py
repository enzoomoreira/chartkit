from __future__ import annotations

import pandas as pd
import pytest

from chartkit.composing.layer import AxisSide, Layer, create_layer
from chartkit.exceptions import RegistryError, ValidationError


class TestCreateLayerValidation:
    """Eager validation in create_layer() catches invalid inputs at construction."""

    def test_invalid_kind_raises_registry_error(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(RegistryError, match="not supported"):
            create_layer(df, kind="invalid")  # type: ignore[arg-type]

    def test_invalid_axis_raises_validation_error(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValidationError, match="Invalid axis"):
            create_layer(df, axis="center")  # type: ignore[arg-type]

    def test_invalid_units_raises_validation_error(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValidationError, match="units"):
            create_layer(df, units="EUR")  # type: ignore[arg-type]

    def test_invalid_highlight_raises_validation_error(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValidationError, match="invalid"):
            create_layer(df, highlight="invalid")  # type: ignore[arg-type]


class TestLayer:
    def test_frozen_prevents_reassignment(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        layer = Layer(df=df)
        with pytest.raises(AttributeError):
            layer.kind = "bar"  # type: ignore[misc]

    def test_defaults(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        layer = Layer(df=df)
        assert layer.kind == "line"
        assert layer.x is None
        assert layer.y is None
        assert layer.units is None
        assert layer.highlight is False
        assert layer.metrics is None
        assert layer.fill_between is None
        assert layer.axis == "left"
        assert layer.kwargs == {}

    def test_all_fields(self) -> None:
        df = pd.DataFrame({"a": [1], "b": [2]})
        layer = Layer(
            df=df,
            kind="bar",
            x="a",
            y=["a", "b"],
            units="BRL",
            highlight="last",
            metrics=["ath"],
            fill_between=("a", "b"),
            axis="right",
            kwargs={"color": "red"},
        )
        assert layer.kind == "bar"
        assert layer.x == "a"
        assert layer.y == ["a", "b"]
        assert layer.units == "BRL"
        assert layer.highlight == "last"
        assert layer.metrics == ["ath"]
        assert layer.fill_between == ("a", "b")
        assert layer.axis == "right"
        assert layer.kwargs == {"color": "red"}


class TestCreateLayer:
    def test_returns_layer_instance(self) -> None:
        df = pd.DataFrame({"val": [1, 2, 3]})
        layer = create_layer(df)
        assert isinstance(layer, Layer)

    def test_defaults_match_layer_defaults(self) -> None:
        df = pd.DataFrame({"val": [1, 2, 3]})
        layer = create_layer(df)
        assert layer.kind == "line"
        assert layer.axis == "left"
        assert layer.kwargs == {}

    def test_kwargs_forwarded(self) -> None:
        df = pd.DataFrame({"val": [1]})
        layer = create_layer(df, color="red", linewidth=2)
        assert layer.kwargs == {"color": "red", "linewidth": 2}

    def test_explicit_params(self) -> None:
        df = pd.DataFrame({"a": [1], "b": [2]})
        layer = create_layer(
            df,
            kind="bar",
            x="a",
            y="b",
            units="%",
            highlight=True,
            metrics="ath",
            fill_between=("a", "b"),
            axis="right",
        )
        assert layer.kind == "bar"
        assert layer.x == "a"
        assert layer.y == "b"
        assert layer.units == "%"
        assert layer.highlight is True
        assert layer.metrics == "ath"
        assert layer.fill_between == ("a", "b")
        assert layer.axis == "right"

    def test_dataframe_reference_preserved(self) -> None:
        df = pd.DataFrame({"val": [1, 2, 3]})
        layer = create_layer(df)
        assert layer.df is df


class TestAxisSide:
    def test_left_is_valid(self) -> None:
        side: AxisSide = "left"
        assert side == "left"

    def test_right_is_valid(self) -> None:
        side: AxisSide = "right"
        assert side == "right"
