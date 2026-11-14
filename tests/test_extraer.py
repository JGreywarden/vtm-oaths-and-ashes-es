from conftest import make_metadata

from tools.cadenas import ZERO_WIDTH, text_id
from tools.esquemas import SCHEMAS
from tools.extraer import literal_rows, merge_rows, object_rows, source_rows
from tools.lector import Field, read_fields


def test_object_rows_of_a_scene(scene):
    fields = read_fields(SCHEMAS["DialogueTreeSO"], scene)
    assert list(object_rows("DTA0-P1-1", fields)) == [
        (
            "interfaz/hablantes.jsonl",
            {"id": text_id("ALICE"), "en": "ALICE", "objeto": "DTA0-P1-1"},
        ),
        (
            "escenas/DTA0-P1-1.jsonl",
            {
                "id": text_id("Hello <i>there</i>."),
                "en": "Hello <i>there</i>.",
                "tipo": "linea",
                "hablante": "ALICE",
            },
        ),
        ("escenas/DTA0-P1-1.jsonl", {"id": text_id("Go."), "en": "Go.", "tipo": "opcion"}),
        (
            "interfaz/requisitos.jsonl",
            {"id": text_id("Not hungry enough"), "en": "Not hungry enough", "objeto": "DTA0-P1-1"},
        ),
    ]


def test_object_rows_skips_empty_texts_and_forgets_the_speaker_on_narration():
    fields = [
        Field(0, 0, "ALICE", "hablantes"),
        Field(0, 0, "Yes.", "linea"),
        Field(0, 0, "", "hablantes"),
        Field(0, 0, "She nods.", "linea"),
        Field(0, 0, "", "requisitos"),
        Field(0, 0, ZERO_WIDTH, "textos"),
    ]
    rows = [row for _target, row in object_rows("S", fields)]
    assert [row["en"] for row in rows] == ["ALICE", "Yes.", "She nods."]
    assert "hablante" not in rows[2]


def test_object_rows_of_an_unnamed_interface_object_has_no_context():
    assert list(object_rows("", [Field(0, 0, "BACK", "textos")])) == [
        ("interfaz/textos.jsonl", {"id": text_id("BACK"), "en": "BACK"})
    ]


def test_merge_rows_groups_by_file_and_keeps_the_first_of_each_id():
    pairs = [
        ("a", {"id": "1", "en": "x", "hablante": "ALICE"}),
        ("b", {"id": "1", "en": "x"}),
        ("a", {"id": "2", "en": "y"}),
        ("a", {"id": "1", "en": "x", "hablante": "LENZ"}),
    ]
    assert merge_rows(pairs) == {
        "a": [{"id": "1", "en": "x", "hablante": "ALICE"}, {"id": "2", "en": "y"}],
        "b": [{"id": "1", "en": "x"}],
    }


def test_literal_rows_lists_only_the_closed_list():
    assert list(literal_rows(make_metadata(["internal_key", "Door "]))) == []


def test_source_rows_reads_the_metadata_with_its_own_format(tmp_path):
    source = tmp_path / "global-metadata.dat"
    source.write_bytes(make_metadata(["internal_key"]))
    assert list(source_rows(source, {})) == []
