import pytest

from tools.cadenas import pack_string, read_string, text_id


def test_text_id_is_first_12_hex_chars_of_sha1():
    assert text_id("abc") == "a9993e364706"


def test_text_id_uses_utf8():
    assert text_id("ñ") != text_id("n")
    assert len(text_id("ñ")) == 12


def test_pack_string_pads_to_multiple_of_four():
    assert pack_string("abcde") == b"\x05\x00\x00\x00abcde\x00\x00\x00"
    assert pack_string("abcd") == b"\x04\x00\x00\x00abcd"
    assert pack_string("") == b"\x00\x00\x00\x00"


def test_pack_string_counts_bytes_not_characters():
    assert pack_string("ñ") == b"\x02\x00\x00\x00\xc3\xb1\x00\x00"


def test_read_string_returns_text_and_next_position():
    data = b"\xff" * 4 + pack_string("¿Qué?") + pack_string("x")
    text, end = read_string(data, 4)
    assert text == "¿Qué?"
    assert read_string(data, end) == ("x", len(data))


@pytest.mark.parametrize(
    "data",
    [
        b"\x01\x00",  # no cabe la longitud
        b"\x09\x00\x00\x00abc",  # longitud mayor que los datos
        b"\xff\xff\xff\xffabcd",  # longitud negativa
        b"\x01\x00\x00\x00a\x00\x01\x00",  # relleno que no es cero
        b"\x02\x00\x00\x00\xff\xfe\x00\x00",  # no es utf-8
    ],
)
def test_read_string_rejects_malformed_data(data):
    with pytest.raises(ValueError):
        read_string(data, 0)
