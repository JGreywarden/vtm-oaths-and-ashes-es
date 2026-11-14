"""vuelca el texto visible de los originales a originales/ (solo local, nunca al repo)."""

import sys
from collections.abc import Iterable, Iterator
from pathlib import Path

from tools.cadenas import has_visible_text, text_id
from tools.juego import (
    hierarchy,
    load_file,
    object_name,
    object_path,
    owner_id,
    script_classes,
    text_objects,
)
from tools.lector import Field, read_fields
from tools.literales import visible_texts
from tools.respaldo import check_build, ensure_backup, known_build, known_hashes, steam_build
from tools.rutas import METADATA, ORIGINALS
from tools.traducciones import SCENE_GROUPS, jsonl_files, target_file, write_jsonl


def object_rows(name: str, fields: list[Field]) -> Iterator[tuple[str, dict]]:
    """archivo de destino y fila de cada texto; el contexto ayuda a traducir bien."""
    speaker = ""
    for field in fields:
        if field.group == "hablantes":
            speaker = field.text
        if not has_visible_text(field.text):
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
    """un texto de interfaz no tiene nombre: su contexto es la ruta de su gameobject."""
    file, nodes = load_file(source), None
    for _obj, schema, raw in text_objects(file, classes):
        name = object_name(raw)
        if not name:
            nodes = hierarchy(file) if nodes is None else nodes
            name = object_path(nodes, owner_id(raw))
        yield from object_rows(name, read_fields(schema, raw))


def literal_rows(data: bytes) -> Iterator[tuple[str, dict]]:
    """los textos del código salen de la lista cerrada de literales, no de un esquema."""
    for text in visible_texts(data):
        row = {"id": text_id(text), "en": text, "objeto": Path(METADATA).name}
        yield target_file("codigo", ""), row


def source_rows(source: Path, classes: dict[int, str]) -> Iterator[tuple[str, dict]]:
    """el metadato no es un archivo de unity: se lee con su propio formato."""
    if source.name == Path(METADATA).name:
        return literal_rows(source.read_bytes())
    return file_rows(source, classes)


def merge_rows(pairs: Iterable[tuple[str, dict]]) -> dict[str, list[dict]]:
    """agrupa por archivo; una cadena repetida dentro de él aparece una sola vez."""
    files: dict[str, dict[str, dict]] = {}
    for target, row in pairs:
        files.setdefault(target, {}).setdefault(row["id"], row)
    return {target: list(rows.values()) for target, rows in files.items()}


def extract(sources: list[Path], classes: dict[int, str], out: Path) -> dict[str, list[dict]]:
    """reescribe la carpeta entera: una escena que un parche elimina no debe quedarse."""
    files = merge_rows(pair for source in sources for pair in source_rows(source, classes))
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
