"""
Conversores entre dataclass e dicionario.

Fornece funcoes para converter dataclasses tipadas em dicionarios
e vice-versa, com suporte a aninhamento recursivo.
"""

from dataclasses import fields, is_dataclass
from typing import Any, TypeVar

T = TypeVar("T")


def dict_to_dataclass(cls: type[T], data: dict) -> T:
    """
    Converte dicionario para dataclass recursivamente.

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
        if f.name in data:
            value = data[f.name]
            # Se o campo e uma dataclass, converte recursivamente
            if is_dataclass(f.type) and isinstance(value, dict):
                field_values[f.name] = dict_to_dataclass(f.type, value)
            elif f.type == tuple[float, float] and isinstance(value, (list, tuple)):
                # Converte lista para tupla (para figsize)
                field_values[f.name] = tuple(value)
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
