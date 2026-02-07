"""Hierarquia de excecoes do chartkit."""

__all__ = [
    "ChartKitError",
    "TransformError",
]


class ChartKitError(Exception):
    """Excecao base para todos os erros do chartkit."""


class TransformError(ChartKitError):
    """Erro durante validacao ou execucao de um transform."""
