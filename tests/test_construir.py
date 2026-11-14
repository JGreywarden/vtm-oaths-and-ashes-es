from conftest import make_metadata

from tools.cadenas import text_id
from tools.construir import patch_metadata, patch_object, patch_source, translator
from tools.esquemas import SCHEMAS
from tools.lector import Field, read_fields
from tools.literales import read_literals
from tools.rutas import METADATA

SCHEMA = SCHEMAS["DialogueTreeSO"]
TRANSLATIONS = {
    "escenas/DTA0-P1-1.jsonl": {text_id("Go."): "Ve.", text_id("ALICE"): "no es un hablante"},
    "interfaz/hablantes.jsonl": {text_id("ALICE"): "ALICIA"},
    "escenas/OTRA.jsonl": {text_id("Hello <i>there</i>."): "de otra escena"},
}


def test_translator_looks_in_the_file_of_each_group():
    translate = translator(TRANSLATIONS, "DTA0-P1-1")
    assert translate(Field(0, 0, "Go.", "opcion")) == "Ve."
    assert translate(Field(0, 0, "ALICE", "hablantes")) == "ALICIA"


def test_translator_returns_none_without_translation():
    translate = translator(TRANSLATIONS, "DTA0-P1-1")
    assert translate(Field(0, 0, "Hello <i>there</i>.", "linea")) is None
    assert (
        translator({"interfaz/textos.jsonl": {text_id(""): "x"}}, "")(Field(0, 0, "", "textos"))
        is None
    )


def test_patch_object_without_translations_is_identical(scene):
    assert patch_object(SCHEMA, scene, {}) == scene


def test_patch_object_translates_only_what_has_translation(scene):
    patched = patch_object(SCHEMA, scene, TRANSLATIONS)
    texts = [f.text for f in read_fields(SCHEMA, patched)]
    assert texts == ["ALICIA", "Hello <i>there</i>.", "Ve.", "Not hungry enough"]


def test_patch_object_keeps_identifiers(scene):
    patched = patch_object(SCHEMA, scene, TRANSLATIONS)
    assert patched.count(b"ALICE") == scene.count(b"ALICE") - 1


CODE = {"interfaz/codigo.jsonl": {text_id("Door "): "Puerta ", text_id("internal_key"): "x"}}
DOORS = frozenset({text_id("Door ")})


def test_patch_metadata_without_translations_touches_nothing():
    data = make_metadata(["Door ", "internal_key"])
    assert patch_metadata(data, {}, DOORS) is None
    assert patch_metadata(data, TRANSLATIONS, DOORS) is None


def test_patch_metadata_translates_only_the_closed_list():
    data = make_metadata(["Door ", "internal_key"])
    assert patch_metadata(data, CODE, frozenset()) is None
    assert read_literals(patch_metadata(data, CODE, DOORS)) == [b"Puerta ", b"internal_key"]


def test_patch_source_reads_the_metadata_with_its_own_format(tmp_path):
    source = tmp_path / METADATA.rsplit("/", 1)[-1]
    source.write_bytes(make_metadata(["internal_key"]))
    assert patch_source(source, CODE, {}) is None
