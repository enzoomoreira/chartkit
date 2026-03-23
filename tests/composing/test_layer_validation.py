"""Layer creation and validation tests."""

from __future__ import annotations

import pandas as pd
import pytest

from chartkit.composing.layer import Layer, create_layer
from chartkit.exceptions import ValidationError


class TestCreateLayerValidation:
    """Eager validation in create_layer() catches invalid inputs at construction."""

    def test_invalid_kind_raises(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValidationError, match="not a valid matplotlib"):
            create_layer(df, kind="invalid")  # type: ignore[arg-type]

    def test_invalid_axis_raises(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValidationError, match="Invalid axis"):
            create_layer(df, axis="center")  # type: ignore[arg-type]

    def test_invalid_units_raises(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValidationError, match="units"):
            create_layer(df, units="EUR")  # type: ignore[arg-type]


class TestCreateLayerHappyPath:
    def test_returns_layer_with_defaults(self) -> None:
        df = pd.DataFrame({"val": [1, 2, 3]})
        layer = create_layer(df)
        assert isinstance(layer, Layer)
        assert layer.kind == "line"
        assert layer.axis == "left"
        assert layer.df is df

    def test_explicit_params_forwarded(self) -> None:
        df = pd.DataFrame({"a": [1], "b": [2]})
        layer = create_layer(
            df,
            kind="bar",
            x="a",
            y="b",
            units="%",
            highlight=True,
            metrics="ath",
            axis="right",
            color="red",
        )
        assert layer.kind == "bar"
        assert layer.x == "a"
        assert layer.y == "b"
        assert layer.units == "%"
        assert layer.highlight is True
        assert layer.metrics == "ath"
        assert layer.axis == "right"
        assert layer.kwargs == {"color": "red"}
