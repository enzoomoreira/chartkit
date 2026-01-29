"""
Utilitarios internos da biblioteca.

Este modulo contem funcoes auxiliares que nao fazem parte da API publica.
Nao importe diretamente deste modulo em codigo externo.
"""

from .collision import resolve_collisions

__all__ = [
    "resolve_collisions",
]
