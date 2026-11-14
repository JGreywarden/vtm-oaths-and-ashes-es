"""aplica traduccion/ sobre los originales de respaldo/ y escribe los archivos del juego."""

import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from tools.cadenas import text_id
from tools.juego import game_running, load_file, object_name, script_classes, text_objects
from tools.lector import Field, read_fields, replace_texts
from tools.literales import VISIBLE, patch_literals
from tools.respaldo import (
    check_build,
    ensure_backup,
    known_build,
    known_hashes,
    restore_all,
    save_built,
    steam_build,
)
from tools.rutas import DATA, METADATA, TRANSLATION
from tools.traducciones import load_translations, target_file

Translations = dict[str, dict[str, str]]


def translator(translations: Translations, name: str) -> Callable[[Field], str | None]:
    """busca cada texto en el archivo que le toca; sin traducción devuelve none."""

    def translate(field: Field) -> str | None:
        table = translations.get(target_file(field.group, name), {})
        return table.get(text_id(field.text)) if field.text else None

    return translate


def patch_object(schema: tuple, raw: bytes, translations: Translations) -> bytes:
    translate = translator(translations, object_name(raw))
    return replace_texts(raw, read_fields(schema, raw), translate)


def patch_file(source: Path, translations: Translations, classes: dict[int, str]) -> bytes | None:
    """el archivo parcheado, o none si ninguna traducción lo toca."""
    file, changed = load_file(source), False
    for obj, schema, raw in text_objects(file, classes):
        patched = patch_object(schema, raw, translations)
        if patched != raw:
            obj.set_raw_data(patched)
            changed = True
    return file.save() if changed else None


def patch_metadata(
    data: bytes, translations: Translations, visible: frozenset[str] = VISIBLE
) -> bytes | None:
    """el metadato con los literales traducidos, o none si ninguna traducción lo toca."""
    table = translations.get(target_file("codigo", ""), {})
    patched = patch_literals(data, table, visible)
    return None if patched is data else patched


def patch_source(source: Path, translations: Translations, classes: dict) -> bytes | None:
    """el metadato no es un archivo de unity: se parchea con su propio formato."""
    if source.name == Path(METADATA).name:
        return patch_metadata(source.read_bytes(), translations)
    return patch_file(source, translations, classes)


def build_file(
    name: str, source: Path, translations: Translations, classes: dict, out: Path
) -> bool:
    """un archivo sin cambios se copia tal cual: así queda idéntico al original."""
    patched = patch_source(source, translations, classes)
    (out / name).parent.mkdir(parents=True, exist_ok=True)
    if patched is None:
        shutil.copyfile(source, out / name)
    else:
        (out / name).write_bytes(patched)
    return patched is not None


def build(folder: Path, out: Path = DATA) -> list[str]:
    """parte siempre de respaldo/; devuelve los archivos que llevan alguna traducción."""
    translations, classes = load_translations(folder), script_classes()
    sources = {name: ensure_backup(name, expected) for name, expected in known_hashes().items()}
    return [n for n, s in sources.items() if build_file(n, s, translations, classes, out)]


def main(args: list[str]) -> None:
    if game_running():
        sys.exit("el juego está abierto: ciérralo antes de tocar sus archivos")
    check_build(steam_build(), known_build())
    if args == ["--restaurar"]:
        print("restaurados:", ", ".join(restore_all(known_hashes())))
        save_built([])
        return
    patched = build(Path(args[0]) if args else TRANSLATION)
    save_built(patched)
    print("archivos con traducciones:", ", ".join(patched) or "ninguno (juego original)")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except ValueError as error:
        sys.exit(str(error))
