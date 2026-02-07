"""Configuracao de logging da biblioteca.

O logger e desabilitado por default (best practice para bibliotecas).
Use ``configure_logging()`` para ativar.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

logger.disable("chartkit")

__all__ = ["configure_logging"]


def configure_logging(level: str = "DEBUG", sink: Any = None) -> None:
    """Ativa logging da biblioteca chartkit.

    Args:
        level: Nivel minimo de log (default: ``DEBUG``).
        sink: Destino opcional (arquivo, stream). Se None, usa stderr.
    """
    logger.enable("chartkit")
    if sink:
        logger.add(sink, level=level)
