"""configuración común: los tests marcados «game» se saltan si no está el juego."""

import struct

import pytest

from tools.cadenas import pack_string
from tools.literales import HEAD, MAGIC, VERSION
from tools.rutas import BACKUP, DATA


def pytest_collection_modifyitems(items):
    if DATA.exists() and BACKUP.exists():
        return
    skip = pytest.mark.skip(reason="no están los archivos del juego")
    for item in items:
        if "game" in item.keywords:
            item.add_marker(skip)


def make_head(name: str, script_id: int = 7) -> bytes:
    """cabecera de monobehaviour: objeto, activo, script en el archivo externo 1 y nombre."""
    script = (1).to_bytes(4, "little") + script_id.to_bytes(8, "little")
    return bytes(12) + (1).to_bytes(4, "little") + script + pack_string(name)


def count(number: int) -> bytes:
    return number.to_bytes(4, "little")


def make_scene(name: str = "DTA0-P1-1") -> bytes:
    """escena mínima: un nodo con una línea de alice y una opción con requisito."""
    audio = pack_string("") + bytes(8) + count(0)
    strings = b"".join(pack_string(s) for s in ["1", "ALICE", "Hello <i>there</i>."])
    images = b"".join(pack_string(s) for s in ["THOMAS", "ALICE", "OPERA", ""])
    line = strings + images + audio + count(0)
    choice = pack_string("Go.") + bytes(8) + pack_string("2") + bytes(4) + pack_string("")
    choice += bytes(8) + pack_string("") + bytes(40) + pack_string("Not hungry enough")
    choice += count(0) * 3 + bytes(36) + count(0) * 2 + bytes(16) + audio
    node = pack_string("1") + count(1) + line + count(1) + choice + bytes(16)
    return make_head(name) + count(1) + node + count(0) + count(0)


@pytest.fixture
def scene() -> bytes:
    return make_scene()


TABLE = 40  # la tabla no va pegada a la cabecera: en medio hay otros campos


def make_metadata(texts: list[str], version: int = VERSION) -> bytes:
    """metadato mínimo: cabecera, tabla de posiciones, bloque de literales y otra sección."""
    raws = [text.encode("utf-8") for text in texts]
    offsets = [sum(len(raw) for raw in raws[:n]) for n in range(len(raws) + 1)]
    table = struct.pack(f"<{len(offsets)}I", *offsets)
    block = b"".join(raws)
    counts = (len(table), len(offsets), TABLE + len(table), len(block), len(raws))
    head = HEAD.pack(MAGIC, version, TABLE, *counts)
    return head + bytes(TABLE - HEAD.size) + table + block + b"otra seccion"
