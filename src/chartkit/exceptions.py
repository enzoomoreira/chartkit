"""Exception hierarchy for chartkit."""

__all__ = [
    "ChartKitError",
    "TransformError",
    "ValidationError",
    "RegistryError",
    "StateError",
]


class ChartKitError(Exception):
    """Base exception for all chartkit errors."""


class TransformError(ChartKitError):
    """Error during validation or execution of a transform."""


class ValidationError(ChartKitError, ValueError):
    """Parameter or input validation error."""


class RegistryError(ChartKitError, LookupError):
    """Registry lookup error (chart type, metric, style)."""


class StateError(ChartKitError, RuntimeError):
    """Operation attempted in an invalid state."""
