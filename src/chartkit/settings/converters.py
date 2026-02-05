"""Conversores entre dataclass e dicionario."""

from dataclasses import fields, is_dataclass
from typing import Any, TypeVar, get_origin

__all__ = ["dict_to_dataclass", "dataclass_to_dict"]

T = TypeVar("T")


def _is_generic_tuple(field_type: Any) -> bool:
    return get_origin(field_type) is tuple


def _is_generic_list(field_type: Any) -> bool:
    return get_origin(field_type) is list


def dict_to_dataclass(cls: type[T], data: dict) -> T:
    """Converte dict para dataclass recursivamente (suporta aninhamento e generics)."""
    if not is_dataclass(cls):
        return data  # type: ignore

    field_values = {}
    for f in fields(cls):
        if f.name not in data:
            continue

        value = data[f.name]

        if is_dataclass(f.type) and isinstance(value, dict):
            field_values[f.name] = dict_to_dataclass(f.type, value)
        elif _is_generic_tuple(f.type) and isinstance(value, (list, tuple)):
            field_values[f.name] = tuple(value)
        elif _is_generic_list(f.type) and isinstance(value, (list, tuple)):
            field_values[f.name] = list(value)
        else:
            field_values[f.name] = value

    return cls(**field_values)


def dataclass_to_dict(obj: Any) -> dict:
    """Converte dataclass para dict recursivamente."""
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
