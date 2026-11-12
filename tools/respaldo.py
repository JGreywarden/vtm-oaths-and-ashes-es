"""copias de los archivos originales, verificadas por hash y ligadas a una versión del juego."""

import hashlib
import json
import re
import shutil
import sys
from collections.abc import Iterable
from pathlib import Path

from tools.juego import game_running, load_file, script_classes, text_objects
from tools.lector import read_fields
from tools.rutas import BACKUP, BUILT, DATA, HASHES, MANIFEST


def sha256(path: Path) -> str:
    with open(path, "rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def known_hashes() -> dict[str, str]:
    """hash del original de cada archivo del juego que contiene texto."""
    return json.loads(HASHES.read_text(encoding="utf-8"))["files"]


def known_build() -> str:
    """versión del juego a la que pertenecen los hashes y el respaldo."""
    return json.loads(HASHES.read_text(encoding="utf-8"))["build"]


def steam_build(manifest: Path = MANIFEST) -> str | None:
    """versión instalada según steam; none si la copia no es de steam."""
    if not manifest.exists():
        return None
    found = re.search(r'"buildid"\s+"(\d+)"', manifest.read_text(encoding="utf-8"))
    return found.group(1) if found else None


def check_build(installed: str | None, known: str) -> None:
    """tras un parche, el respaldo es de otra versión y no se puede mezclar con el juego."""
    if installed is not None and installed != known:
        raise ValueError(
            f"el juego se ha actualizado (versión {installed}, respaldo de la {known}): "
            "renueva el respaldo con python -m tools.respaldo"
        )


def check_original(path: Path, expected: str) -> None:
    if sha256(path) != expected:
        raise ValueError(f"{path} no es el original: verifica los archivos del juego en steam")


def ensure_backup(name: str, expected: str, data: Path = DATA, backup: Path = BACKUP) -> Path:
    """crea el respaldo si falta y comprueba siempre que es el original."""
    target = backup / name
    if not target.exists():
        check_original(data / name, expected)
        backup.mkdir(exist_ok=True)
        shutil.copyfile(data / name, target)
    check_original(target, expected)
    return target


def restore_all(names: Iterable[str], data: Path = DATA, backup: Path = BACKUP) -> list[str]:
    """devuelve al juego los originales que tengan respaldo."""
    restored = [name for name in names if (backup / name).exists()]
    for name in restored:
        shutil.copyfile(backup / name, data / name)
    return restored


def load_built(path: Path = BUILT) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_built(names: Iterable[str], data: Path = DATA, path: Path = BUILT) -> None:
    """apunta qué archivos del juego son ahora obra del mod, para no respaldarlos nunca."""
    hashes = {name: sha256(data / name) for name in names}
    path.write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")


def natural(path: Path) -> list:
    """orden con los números como números: level2 va antes que level10."""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name)]


def has_text(path: Path, classes: dict[int, str]) -> bool:
    objects = text_objects(load_file(path), classes)
    return any(f.text for _obj, schema, raw in objects for f in read_fields(schema, raw))


def text_files(data: Path, classes: dict[int, str]) -> list[Path]:
    """archivos del juego con algún texto visible."""
    paths = [*data.glob("*.assets"), *(p for p in data.glob("level*") if not p.suffix)]
    return [path for path in sorted(paths, key=natural) if has_text(path, classes)]


def still_patched(hashes: dict[str, str], built: dict[str, str]) -> list[str]:
    """archivos que siguen siendo los que escribió el mod: steam no los ha repuesto."""
    return [name for name, value in hashes.items() if built.get(name) == value]


def replace_backups(paths: list[Path], backup: Path) -> None:
    """los respaldos de una versión anterior del juego ya no sirven para la instalada."""
    backup.mkdir(exist_ok=True)
    for old in backup.iterdir():
        old.unlink()
    for path in paths:
        shutil.copyfile(path, backup / path.name)


def renew(build: str, built: dict[str, str], backup: Path = BACKUP, target: Path = HASHES) -> None:
    """respalda la versión instalada; se niega si queda algún archivo parcheado por el mod."""
    paths = text_files(DATA, script_classes())
    hashes = {path.name: sha256(path) for path in paths}
    patched = still_patched(hashes, built)
    if patched:
        raise ValueError(f"verifica la integridad en steam; siguen parcheados: {patched}")
    replace_backups(paths, backup)
    content = json.dumps({"build": build, "files": hashes}, indent=2)
    target.write_text(content + "\n", encoding="utf-8")


def main() -> None:
    build = steam_build()
    if build is None or build == known_build():
        sys.exit("no hay una versión nueva del juego que respaldar")
    if game_running():
        sys.exit("el juego está abierto: ciérralo antes de renovar el respaldo")
    renew(build, load_built())
    print(f"respaldo renovado con la versión {build}: {len(known_hashes())} archivos")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        sys.exit(str(error))
