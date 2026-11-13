import pytest

from tools.traducciones import write_jsonl
from tools.validar import (
    clean_spacing,
    compare_errors,
    compile_terms,
    content_errors,
    edges,
    file_errors,
    format_errors,
    glossary_errors,
    load_glossary,
    missing_terms,
    pair_errors,
    pending,
    row_errors,
    same_newlines,
    same_tags,
    stem,
    term_pattern,
    untranslated,
)


def term(en, es, estado="oficial"):
    return {"en": en, "es": es, "categoria": "x", "estado": estado, "notas": ""}


TERMS = compile_terms(
    [
        term("Kindred", "Vástago / Vástagos"),
        term("the Beast", "la Bestia"),
        term("stake", "estaca / estacar"),
        term("Embrace", "Abrazo / Abrazar / Abrazado"),
        term("lick", "chupóptero", estado="propuesto"),
    ]
)


def test_load_glossary_reads_rows_as_dicts(tmp_path):
    path = tmp_path / "g.csv"
    path.write_text("en,es,categoria,estado,notas\nkine,ganado,x,oficial,\n", encoding="utf-8")
    assert load_glossary(path) == [term("kine", "ganado")]


def test_glossary_errors_accepts_good_rows():
    assert glossary_errors([term("kine", "ganado"), term("sire", "sire", "pendiente")]) == []


def test_glossary_errors_reports_duplicates_and_malformed_rows():
    rows = [
        term("kine", "ganado"),
        term("kine", "reses"),
        term("sire", ""),
        term("boon", "favor", estado="quizá"),
        {"en": "a", "es": "b", "categoria": "c", "estado": "oficial", "notas": "", None: ["z"]},
        {"en": "a", "es": "b", "categoria": None, "estado": None, "notas": None},
    ]
    errors = glossary_errors(rows)
    assert [e.split(":")[0] for e in errors] == [f"glosario, fila {n}" for n in range(3, 8)]
    assert "repetido" in errors[0] and "columnas" in errors[3] and "columnas" in errors[4]


@pytest.mark.parametrize(
    ("glossary_term", "text", "found"),
    [
        ("Kindred", "Few Kindred would agree.", True),
        ("Kindred", "a kindred spirit", False),
        ("Anarch", "the Anarchs and the Prince’s men", True),
        ("stake", "The stakes are high", True),
        ("stake", "a mistake", False),
        ("herd", "they kept herding us", False),
        ("the Beast", "The Beast stirs.", True),
        ("the Beast", "the beast of burden", False),
        ("Crow", "Crow's hideout", True),
        ("haven", "We haven’t moved since dusk.", False),
        ("haven", "I haven't seen it.", False),
        ("haven", "The haven’s door was open.", True),
    ],
)
def test_term_pattern_matches_whole_terms(glossary_term, text, found):
    assert bool(term_pattern(glossary_term).search(text)) is found


def test_stem_accepts_gender_and_number():
    assert stem("Abrazado") in "fue abrazada"
    assert stem("Vástagos") in "los vástagos"
    assert stem("la Bestia") in "de la bestia" and stem("el Coto") in "al coto"
    assert stem("sire") == "sire"


def test_compile_terms_keeps_only_decided_terms():
    assert [t[0] for t in TERMS] == ["Kindred", "the Beast", "stake", "Embrace"]


def test_missing_terms_reports_terms_without_their_approved_form():
    assert missing_terms(
        "Most Kindred fear the Beast.", "Los vampiros temen a la Bestia.", TERMS
    ) == ["Kindred"]
    assert missing_terms("Kindred fear the Beast.", "Los Vástagos temen a la Bestia.", TERMS) == []
    assert missing_terms("A lick.", "Un vampiro.", TERMS) == []


def test_same_tags():
    assert same_tags("a <i>b</i> c", "x <i>y</i>")
    assert not same_tags("a <i>b</i>", "a <i>b")
    assert not same_tags("a <b>b</b>", "a <i>b</i>")


def test_same_newlines():
    assert same_newlines("a\n\nb", "x\n\ny")
    assert not same_newlines("a\nb", "a b")
    assert not same_newlines("a\r\nb", "a\nb")


def test_edges_ignores_invisible_characters():
    assert edges("​​Hola ") == ("", " ")
    assert edges(" The Camarilla") == (" ", "")


def test_clean_spacing():
    assert clean_spacing("​Hello.", "Hola.")
    assert clean_spacing(" The Camarilla", " La Camarilla")
    assert not clean_spacing("Hello.", "Hola. ")
    assert not clean_spacing("Hello.", "Hola,  qué tal.")
    assert not clean_spacing("Hello.", "Ho​la.")
    assert clean_spacing("a  b", "x  y")


def test_row_errors():
    assert row_errors({"id": "3f9a1c2b7d40", "es": "Texto."}) == []
    assert row_errors({"id": "3F9A", "es": "Texto."}) == ["id mal formado"]
    assert row_errors({"id": "3f9a1c2b7d40", "es": "  "}) == ["traducción vacía"]
    assert row_errors({"es": None}) == ["id mal formado", "traducción vacía"]


def test_file_errors_reports_repeated_ids_and_bad_rows():
    rows = [
        {"id": "3f9a1c2b7d40", "es": "a"},
        {"id": "3f9a1c2b7d40", "es": "b"},
        {"id": "000000000001", "es": ""},
    ]
    assert file_errors(rows) == ["3f9a1c2b7d40: id repetido", "000000000001: traducción vacía"]


def test_pair_errors_of_a_good_translation():
    row = {"id": "x", "es": "Pocos <i>Vástagos</i> estarían de acuerdo."}
    assert pair_errors("Few <i>Kindred</i> would agree.", row, TERMS) == []


def test_pair_errors_reports_each_problem():
    row = {"id": "x", "es": "Pocos vampiros estarían de acuerdo. "}
    errors = pair_errors("Few <i>Kindred</i>\nwould agree.", row, TERMS)
    assert len(errors) == 4 and errors[3] == "falta el término del glosario: Kindred"


def test_pair_errors_allows_declared_glossary_exceptions():
    row = {"id": "x", "es": "Hay mucho en juego.", "sin_glosario": ["stake"]}
    assert pair_errors("The stakes are high.", row, TERMS) == []
    assert pair_errors("The stakes are high.", {"id": "x", "es": row["es"]}, TERMS) != []


def test_compare_errors_reports_unknown_ids():
    rows = [{"id": "a", "es": "Hola."}, {"id": "b", "es": "Adiós."}]
    assert compare_errors(rows, {"a": "Hello."}, TERMS) == ["b: el id no existe en el original"]


def test_untranslated():
    originals = [{"id": "a", "en": "x"}, {"id": "b", "en": "y"}]
    assert untranslated(originals, {"a"}) == [{"id": "b", "en": "y"}]


@pytest.fixture
def trees(tmp_path):
    originals, folder = tmp_path / "originales", tmp_path / "traduccion"
    rows = [{"id": "aaaaaaaaaaaa", "en": "Hello."}, {"id": "bbbbbbbbbbbb", "en": "Bye."}]
    write_jsonl(originals / "escenas" / "S.jsonl", rows)
    write_jsonl(originals / "interfaz" / "textos.jsonl", [{"id": "cccccccccccc", "en": "BACK"}])
    write_jsonl(folder / "escenas" / "S.jsonl", [{"id": "aaaaaaaaaaaa", "es": "Hola."}])
    return folder, originals


def test_format_errors_names_the_file(trees):
    folder, _originals = trees
    assert format_errors(folder) == []
    write_jsonl(folder / "escenas" / "S.jsonl", [{"id": "aaaaaaaaaaaa", "es": ""}])
    assert format_errors(folder) == ["escenas/S.jsonl: aaaaaaaaaaaa: traducción vacía"]


def test_content_errors_compares_with_the_originals(trees):
    folder, originals = trees
    assert content_errors(folder, originals, TERMS) == []
    write_jsonl(folder / "escenas" / "S.jsonl", [{"id": "aaaaaaaaaaaa", "es": "Hola.\n"}])
    write_jsonl(folder / "escenas" / "X.jsonl", [{"id": "aaaaaaaaaaaa", "es": "Hola."}])
    errors = content_errors(folder, originals, TERMS)
    assert errors[0].startswith("escenas/S.jsonl: aaaaaaaaaaaa: saltos de línea")
    assert errors[-1] == "escenas/X.jsonl: no corresponde a ningún archivo del juego"


def test_pending_lists_untranslated_strings_per_file(trees):
    folder, originals = trees
    assert pending(folder, originals) == {
        "escenas/S.jsonl": [{"id": "bbbbbbbbbbbb", "en": "Bye."}],
        "interfaz/textos.jsonl": [{"id": "cccccccccccc", "en": "BACK"}],
    }
