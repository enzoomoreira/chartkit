"""Overlays visuais para graficos (medias moveis, linhas de referencia, bandas, marcadores)."""

from .bands import add_band
from .markers import HIGHLIGHT_STYLES, HighlightStyle, highlight_last
from .moving_average import add_moving_average
from .reference_lines import add_ath_line, add_atl_line, add_hline

__all__ = [
    "add_moving_average",
    "add_ath_line",
    "add_atl_line",
    "add_hline",
    "add_band",
    "highlight_last",
    "HighlightStyle",
    "HIGHLIGHT_STYLES",
]
