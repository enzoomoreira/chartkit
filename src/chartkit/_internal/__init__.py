"""
Utilitarios internos da biblioteca.

Este modulo contem funcoes auxiliares que nao fazem parte da API publica.
Nao importe diretamente deste modulo em codigo externo.
"""

from .collision import (
    register_fixed,
    register_moveable,
    register_passive,
    resolve_collisions,
)

__all__ = [
    "register_fixed",
    "register_moveable",
    "register_passive",
    "resolve_collisions",
]
