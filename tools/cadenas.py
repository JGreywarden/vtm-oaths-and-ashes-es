"""cadenas serializadas de unity: longitud int32, utf-8 y relleno hasta múltiplo de 4."""

import hashlib
import struct


def text_id(text: str) -> str:
    """identifica una cadena original sin tener que guardar su texto en el repo."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def pack_string(text: str) -> bytes:
    raw = text.encode("utf-8")
    return struct.pack("<i", len(raw)) + raw + b"\0" * (-len(raw) % 4)


def read_string(data: bytes, pos: int) -> tuple[str, int]:
    """devuelve el texto y la posición siguiente; falla si ahí no hay una cadena bien formada."""
    if pos + 4 > len(data):
        raise ValueError(f"no cabe una cadena en {pos}")
    (size,) = struct.unpack_from("<i", data, pos)
    end = pos + 4 + size + (-size % 4)
    if size < 0 or end > len(data) or any(data[pos + 4 + size : end]):
        raise ValueError(f"cadena mal formada en {pos}")
    try:
        return data[pos + 4 : pos + 4 + size].decode("utf-8"), end
    except UnicodeDecodeError as error:
        raise ValueError(f"cadena mal formada en {pos}") from error
