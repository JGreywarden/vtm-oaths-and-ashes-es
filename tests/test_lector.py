import pytest

from tools.cadenas import pack_string
from tools.esquemas import SCHEMAS
from tools.lector import Field, read_fields, replace_texts

SCHEMA = (4, "str", "text:a", [2 * 4, "text:b"], "rest")


def sample() -> bytes:
    items = bytes(8) + pack_string("uno") + bytes(8) + pack_string("dos")
    count = (2).to_bytes(4, "little")
    return bytes(4) + pack_string("ID") + pack_string("Hola") + count + items + b"\x07" * 5


def test_read_fields_finds_visible_texts_with_their_group():
    fields = read_fields(SCHEMA, sample())
    assert [(f.text, f.group) for f in fields] == [("Hola", "a"), ("uno", "b"), ("dos", "b")]
    assert sample()[fields[0].start : fields[0].end] == pack_string("Hola")


def test_read_fields_requires_exact_end():
    with pytest.raises(ValueError):
        read_fields(SCHEMA[:-1], sample())


def test_read_fields_rejects_data_that_does_not_fit():
    with pytest.raises(ValueError):
        read_fields(SCHEMA, sample()[:30])
    with pytest.raises(ValueError):
        read_fields((4, ["str"]), bytes(4) + b"\xff\xff\xff\x7f")


def test_read_fields_understands_a_scene(scene):
    fields = read_fields(SCHEMAS["DialogueTreeSO"], scene)
    assert [(f.text, f.group) for f in fields] == [
        ("ALICE", "hablantes"),
        ("Hello <i>there</i>.", "linea"),
        ("Go.", "opcion"),
        ("Not hungry enough", "requisitos"),
    ]


def test_replace_texts_without_translations_keeps_data_identical():
    data = sample()
    assert replace_texts(data, read_fields(SCHEMA, data), lambda field: None) == data


def test_replace_texts_replaces_by_position_and_keeps_the_rest():
    data = sample()
    new = {"Hola": "Buenas noches", "dos": "2"}
    patched = replace_texts(data, read_fields(SCHEMA, data), lambda f: new.get(f.text))
    texts = [f.text for f in read_fields(SCHEMA, patched)]
    assert texts == ["Buenas noches", "uno", "2"]
    assert patched.startswith(bytes(4) + pack_string("ID"))
    assert patched.endswith(b"\x07" * 5)


def test_replace_texts_does_not_touch_an_identifier_with_the_same_text():
    data = bytes(4) + pack_string("ALICE") + pack_string("ALICE") + (0).to_bytes(4, "little")
    patched = replace_texts(data, read_fields(SCHEMA, data), lambda f: "ALICIA")
    assert patched == bytes(4) + pack_string("ALICE") + pack_string("ALICIA") + bytes(4)


def test_field_is_a_plain_tuple():
    assert Field(0, 8, "x", "linea") == (0, 8, "x", "linea")
