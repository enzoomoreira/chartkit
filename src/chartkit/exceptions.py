"""Hierarquia de excecoes do chartkit."""

__all__ = [
    "ChartKitError",
    "TransformError",
    "ValidationError",
    "RegistryError",
    "StateError",
]


class ChartKitError(Exception):
    """Excecao base para todos os erros do chartkit."""


class TransformError(ChartKitError):
    """Erro durante validacao ou execucao de um transform."""


class ValidationError(ChartKitError, ValueError):
    """Erro de validacao de parametro ou input."""


class RegistryError(ChartKitError, LookupError):
    """Erro de lookup em registry (chart type, metrica, style)."""


class StateError(ChartKitError, RuntimeError):
    """Erro de operacao em estado invalido."""
