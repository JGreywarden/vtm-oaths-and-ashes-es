"""lee un objeto siguiendo su esquema y localiza los campos de texto visible."""

import struct
from collections.abc import Callable
from typing import NamedTuple

from tools.cadenas import pack_string, read_string


class Field(NamedTuple):
    start: int
    end: int
    text: str
    group: str


def read_fields(schema: tuple, data: bytes) -> list[Field]:
    """falla si el esquema no consume el objeto exacto: así no se cuela un campo mal leído."""
    fields: list[Field] = []
    end = _read(schema, data, 0, fields)
    if end != len(data):
        raise ValueError(f"el esquema acaba en {end} y el objeto mide {len(data)}")
    return fields


def replace_texts(data: bytes, fields: list[Field], translate: Callable) -> bytes:
    """sustituye por posición; un campo sin traducción (none) se queda como está."""
    parts, last = [], 0
    for field in fields:
        new = translate(field)
        if new is not None:
            parts += [data[last : field.start], pack_string(new)]
            last = field.end
    return b"".join(parts) + data[last:]


def _read(schema, data: bytes, pos: int, fields: list[Field]) -> int:
    for item in schema:
        pos = _read_item(item, data, pos, fields)
    return pos


def _read_item(item, data: bytes, pos: int, fields: list[Field]) -> int:
    if isinstance(item, int):
        return _skip(data, pos, item)
    if isinstance(item, list):
        return _read_list(item, data, pos, fields)
    if item == "rest":
        return len(data)
    text, end = read_string(data, pos)
    if item != "str":
        fields.append(Field(pos, end, text, item.removeprefix("text:")))
    return end


def _skip(data: bytes, pos: int, size: int) -> int:
    if pos + size > len(data):
        raise ValueError(f"faltan bytes en {pos}")
    return pos + size


def _read_list(schema: list, data: bytes, pos: int, fields: list[Field]) -> int:
    (count,) = struct.unpack_from("<i", data, _skip(data, pos, 4) - 4)
    if not 0 <= count <= len(data):
        raise ValueError(f"número de elementos imposible en {pos}")
    pos += 4
    for _ in range(count):
        pos = _read(schema, data, pos, fields)
    return pos
