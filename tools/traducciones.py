"""lectura y escritura de los .jsonl y reparto de cada texto en su archivo."""

import json
from pathlib import Path

SCENE_GROUPS = {"linea", "opcion"}


def target_file(group: str, object_name: str) -> str:
    """el texto de una escena va a su archivo; el resto se comparte por tipo de interfaz."""
    if group in SCENE_GROUPS:
        return f"escenas/{object_name}.jsonl"
    return f"interfaz/{group}.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(row, ensure_ascii=False) + "\n" for row in rows]
    path.write_text("".join(lines), encoding="utf-8", newline="\n")


def jsonl_files(folder: Path) -> dict[str, Path]:
    """archivos de un árbol de traducción o de originales, por su ruta relativa."""
    paths = sorted(folder.glob("*/*.jsonl"))
    return {path.relative_to(folder).as_posix(): path for path in paths}


def load_translations(folder: Path) -> dict[str, dict[str, str]]:
    """por archivo, la traducción de cada id."""
    files = jsonl_files(folder).items()
    return {name: {row["id"]: row["es"] for row in load_jsonl(path)} for name, path in files}
