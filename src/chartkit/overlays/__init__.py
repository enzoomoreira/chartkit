"""Overlays visuais para graficos (medias moveis, linhas de referencia, bandas, marcadores)."""

from .bands import add_band
from .fill_between import add_fill_between
from .markers import HIGHLIGHT_STYLES, HighlightStyle, highlight_last
from .moving_average import add_moving_average
from .reference_lines import (
    add_ath_line,
    add_atl_line,
    add_avg_line,
    add_hline,
    add_target_line,
)
from .std_band import add_std_band
from .vband import add_vband

__all__ = [
    "add_moving_average",
    "add_ath_line",
    "add_atl_line",
    "add_avg_line",
    "add_hline",
    "add_target_line",
    "add_band",
    "add_std_band",
    "add_vband",
    "add_fill_between",
    "highlight_last",
    "HighlightStyle",
    "HIGHLIGHT_STYLES",
]
