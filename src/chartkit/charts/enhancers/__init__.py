"""Specialized chart enhancers. Imports trigger automatic registration."""

from . import (  # noqa: F401
    area,
    bar,
    ecdf,
    eventplot,
    hist,
    pie,
    stackplot,
    stacked_bar,
    stairs,
    statistical,
    stem,
)

__all__: list[str] = []
