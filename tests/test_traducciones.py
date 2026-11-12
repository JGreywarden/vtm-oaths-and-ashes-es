from tools.traducciones import (
    jsonl_files,
    load_jsonl,
    load_translations,
    target_file,
    write_jsonl,
)

ROWS = [{"id": "3f9a1c2b7d40", "es": "¿Qué «tal»?\n—Bien…"}, {"id": "000000000001", "es": "x"}]


def test_target_file_sends_scene_text_to_its_scene():
    assert target_file("linea", "DTA0-P1-1") == "escenas/DTA0-P1-1.jsonl"
    assert target_file("opcion", "DTA0-P1-1") == "escenas/DTA0-P1-1.jsonl"


def test_target_file_shares_interface_text_by_kind():
    assert target_file("hablantes", "DTA0-P1-1") == "interfaz/hablantes.jsonl"
    assert target_file("textos", "") == "interfaz/textos.jsonl"


def test_write_jsonl_and_load_jsonl_round_trip(tmp_path):
    path = tmp_path / "escenas" / "a.jsonl"
    write_jsonl(path, ROWS)
    assert load_jsonl(path) == ROWS


def test_write_jsonl_writes_one_readable_line_per_row(tmp_path):
    write_jsonl(tmp_path / "a.jsonl", ROWS)
    lines = (tmp_path / "a.jsonl").read_bytes().split(b"\n")
    assert len(lines) == 3 and lines[2] == b""
    assert "¿Qué «tal»?".encode() in lines[0] and b"\r" not in lines[0]


def test_load_jsonl_skips_blank_lines(tmp_path):
    (tmp_path / "a.jsonl").write_text('\n{"id": "a", "es": "b"}\n\n', encoding="utf-8")
    assert load_jsonl(tmp_path / "a.jsonl") == [{"id": "a", "es": "b"}]


def test_jsonl_files_uses_relative_paths(tmp_path):
    write_jsonl(tmp_path / "interfaz" / "diario.jsonl", ROWS)
    (tmp_path / "glosario.csv").write_text("en,es\n", encoding="utf-8")
    assert jsonl_files(tmp_path) == {"interfaz/diario.jsonl": tmp_path / "interfaz/diario.jsonl"}


def test_load_translations_maps_ids_per_file(tmp_path):
    write_jsonl(tmp_path / "escenas" / "a.jsonl", ROWS)
    assert load_translations(tmp_path) == {
        "escenas/a.jsonl": {"3f9a1c2b7d40": "¿Qué «tal»?\n—Bien…", "000000000001": "x"}
    }
    assert load_translations(tmp_path / "vacio") == {}
