from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from chartkit.engine import _PlotParams


class TestValidatePlotParams:
    def test_valid_units_accepted(self) -> None:
        p = _PlotParams(units="BRL")
        assert p.units == "BRL"

    def test_invalid_units_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            _PlotParams(units="EUR")

    def test_none_units_accepted(self) -> None:
        p = _PlotParams(units=None)
        assert p.units is None

    def test_legend_bool_accepted(self) -> None:
        p = _PlotParams(legend=True)
        assert p.legend is True

    def test_legend_string_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            _PlotParams(legend="yes")  # type: ignore[arg-type]
