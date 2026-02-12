"""Configuracao de logging da biblioteca.

O logger e desabilitado por default (best practice para bibliotecas).
Use ``configure_logging()`` para ativar e ``disable_logging()`` para reverter.
"""

from __future__ import annotations

import sys
from typing import TextIO

from loguru import logger

logger.disable("chartkit")

__all__ = ["configure_logging", "disable_logging"]

_handler_ids: list[int] = []


def configure_logging(level: str = "DEBUG", sink: TextIO | None = None) -> int:
    """Ativa logging da biblioteca chartkit.

    Remove handlers anteriores antes de adicionar o novo para evitar
    duplicacao de logs em chamadas repetidas.

    Args:
        level: Nivel minimo de log (default: ``DEBUG``).
        sink: Destino dos logs (stream). Se ``None``, usa ``sys.stderr``.

    Returns:
        ID do handler adicionado (pode ser passado a ``logger.remove()``).
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
    """Desativa logging da biblioteca e remove handlers adicionados."""
    logger.disable("chartkit")
    for hid in _handler_ids:
        try:
            logger.remove(hid)
        except ValueError:
            pass
    _handler_ids.clear()
