"""Warning categories chartkit raises.

Logging is opt-in, so anything routed only through the logger is invisible to
the average caller. Conditions that change what the user gets -- data being
altered, a parameter being ignored, a chart being degraded -- are raised as
warnings instead, which surface by default and can be filtered, silenced or
escalated to errors with the standard ``warnings`` machinery:

    import warnings
    from chartkit.warnings import DataMutationWarning

    warnings.simplefilter("error", DataMutationWarning)

The rule for choosing between the two: warn when the outcome differs from
what the caller asked for -- a column silently dropped, a guessed window, an
ignored parameter. Report through the logger when the library is simply
doing the job it was asked to do. ``despike()`` replacing spikes is a log
record; ``variation()`` quietly discarding a text column is a warning.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

__all__ = [
    "ChartKitWarning",
    "DataMutationWarning",
    "InferenceWarning",
    "RenderingWarning",
    "warn",
]

_PACKAGE_ROOT = str(Path(__file__).parent)


class ChartKitWarning(UserWarning):
    """Base class for every warning chartkit raises."""


class DataMutationWarning(ChartKitWarning):
    """The data being plotted or transformed was altered.

    Raised when columns are dropped, values are replaced or non-finite
    entries are normalised -- cases where the output no longer matches the
    input the caller provided.
    """


class InferenceWarning(ChartKitWarning):
    """A value the caller did not supply had to be guessed.

    Raised when frequency detection fails and a fallback window is used, or
    when a statistic is computed from fewer observations than requested.
    """


class RenderingWarning(ChartKitWarning):
    """The chart was rendered, but not as requested.

    Raised when a parameter is ignored, a resource is missing, or the result
    is likely to be unreadable.
    """


def warn(message: str, category: type[ChartKitWarning]) -> None:
    """Emit *message*, attributed to the first frame outside chartkit.

    Warnings are raised from deep inside the render pipeline, so a fixed
    stacklevel would point at library internals. Walking out to the caller
    makes the warning name the line the user can actually change.
    """
    stacklevel = 2
    frame = sys._getframe(1)
    while frame is not None and frame.f_code.co_filename.startswith(_PACKAGE_ROOT):
        stacklevel += 1
        frame = frame.f_back

    warnings.warn(message, category, stacklevel=stacklevel)
