"""Highlight input normalization."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, get_args

from ..exceptions import ValidationError
from ..overlays import HighlightMode

if TYPE_CHECKING:
    from ..engine import HighlightInput

__all__ = ["normalize_highlight"]

_VALID_MODES: set[str] = set(get_args(HighlightMode))


def normalize_highlight(highlight: HighlightInput) -> list[HighlightMode]:
    """Convert various highlight input forms to a list of HighlightMode."""
    if highlight is True:
        return ["last"]
    if highlight is False:
        return []
    if isinstance(highlight, str):
        if highlight not in _VALID_MODES:
            available = ", ".join(sorted(_VALID_MODES))
            raise ValidationError(
                f"Highlight mode '{highlight}' invalid. Available: {available}"
            )
        return [cast(HighlightMode, highlight)]
    modes: list[HighlightMode] = []
    for m in highlight:
        if m not in _VALID_MODES:
            available = ", ".join(sorted(_VALID_MODES))
            raise ValidationError(
                f"Highlight mode '{m}' invalid. Available: {available}"
            )
        modes.append(cast(HighlightMode, m))
    return modes
