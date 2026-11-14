"""literales de texto del código: viven en global-metadata.dat, fuera de los archivos de unity."""

import struct
from itertools import accumulate, pairwise

from tools.cadenas import text_id

MAGIC, VERSION = 0xFAB11BAF, 39
# firma y versión; después, posición, tamaño y número de la tabla y del bloque de literales
HEAD = struct.Struct("<II6i")

# lista cerrada: ids de los literales que son texto en pantalla. un literal se comparte con
# todo el código, así que solo entra aquí tras comprobar que no hace de clave interna
# (nombre de archivo, valor guardado en la partida o nombre de una acción del mando).
VISIBLE = frozenset(
    {
        # perfiles de guardado: ranura, ranura vacía, tipo de guardado y avisos de partida nueva
        "17747d754d35",
        "3159fe421b32",
        "1574d21a573f",
        "e10fc58473cd",
        "cd0c1d67d65f",
        "8db07e99a45b",
        # nombre del capítulo en la ranura y en el registro de conversaciones
        "c53cc8aec774",
        "60e65a2fefe7",
        "1845fbbca21d",
        "0cba43522c26",
        "5973e8bae03a",
        # diario: aviso de entrada actualizada y registro de conversaciones
        "c1c063afb6d8",
        "f58811ba5ff5",
        "9f986d00c78d",
        "f528b5c9cdd2",
        # mapa de influencia: líder de la banda y distrito sin dueño
        "1b0434b6d239",
        "c837f2f25c5d",
        "94a79c9074e6",
        # laboratorio: resultado y motivos por los que no se puede destilar
        "e2eaa4a04eaf",
        "c4d01394c2f8",
        "f0b9c0ff4daf",
        "f3a3f81eb81b",
        "0ba1ae352c6a",
        "628630ca3cd6",
        "a7d02a0146bd",
        "bec2615a36ac",
        "a6caf4f67a06",
        "9880e79701ee",
        "02c266b0fa6c",
        "392c396665d3",
        # opciones: modo de pantalla, aviso de cambios aplicados y botón de confirmar
        "cb715b87a2a7",
        "d09b31120561",
        "beb19e2a881b",
        "04a212215ef9",
    }
)


def read_header(data: bytes) -> tuple[int, int, int, int, int, int]:
    """tabla y bloque de literales; falla si un parche ha cambiado el formato."""
    if len(data) < HEAD.size:
        raise ValueError("global-metadata.dat no tiene el formato conocido")
    magic, version, table, table_size, count, block, block_size, texts = HEAD.unpack_from(data)
    known = (magic, version) == (MAGIC, VERSION)
    if not known or table_size != count * 4 or count != texts + 1:
        raise ValueError("global-metadata.dat no tiene el formato conocido")
    return table, table_size, count, block, block_size, texts


def read_literals(data: bytes) -> list[bytes]:
    """cada literal va de su posición a la del siguiente; la última es el final del bloque."""
    table, _size, count, block, block_size, _texts = read_header(data)
    offsets = struct.unpack_from(f"<{count}I", data, table)
    if offsets[-1] != block_size or any(a > b for a, b in pairwise(offsets)):
        raise ValueError("global-metadata.dat no tiene el formato conocido")
    return [data[block + start : block + end] for start, end in pairwise(offsets)]


def visible_text(raw: bytes, visible: frozenset[str] = VISIBLE) -> str | None:
    """el texto de un literal de la lista cerrada; none si no pertenece a ella."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return text if text_id(text) in visible else None


def visible_texts(data: bytes, visible: frozenset[str] = VISIBLE) -> list[str]:
    texts = (visible_text(raw, visible) for raw in read_literals(data))
    return [text for text in texts if text is not None]


def translate_literal(raw: bytes, table: dict[str, str], visible: frozenset[str]) -> bytes:
    """solo cambia un literal de la lista cerrada con traducción; el resto queda como está."""
    text = visible_text(raw, visible)
    translated = None if text is None else table.get(text_id(text))
    return raw if translated is None else translated.encode("utf-8")


def rebuild(data: bytes, literals: list[bytes]) -> bytes:
    """añade un bloque nuevo al final y apunta a él la cabecera: ninguna sección se mueve.

    la tabla de posiciones conserva su sitio y su tamaño; el bloque antiguo queda sin uso.
    """
    table, size, count, _block, _block_size, texts = read_header(data)
    offsets = list(accumulate((len(raw) for raw in literals), initial=0))
    padded = data + bytes(-len(data) % 4)
    head = HEAD.pack(MAGIC, VERSION, table, size, count, len(padded), offsets[-1], texts)
    positions = struct.pack(f"<{count}I", *offsets)
    middle = padded[HEAD.size : table] + positions + padded[table + size :]
    return head + middle + b"".join(literals)


def patch_literals(data: bytes, table: dict[str, str], visible: frozenset[str] = VISIBLE) -> bytes:
    """el metadato con los literales traducidos; sin cambios devuelve los mismos bytes."""
    literals = read_literals(data)
    patched = [translate_literal(raw, table, visible) for raw in literals]
    return data if patched == literals else rebuild(data, patched)
