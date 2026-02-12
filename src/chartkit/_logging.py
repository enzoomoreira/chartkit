"""Library logging configuration.

The logger is disabled by default (best practice for libraries).
Use ``configure_logging()`` to enable and ``disable_logging()`` to revert.
"""

from __future__ import annotations

import sys
from typing import TextIO

from loguru import logger

logger.disable("chartkit")

__all__ = ["configure_logging", "disable_logging"]

_handler_ids: list[int] = []


def configure_logging(level: str = "DEBUG", sink: TextIO | None = None) -> int:
    """Enable chartkit library logging.

    Removes previous handlers before adding the new one to avoid
    duplicate logs on repeated calls.

    Args:
        level: Minimum log level (default: ``DEBUG``).
        sink: Log destination (stream). If ``None``, uses ``sys.stderr``.

    Returns:
        ID of the added handler (can be passed to ``logger.remove()``).
    """
    for hid in _handler_ids:
        try:
            logger.remove(hid)
        except ValueError:
            pass
    _handler_ids.clear()

    logger.enable("chartkit")
    target = sink if sink is not None else sys.stderr
    handler_id = logger.add(target, level=level, filter="chartkit")
    _handler_ids.append(handler_id)
    return handler_id


def disable_logging() -> None:
    """Disable library logging and remove added handlers."""
    logger.disable("chartkit")
    for hid in _handler_ids:
        try:
            logger.remove(hid)
        except ValueError:
            pass
    _handler_ids.clear()
