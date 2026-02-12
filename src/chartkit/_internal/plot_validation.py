"""Shared runtime validation for plot-related parameters."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, StrictBool
from pydantic import ValidationError as PydanticValidationError

from ..exceptions import ValidationError

UnitFormat = Literal["BRL", "USD", "BRL_compact", "USD_compact", "%", "human", "points"]


class PlotParamsModel(BaseModel):
    units: UnitFormat | None = None
    legend: StrictBool | None = None


def validate_plot_params(units: UnitFormat | None, legend: bool | None) -> None:
    """Validate generic plot params and normalize pydantic errors."""
    try:
        PlotParamsModel(units=units, legend=legend)
    except PydanticValidationError as exc:
        errors = exc.errors()
        msgs = [
            f"  {e['loc'][0]}: {e['msg']}" if e.get("loc") else f"  {e['msg']}"
            for e in errors
        ]
        raise ValidationError("Invalid plot parameters:\n" + "\n".join(msgs)) from exc


__all__ = ["UnitFormat", "validate_plot_params"]
