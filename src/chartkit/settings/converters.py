"""
Conversores entre dataclass e dicionario.

Fornece funcoes para converter dataclasses tipadas em dicionarios
e vice-versa, com suporte a aninhamento recursivo.
"""

from dataclasses import fields, is_dataclass
from typing import Any, TypeVar, get_origin

__all__ = ["dict_to_dataclass", "dataclass_to_dict"]

T = TypeVar("T")


def _is_generic_tuple(field_type: Any) -> bool:
    """
    Verifica se field_type e qualquer tipo de tuple.

    Args:
        field_type: Tipo anotado do campo.

    Returns:
        True se for um tipo tuple generico, False caso contrario.
    """
    return get_origin(field_type) is tuple


def _is_generic_list(field_type: Any) -> bool:
    """
    Verifica se field_type e qualquer tipo de list.

    Args:
        field_type: Tipo anotado do campo.

    Returns:
        True se for um tipo list generico, False caso contrario.
    """
    return get_origin(field_type) is list


def dict_to_dataclass(cls: type[T], data: dict) -> T:
    """
    Converte dicionario para dataclass recursivamente.

    Suporta tipos genericos via typing.get_origin/get_args.

    Args:
        cls: Classe dataclass de destino.
        data: Dicionario com dados.

    Returns:
        Instancia da dataclass preenchida com dados do dicionario.

    Example:
        >>> @dataclass
        ... class Config:
        ...     name: str
        ...     value: int
        >>> dict_to_dataclass(Config, {'name': 'test', 'value': 42})
        Config(name='test', value=42)
    """
    if not is_dataclass(cls):
        return data  # type: ignore

    field_values = {}
    for f in fields(cls):
        if f.name not in data:
            continue

        value = data[f.name]

        # Recursivo para dataclasses aninhadas
        if is_dataclass(f.type) and isinstance(value, dict):
            field_values[f.name] = dict_to_dataclass(f.type, value)

        # Tuple (qualquer tipo) - converte list para tuple
        elif _is_generic_tuple(f.type) and isinstance(value, (list, tuple)):
            field_values[f.name] = tuple(value)

        # List (qualquer tipo) - garante que e list
        elif _is_generic_list(f.type) and isinstance(value, (list, tuple)):
            field_values[f.name] = list(value)

        # Tipos simples - passa direto
        else:
            field_values[f.name] = value

    return cls(**field_values)


def dataclass_to_dict(obj: Any) -> dict:
    """
    Converte dataclass para dicionario recursivamente.

    Args:
        obj: Instancia de dataclass.

    Returns:
        Dicionario com dados da dataclass.

    Example:
        >>> @dataclass
        ... class Config:
        ...     name: str
        ...     value: int
        >>> dataclass_to_dict(Config(name='test', value=42))
        {'name': 'test', 'value': 42}
    """
    if not is_dataclass(obj):
        return obj

    result = {}
    for f in fields(obj):
        value = getattr(obj, f.name)
        if is_dataclass(value):
            result[f.name] = dataclass_to_dict(value)
        elif isinstance(value, tuple):
            result[f.name] = list(value)
        else:
            result[f.name] = value

    return result
