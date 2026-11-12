"""tests sobre los archivos reales del juego; se saltan si el juego no está."""

import io
import json

import pytest
import UnityPy

from tools.cadenas import text_id
from tools.construir import build, build_file, patch_file
from tools.esquemas import SCHEMAS
from tools.extraer import extract, file_rows
from tools.juego import load_file, object_class, object_name, script_classes, text_objects
from tools.lector import read_fields
from tools.respaldo import (
    has_text,
    known_build,
    known_hashes,
    renew,
    sha256,
    steam_build,
    text_files,
)
from tools.rutas import BACKUP, DATA
from tools.traducciones import load_jsonl, write_jsonl

pytestmark = pytest.mark.game

SCENE = "DTA0-P1-4"


@pytest.fixture(scope="module")
def classes():
    return script_classes()


def raw_objects(file) -> dict[int, bytes]:
    return {path_id: bytes(obj.get_raw_data()) for path_id, obj in file.objects.items()}


def first_line(classes) -> str:
    rows = [row for _target, row in file_rows(BACKUP / "resources.assets", classes)]
    return next(row["en"] for row in rows if row.get("tipo") == "linea")


def test_script_classes_knows_the_scene_class(classes):
    assert "DialogueTreeSO" in classes.values()
    assert "TMPro.TextMeshProUGUI" in classes.values()


def test_backup_belongs_to_the_installed_version():
    assert steam_build() in (None, known_build())


def test_backups_are_the_known_originals():
    hashes = known_hashes()
    present = [name for name in hashes if (BACKUP / name).exists()]
    assert "resources.assets" in present
    assert all(sha256(BACKUP / name) == hashes[name] for name in present)


def test_every_text_object_fits_its_schema_exactly(classes):
    """si una actualización del juego cambia un formato, falla aquí y no en la partida."""
    found = set()
    for name in known_hashes():
        file = load_file(BACKUP / name)
        externals = [external.path for external in file.externals]
        for _obj, schema, raw in text_objects(file, classes):
            read_fields(schema, raw)
            found.add(object_class(raw, externals, classes))
    assert found == set(SCHEMAS)


def test_text_objects_finds_the_first_scene(classes):
    found = text_objects(load_file(BACKUP / "resources.assets"), classes)
    assert "DTA0-P1-1" in {object_name(raw) for _obj, _schema, raw in found}


def test_file_rows_gives_context_for_scene_lines(classes):
    rows = [row for target, row in file_rows(BACKUP / "resources.assets", classes)]
    assert any(row.get("hablante") == "THOMAS" for row in rows)
    assert {"linea", "opcion"} <= {row.get("tipo") for row in rows}


def test_patch_file_without_translations_changes_nothing(classes):
    assert patch_file(BACKUP / "sharedassets1.assets", {}, classes) is None


def test_rewriting_a_file_keeps_every_object_identical():
    """unitypy reescribe el archivo entero: ningún objeto puede salir distinto."""
    file = load_file(BACKUP / "sharedassets1.assets")
    rewritten = UnityPy.load(io.BytesIO(file.save())).file
    assert raw_objects(rewritten) == raw_objects(file)


def test_patch_file_changes_only_the_translated_text(classes):
    line = first_line(classes)
    translations = {"escenas/DTA0-P1-1.jsonl": {text_id(line): "Línea de prueba: ¿se ve «así»?"}}
    patched = patch_file(BACKUP / "resources.assets", translations, classes)
    before = raw_objects(load_file(BACKUP / "resources.assets"))
    after = raw_objects(UnityPy.load(io.BytesIO(patched)).file)
    changed = [path_id for path_id in before if before[path_id] != after[path_id]]
    assert len(changed) == 1 and object_name(after[changed[0]]) == "DTA0-P1-1"
    assert "Línea de prueba: ¿se ve «así»?".encode() in after[changed[0]]


def test_build_file_copies_an_untranslated_file_as_is(classes, tmp_path):
    assert build_file(BACKUP / "sharedassets1.assets", {}, classes, tmp_path) is False
    assert sha256(tmp_path / "sharedassets1.assets") == known_hashes()["sharedassets1.assets"]


def test_build_without_translations_leaves_the_original_game(tmp_path):
    out = tmp_path / "juego"
    out.mkdir()
    assert build(tmp_path / "sin_traducciones", out) == []
    hashes = known_hashes()
    assert all(sha256(out / name) == expected for name, expected in hashes.items())


def test_extract_writes_one_file_per_kind_and_removes_stale_files(classes, tmp_path):
    write_jsonl(tmp_path / "escenas" / "ELIMINADA.jsonl", [{"id": "a", "en": "x"}])
    files = extract([BACKUP / "sharedassets1.assets"], classes, tmp_path)
    assert "interfaz/misiones.jsonl" in files
    rows = load_jsonl(tmp_path / "interfaz" / "misiones.jsonl")
    assert rows == files["interfaz/misiones.jsonl"] and "en" in rows[0]
    assert not (tmp_path / "escenas" / "ELIMINADA.jsonl").exists()


def test_has_text_tells_files_with_visible_text(classes):
    assert has_text(DATA / "level1", classes)
    assert not has_text(DATA / "level0", classes)


def test_text_files_are_the_files_with_known_hashes(classes):
    assert {path.name for path in text_files(DATA, classes)} == set(known_hashes())


def test_renew_backs_up_the_installed_version(tmp_path):
    renew("123", {}, tmp_path / "respaldo", tmp_path / "hashes.json")
    written = json.loads((tmp_path / "hashes.json").read_text(encoding="utf-8"))
    assert written["build"] == "123" and set(written["files"]) == set(known_hashes())
    assert sha256(tmp_path / "respaldo" / "level1") == sha256(DATA / "level1")


def test_renew_refuses_to_back_up_a_file_written_by_the_mod(tmp_path):
    built = {"level1": sha256(DATA / "level1")}
    with pytest.raises(ValueError, match="level1"):
        renew("123", built, tmp_path / "respaldo", tmp_path / "hashes.json")
    assert not (tmp_path / "respaldo").exists()


def test_build_applies_a_translation_folder(classes, tmp_path):
    out, folder = tmp_path / "juego", tmp_path / "traduccion"
    out.mkdir()
    line = first_line(classes)
    write_jsonl(folder / "escenas" / "DTA0-P1-1.jsonl", [{"id": text_id(line), "es": "Prueba."}])
    assert build(folder, out) == ["resources.assets"]
    assert sha256(out / "resources.assets") != known_hashes()["resources.assets"]
    assert sha256(out / "level1") == known_hashes()["level1"]
