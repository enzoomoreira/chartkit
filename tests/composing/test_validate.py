from __future__ import annotations

import pandas as pd
import pytest

from chartkit.composing.compose import _validate_layers
from chartkit.composing.layer import Layer
from chartkit.exceptions import ValidationError


def _layer(axis: str = "left") -> Layer:
    return Layer(df=pd.DataFrame({"v": [1, 2]}), axis=axis)  # type: ignore[arg-type]


class TestValidateLayers:
    def test_empty_raises(self) -> None:
        with pytest.raises(ValidationError, match="at least one layer"):
            _validate_layers((), None)

    def test_all_right_raises(self) -> None:
        with pytest.raises(ValidationError, match="axis='right'"):
            _validate_layers((_layer("right"),), None)

    def test_all_right_multiple_raises(self) -> None:
        with pytest.raises(ValidationError, match="axis='right'"):
            _validate_layers((_layer("right"), _layer("right")), None)

    def test_single_left_passes(self) -> None:
        _validate_layers((_layer("left"),), None)

    def test_mixed_passes(self) -> None:
        _validate_layers((_layer("left"), _layer("right")), None)
