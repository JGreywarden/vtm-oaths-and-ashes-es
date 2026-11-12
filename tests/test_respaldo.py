import hashlib
from pathlib import Path

import pytest

from tools.respaldo import (
    check_build,
    check_original,
    ensure_backup,
    known_build,
    known_hashes,
    load_built,
    natural,
    replace_backups,
    restore_all,
    save_built,
    sha256,
    steam_build,
    still_patched,
)

ORIGINAL = b"original"
EXPECTED = hashlib.sha256(ORIGINAL).hexdigest()


@pytest.fixture
def folders(tmp_path):
    data, backup = tmp_path / "data", tmp_path / "respaldo"
    data.mkdir()
    (data / "level1").write_bytes(ORIGINAL)
    return data, backup


def test_sha256_of_a_file(tmp_path):
    (tmp_path / "f").write_bytes(b"abc")
    assert sha256(tmp_path / "f") == hashlib.sha256(b"abc").hexdigest()


def test_known_hashes_lists_the_files_with_text():
    hashes = known_hashes()
    assert {"resources.assets", "sharedassets1.assets", "level1"} <= set(hashes)
    assert all(len(value) == 64 for value in hashes.values())


def test_known_build_is_a_steam_build_number():
    assert known_build().isdigit()


def test_steam_build_reads_the_manifest(tmp_path):
    manifest = tmp_path / "appmanifest.acf"
    manifest.write_text('"AppState"\n{\n\t"appid"\t\t"1"\n\t"buildid"\t\t"26625395"\n}\n')
    assert steam_build(manifest) == "26625395"


def test_steam_build_is_none_outside_steam(tmp_path):
    assert steam_build(tmp_path / "no_existe.acf") is None
    (tmp_path / "vacio.acf").write_text('"AppState"\n{\n}\n')
    assert steam_build(tmp_path / "vacio.acf") is None


def test_check_build_rejects_a_backup_of_another_version():
    check_build("2", "2")
    check_build(None, "2")
    with pytest.raises(ValueError, match="actualizado"):
        check_build("3", "2")


def test_check_original_rejects_a_modified_file(folders):
    data, _backup = folders
    check_original(data / "level1", EXPECTED)
    (data / "level1").write_bytes(b"parcheado")
    with pytest.raises(ValueError):
        check_original(data / "level1", EXPECTED)


def test_ensure_backup_creates_a_verified_copy(folders):
    data, backup = folders
    assert ensure_backup("level1", EXPECTED, data, backup) == backup / "level1"
    assert (backup / "level1").read_bytes() == ORIGINAL


def test_ensure_backup_never_copies_a_patched_file(folders):
    data, backup = folders
    (data / "level1").write_bytes(b"parcheado")
    with pytest.raises(ValueError):
        ensure_backup("level1", EXPECTED, data, backup)
    assert not (backup / "level1").exists()


def test_ensure_backup_never_overwrites_an_existing_backup(folders):
    data, backup = folders
    ensure_backup("level1", EXPECTED, data, backup)
    (data / "level1").write_bytes(b"parcheado")
    ensure_backup("level1", EXPECTED, data, backup)
    assert (backup / "level1").read_bytes() == ORIGINAL


def test_ensure_backup_detects_a_corrupt_backup(folders):
    data, backup = folders
    ensure_backup("level1", EXPECTED, data, backup)
    (backup / "level1").write_bytes(b"roto")
    with pytest.raises(ValueError):
        ensure_backup("level1", EXPECTED, data, backup)


def test_restore_all_copies_back_only_what_has_a_backup(folders):
    data, backup = folders
    ensure_backup("level1", EXPECTED, data, backup)
    (data / "level1").write_bytes(b"parcheado")
    assert restore_all(["level1", "level2"], data, backup) == ["level1"]
    assert (data / "level1").read_bytes() == ORIGINAL


def test_save_built_and_load_built_remember_what_the_mod_wrote(folders, tmp_path):
    data, _backup = folders
    assert load_built(tmp_path / "construido.json") == {}
    save_built(["level1"], data, tmp_path / "construido.json")
    assert load_built(tmp_path / "construido.json") == {"level1": EXPECTED}
    save_built([], data, tmp_path / "construido.json")
    assert load_built(tmp_path / "construido.json") == {}


def test_natural_sorts_numbers_as_numbers():
    names = ["level10", "level2", "sharedassets1.assets", "level1"]
    assert sorted(names, key=lambda name: natural(Path(name))) == [
        "level1",
        "level2",
        "level10",
        "sharedassets1.assets",
    ]


def test_still_patched_finds_files_the_mod_wrote():
    hashes = {"level1": "aa", "level2": "bb"}
    assert still_patched(hashes, {"level1": "aa", "level2": "otro"}) == ["level1"]
    assert still_patched(hashes, {}) == []


def test_replace_backups_discards_the_previous_version(folders):
    data, backup = folders
    backup.mkdir()
    (backup / "level1").write_bytes(b"de la version anterior")
    (backup / "level9").write_bytes(b"ya no tiene texto")
    replace_backups([data / "level1"], backup)
    assert [path.name for path in backup.iterdir()] == ["level1"]
    assert (backup / "level1").read_bytes() == ORIGINAL
