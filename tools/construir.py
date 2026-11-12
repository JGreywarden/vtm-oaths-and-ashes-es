"""aplica traduccion/ sobre los originales de respaldo/ y escribe los archivos del juego."""

import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from tools.cadenas import text_id
from tools.juego import game_running, load_file, object_name, script_classes, text_objects
from tools.lector import Field, read_fields, replace_texts
from tools.respaldo import (
    check_build,
    ensure_backup,
    known_build,
    known_hashes,
    restore_all,
    save_built,
    steam_build,
)
from tools.rutas import DATA, TRANSLATION
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


def build_file(source: Path, translations: Translations, classes: dict, out: Path) -> bool:
    """un archivo sin cambios se copia tal cual: así queda idéntico al original."""
    patched = patch_file(source, translations, classes)
    if patched is None:
        shutil.copyfile(source, out / source.name)
    else:
        (out / source.name).write_bytes(patched)
    return patched is not None


def build(folder: Path, out: Path = DATA) -> list[str]:
    """parte siempre de respaldo/; devuelve los archivos que llevan alguna traducción."""
    translations, classes = load_translations(folder), script_classes()
    sources = [ensure_backup(name, expected) for name, expected in known_hashes().items()]
    return [s.name for s in sources if build_file(s, translations, classes, out)]


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
