"""vuelca el texto visible de los originales a originales/ (solo local, nunca al repo)."""

import sys
from collections.abc import Iterable, Iterator
from pathlib import Path

from tools.cadenas import text_id
from tools.juego import load_file, object_name, script_classes, text_objects
from tools.lector import Field, read_fields
from tools.respaldo import check_build, ensure_backup, known_build, known_hashes, steam_build
from tools.rutas import ORIGINALS
from tools.traducciones import SCENE_GROUPS, jsonl_files, target_file, write_jsonl


def object_rows(name: str, fields: list[Field]) -> Iterator[tuple[str, dict]]:
    """archivo de destino y fila de cada texto; el contexto ayuda a traducir bien."""
    speaker = ""
    for field in fields:
        if field.group == "hablantes":
            speaker = field.text
        if not field.text:
            continue
        row = {"id": text_id(field.text), "en": field.text}
        if field.group in SCENE_GROUPS:
            row["tipo"] = field.group
        elif name:
            row["objeto"] = name
        if field.group == "linea" and speaker:
            row["hablante"] = speaker
        yield target_file(field.group, name), row


def file_rows(source: Path, classes: dict[int, str]) -> Iterator[tuple[str, dict]]:
    for _obj, schema, raw in text_objects(load_file(source), classes):
        yield from object_rows(object_name(raw), read_fields(schema, raw))


def merge_rows(pairs: Iterable[tuple[str, dict]]) -> dict[str, list[dict]]:
    """agrupa por archivo; una cadena repetida dentro de él aparece una sola vez."""
    files: dict[str, dict[str, dict]] = {}
    for target, row in pairs:
        files.setdefault(target, {}).setdefault(row["id"], row)
    return {target: list(rows.values()) for target, rows in files.items()}


def extract(sources: list[Path], classes: dict[int, str], out: Path) -> dict[str, list[dict]]:
    """reescribe la carpeta entera: una escena que un parche elimina no debe quedarse."""
    files = merge_rows(pair for source in sources for pair in file_rows(source, classes))
    for stale in jsonl_files(out).values():
        stale.unlink()
    for target, rows in files.items():
        write_jsonl(out / target, rows)
    return files


def main() -> None:
    check_build(steam_build(), known_build())
    sources = [ensure_backup(name, expected) for name, expected in known_hashes().items()]
    files = extract(sources, script_classes(), ORIGINALS)
    total = sum(len(rows) for rows in files.values())
    print(f"{total} cadenas en {len(files)} archivos de {ORIGINALS.name}/")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        sys.exit(str(error))
