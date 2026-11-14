import struct

import pytest
from conftest import TABLE, make_metadata

from tools.cadenas import text_id
from tools.literales import (
    HEAD,
    patch_literals,
    read_header,
    read_literals,
    rebuild,
    translate_literal,
    visible_text,
    visible_texts,
)

TEXTS = ["", "Door ", "Open the door?", "internal_key"]
VISIBLE = frozenset({text_id("Door "), text_id("Open the door?")})


@pytest.fixture
def metadata() -> bytes:
    return make_metadata(TEXTS)


def test_read_header_finds_the_table_and_the_block(metadata):
    assert read_header(metadata) == (TABLE, 20, 5, TABLE + 20, 31, 4)


def test_read_header_rejects_an_unknown_format(metadata):
    with pytest.raises(ValueError, match="formato"):
        read_header(make_metadata(TEXTS, version=40))
    with pytest.raises(ValueError, match="formato"):
        read_header(b"corto")
    broken = metadata[:16] + struct.pack("<i", 9) + metadata[20:]
    with pytest.raises(ValueError, match="formato"):
        read_header(broken)


def test_read_literals_cuts_each_literal_at_the_next_position(metadata):
    assert read_literals(metadata) == [text.encode() for text in TEXTS]


def test_read_literals_rejects_a_table_that_does_not_fit_the_block(metadata):
    broken = metadata[:24] + struct.pack("<i", 99) + metadata[28:]
    with pytest.raises(ValueError, match="formato"):
        read_literals(broken)


def test_visible_text_only_knows_the_closed_list():
    assert visible_text(b"Door ", VISIBLE) == "Door "
    assert visible_text(b"internal_key", VISIBLE) is None
    assert visible_text(b"\xff\xfe", VISIBLE) is None


def test_visible_texts_lists_the_texts_of_the_closed_list(metadata):
    assert visible_texts(metadata, VISIBLE) == ["Door ", "Open the door?"]


def test_translate_literal_never_changes_a_literal_outside_the_closed_list():
    table = {text_id("Door "): "Puerta ", text_id("internal_key"): "clave"}
    assert translate_literal(b"Door ", table, VISIBLE) == b"Puerta "
    assert translate_literal(b"internal_key", table, VISIBLE) == b"internal_key"
    assert translate_literal(b"Open the door?", table, VISIBLE) == b"Open the door?"


def test_patch_literals_without_translations_is_identical(metadata):
    assert patch_literals(metadata, {}, VISIBLE) is metadata
    assert patch_literals(metadata, {text_id("internal_key"): "clave"}, VISIBLE) is metadata


def test_patch_literals_translates_and_keeps_the_rest(metadata):
    table = {text_id("Open the door?"): "¿Abrir la puerta?"}
    patched = patch_literals(metadata, table, VISIBLE)
    texts = [raw.decode() for raw in read_literals(patched)]
    assert texts == ["", "Door ", "¿Abrir la puerta?", "internal_key"]


def test_rebuild_appends_the_block_and_moves_nothing_else(metadata):
    patched = rebuild(metadata, [b"", b"Puerta ", b"x", b"internal_key"])
    table, size, count, block, block_size, texts = read_header(patched)
    assert (table, size, count, texts) == (TABLE, 20, 5, 4)
    assert block == len(metadata) + (-len(metadata) % 4) and block % 4 == 0
    assert patched[block:] == b"Puerta xinternal_key" and block_size == 20
    assert patched[TABLE + size : len(metadata)] == metadata[TABLE + size :]
    assert patched[HEAD.size : TABLE] == metadata[HEAD.size : TABLE]
