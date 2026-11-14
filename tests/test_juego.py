from conftest import make_head

from tools.juego import MANAGERS, is_running, object_class, object_name, object_path, owner_id

CLASSES = {7: "DialogueTreeSO"}


def test_object_class_follows_the_script_pointer():
    assert object_class(make_head("x"), [MANAGERS], CLASSES) == "DialogueTreeSO"


def test_object_class_ignores_unknown_scripts_and_other_files():
    assert object_class(make_head("x", script_id=8), [MANAGERS], CLASSES) is None
    assert object_class(make_head("x"), ["resources.assets"], CLASSES) is None
    assert object_class(bytes(28), [MANAGERS], CLASSES) is None


def test_object_name_reads_the_string_at_byte_28():
    assert object_name(make_head("DTA0-P1-1") + b"\x01\x02\x03\x04") == "DTA0-P1-1"


def test_owner_id_reads_the_game_object_pointer():
    raw = bytes(4) + (42).to_bytes(8, "little") + make_head("")[12:]
    assert owner_id(raw) == 42


def test_object_path_climbs_to_the_root():
    nodes = {1: ("Canvas", 0), 2: ("Menu", 1), 3: ("Label", 2)}
    assert object_path(nodes, 3) == "Canvas/Menu/Label"
    assert object_path(nodes, 1) == "Canvas"


def test_object_path_of_an_unknown_object_is_empty_and_a_cycle_ends():
    assert object_path({}, 5) == ""
    assert object_path({1: ("A", 2), 2: ("B", 1)}, 1) == "B/A"


def test_is_running_finds_the_executable_in_the_task_list():
    line = '"Vampire the Masquerade Oaths & Ashes.exe","1234","Console","1","500.000 K"'
    assert is_running('"explorer.exe","1"\n' + line)
    assert not is_running('"explorer.exe","1"\n"steam.exe","2"')
