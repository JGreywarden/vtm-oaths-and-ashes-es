from tools.cadenas import text_id
from tools.construir import patch_object, translator
from tools.esquemas import SCHEMAS
from tools.lector import Field, read_fields

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
