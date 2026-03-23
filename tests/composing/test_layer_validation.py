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


class TestCreateLayerClassification:
    """Validation via chart kind classification at layer construction."""

    def test_highlight_on_unsupported_kind_raises(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValidationError, match="does not support highlight"):
            create_layer(df, kind="stackplot", highlight=True)

    def test_highlight_on_supported_kind_passes(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        layer = create_layer(df, kind="bar", highlight=True)
        assert layer.highlight is True

    def test_metrics_on_unsupported_kind_raises(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValidationError, match="does not support metrics"):
            create_layer(df, kind="pie", metrics="ath")

    def test_metrics_on_supported_kind_passes(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        layer = create_layer(df, kind="line", metrics=["ath", "ma:12"])
        assert layer.metrics == ["ath", "ma:12"]

    def test_alias_kind_validates_correctly(self) -> None:
        """'line' -> 'plot' (series) should allow highlight + metrics."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        layer = create_layer(df, kind="line", highlight=True, metrics="ath")
        assert layer.kind == "line"

    def test_highlight_false_skips_validation(self) -> None:
        """highlight=False should not trigger validation even on unsupported kinds."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        layer = create_layer(df, kind="stackplot", highlight=False)
        assert layer.highlight is False

    def test_metrics_none_skips_validation(self) -> None:
        """metrics=None should not trigger validation even on unsupported kinds."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        layer = create_layer(df, kind="pie")
        assert layer.metrics is None


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
