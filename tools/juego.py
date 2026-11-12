"""borde con unitypy y con el sistema: archivos del juego, clases de script y proceso."""

import struct
import subprocess
from collections.abc import Iterator
from pathlib import Path

import UnityPy

from tools.cadenas import read_string
from tools.esquemas import SCHEMAS
from tools.rutas import DATA, GAME_EXE

MANAGERS = "globalgamemanagers.assets"


def load_file(path: Path):
    return UnityPy.load(str(path)).file


def script_classes(data: Path = DATA) -> dict[int, str]:
    """nombre completo de cada script: los objetos solo guardan un puntero a él."""
    objects = load_file(data / MANAGERS).objects.values()
    scripts = ((o.path_id, o.read()) for o in objects if o.type.name == "MonoScript")
    return {i: ".".join(filter(None, [s.m_Namespace, s.m_ClassName])) for i, s in scripts}


def object_class(raw: bytes, externals: list[str], classes: dict[int, str]) -> str | None:
    file_id, path_id = struct.unpack_from("<iq", raw, 16)
    if file_id == 0 or externals[file_id - 1] != MANAGERS:
        return None
    return classes.get(path_id)


def object_name(raw: bytes) -> str:
    return read_string(raw, 28)[0]


def text_objects(file, classes: dict[int, str]) -> Iterator[tuple]:
    """objetos que tienen esquema, con él y con sus datos."""
    externals = [external.path for external in file.externals]
    for obj in file.objects.values():
        if obj.type.name != "MonoBehaviour":
            continue
        raw = bytes(obj.get_raw_data())
        schema = SCHEMAS.get(object_class(raw, externals, classes))
        if schema:
            yield obj, schema, raw


def is_running(task_list: str) -> bool:
    return GAME_EXE.lower() in task_list.lower()


def game_running() -> bool:
    """en formato csv, tasklist no recorta el nombre del ejecutable."""
    result = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True)
    return is_running(result.stdout)
