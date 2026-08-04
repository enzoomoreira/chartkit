"""Library logging configuration.

chartkit follows the standard library convention: it logs to
``logging.getLogger("chartkit")`` and attaches a ``NullHandler``, so nothing
is emitted unless the host application configures logging. Use
``configure_logging()`` for a quick stderr handler during development and
``disable_logging()`` to remove it again.

Note that logging is for diagnostics. Conditions the caller should act on --
data being altered, a chart being degraded -- are raised through
``chartkit.warnings`` instead, so they surface without any opt-in.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TextIO

__all__ = ["configure_logging", "disable_logging"]

_ROOT_NAME = "chartkit"

# A NullHandler keeps "No handlers could be found" quiet without deciding
# anything on the application's behalf.
logging.getLogger(_ROOT_NAME).addHandler(logging.NullHandler())

_handlers: list[logging.Handler] = []


def configure_logging(
    level: int | str = logging.DEBUG, sink: TextIO | None = None
) -> logging.Handler:
    """Enable chartkit library logging on a stream.

    Removes previously added handlers first, so repeated calls do not
    duplicate output.

    Args:
        level: Minimum log level (default: ``DEBUG``).
        sink: Log destination (stream). If ``None``, uses ``sys.stderr``.

    Returns:
        The handler that was added, for later removal.
    """
    disable_logging()

    root = logging.getLogger(_ROOT_NAME)
    handler = logging.StreamHandler(sink if sink is not None else sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))

    root.addHandler(handler)
    root.setLevel(level)
    _handlers.append(handler)
    return handler


def disable_logging() -> None:
    """Remove handlers added by ``configure_logging()``."""
    root = logging.getLogger(_ROOT_NAME)
    for handler in _handlers:
        root.removeHandler(handler)
    _handlers.clear()
    root.setLevel(logging.NOTSET)
