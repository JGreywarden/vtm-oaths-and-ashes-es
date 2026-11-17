import pytest

from tools.traducciones import write_jsonl
from tools.validar import (
    BOX_LINES,
    BOX_WIDTH,
    CAPITAL,
    NOTEBOOK_LINES,
    NOTEBOOK_WIDTH,
    OPTION_WIDTH,
    PANEL_LINES,
    PANEL_WIDTH,
    POPUP_WIDTH,
    SPEAKER_WIDTH,
    box_lines,
    clean_spacing,
    compare_errors,
    compile_terms,
    content_errors,
    edges,
    file_errors,
    fits_box,
    fits_notebook,
    fits_option,
    fits_panel,
    fits_popup,
    fits_speaker,
    format_errors,
    glossary_errors,
    kinds_of,
    load_glossary,
    missing_terms,
    notebook_lines,
    option_width,
    pair_errors,
    panel_lines,
    pending,
    plain,
    popup_kinds,
    popup_lines,
    row_errors,
    same_newlines,
    same_tags,
    scene_kinds,
    space_errors,
    stem,
    stems,
    term_pattern,
    untranslated,
    variant_errors,
    variant_group,
    wrapped_lines,
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


def test_plain_drops_case_and_accents():
    assert plain("Barón") == "baron"
    assert plain("los Vástagos del ELÍSEO") == "los vastagos del eliseo"


def test_stems_gives_one_plain_stem_per_approved_form():
    assert stems("Vástago / Vástagos") == ["vastag", "vastag"]
    assert stems("Barón") == ["baron"]


def test_missing_terms_accepts_a_plural_that_loses_its_accent():
    terms = compile_terms([term("Baron", "Barón")])
    assert missing_terms("The Barons agree.", "Los Barones están de acuerdo.", terms) == []
    assert missing_terms("The Barons agree.", "Los jefes están de acuerdo.", terms) == ["Baron"]


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


def filled(lines: int) -> str:
    """texto inventado que ocupa justo ese número de líneas del cuadro."""
    return " ".join(["x" * BOX_WIDTH] * lines)


def test_box_lines_wraps_at_the_box_width_and_ignores_tags():
    assert box_lines("Hola.") == 1
    assert box_lines(filled(3)) == 3
    assert box_lines("<i>" + "x" * (BOX_WIDTH - 1) + "</i> y") == 2
    assert box_lines("<i>" + "x" * (BOX_WIDTH - 2) + "</i> y") == 1


def test_fits_box_allows_what_the_box_or_the_original_holds():
    assert fits_box("Hello.", filled(BOX_LINES))
    assert not fits_box("Hello.", filled(BOX_LINES + 1))
    assert fits_box(filled(BOX_LINES + 1), filled(BOX_LINES + 1))
    assert not fits_box(filled(BOX_LINES + 1), filled(BOX_LINES + 2))


def test_option_width_counts_capitals_as_wider_and_ignores_tags():
    assert option_width("abc.") == 4
    assert option_width("ABC.") == pytest.approx(3 * CAPITAL + 1)
    assert option_width(" <i>abc</i> ") == 3


def test_fits_option_allows_what_the_line_or_the_original_holds():
    assert fits_option("Go.", "x" * OPTION_WIDTH)
    assert not fits_option("Go.", "x" * (OPTION_WIDTH + 1))
    assert fits_option("x" * (OPTION_WIDTH + 5), "y" * (OPTION_WIDTH + 5))
    assert not fits_option("x" * (OPTION_WIDTH + 5), "y" * (OPTION_WIDTH + 6))
    assert not fits_option("Go.", "[" + "X" * OPTION_WIDTH + "]")


def test_fits_speaker_allows_what_the_label_or_the_original_holds():
    assert fits_speaker("GUARD", "X" * SPEAKER_WIDTH)
    assert not fits_speaker("GUARD", "X" * (SPEAKER_WIDTH + 1))
    assert fits_speaker("X" * (SPEAKER_WIDTH + 3), "Y" * (SPEAKER_WIDTH + 3))
    assert not fits_speaker("X" * (SPEAKER_WIDTH + 3), "Y" * (SPEAKER_WIDTH + 4))


def paragraphs(first: int, second: int) -> str:
    """dos párrafos de esas líneas en un recuadro del mapa, separados por una en blanco."""
    line = "x" * (PANEL_WIDTH - 1)
    return " ".join([line] * first) + "\n\n" + " ".join([line] * second)


def test_panel_lines_counts_the_blank_line_between_paragraphs():
    assert panel_lines("Zona norte.") == 1
    assert panel_lines(paragraphs(3, 2)) == 3 + 1 + 2
    assert panel_lines("<b>" + "x" * PANEL_WIDTH + "</b>") == 1


def test_fits_panel_allows_what_the_panel_or_the_original_holds():
    assert fits_panel("Short.", paragraphs(7, PANEL_LINES - 8))
    assert not fits_panel("Short.", paragraphs(7, PANEL_LINES - 7))
    assert fits_panel(paragraphs(8, PANEL_LINES - 7), paragraphs(7, PANEL_LINES - 6))
    assert not fits_panel(paragraphs(8, PANEL_LINES - 7), paragraphs(8, PANEL_LINES - 6))


def test_space_errors_reports_a_map_panel_text_that_overflows():
    long_text = paragraphs(7, PANEL_LINES - 7)
    assert space_errors("Short.", long_text, "") == []
    assert space_errors("Short.", long_text, "panel") == [
        f"no cabe en el recuadro del mapa: ocupa {PANEL_LINES + 1} líneas"
    ]


def test_wrapped_lines_wraps_each_paragraph_and_ignores_tags():
    assert wrapped_lines("uno dos tres", 7) == 2
    assert wrapped_lines("uno\n\ndos", 7) == 3
    assert wrapped_lines("<i>uno dos</i>", 7) == 1


def popup_text(lines: int) -> str:
    """párrafo de aviso que ocupa esas líneas."""
    return " ".join(["x" * (POPUP_WIDTH - 1)] * lines)


def test_popup_lines_wraps_at_the_popup_width():
    assert popup_lines("Usa la fórmula.") == 1
    assert popup_lines(popup_text(3)) == 3


def test_fits_popup_allows_no_more_lines_than_the_original():
    assert fits_popup(popup_text(3), popup_text(3))
    assert fits_popup(popup_text(3), popup_text(2))
    assert not fits_popup(popup_text(3), popup_text(4))


def test_space_errors_reports_a_popup_paragraph_longer_than_the_original():
    assert space_errors(popup_text(2), popup_text(3), "") == []
    assert space_errors(popup_text(2), popup_text(3), "aviso") == [
        "pisa la leyenda del aviso: ocupa 3 líneas y el original 2"
    ]
    assert space_errors(popup_text(2), popup_text(2), "aviso") == []


def notebook_text(lines: int) -> str:
    """texto que ocupa esas líneas en el cuaderno del laboratorio."""
    return " ".join(["x" * (NOTEBOOK_WIDTH - 1)] * lines)


def test_notebook_lines_wraps_at_the_notebook_width():
    assert notebook_lines("Efecto: calma.") == 1
    assert notebook_lines(notebook_text(4)) == 4


def test_fits_notebook_allows_the_lines_of_the_original_or_of_an_effect():
    assert fits_notebook("Effect.", notebook_text(NOTEBOOK_LINES))
    assert not fits_notebook("Effect.", notebook_text(NOTEBOOK_LINES + 1))
    assert fits_notebook(notebook_text(9), notebook_text(9))
    assert not fits_notebook(notebook_text(9), notebook_text(10))


def test_space_errors_reports_a_notebook_text_longer_than_the_original():
    assert space_errors(notebook_text(9), notebook_text(10), "") == []
    assert space_errors(notebook_text(9), notebook_text(10), "cuaderno") == [
        "no cabe en el cuaderno del laboratorio: ocupa 10 líneas y el original 9"
    ]


def test_popup_kinds_keeps_the_paragraphs_of_popups_with_a_legend():
    rows = [
        {"id": "a", "en": "x", "objeto": "BrewTutorial/Bg/Body/Description/Text (TMP)"},
        {"id": "b", "en": "y", "objeto": "BrewTutorial/Bg/Body/Text (TMP) (1)"},
        {"id": "c", "en": "z", "objeto": "LinksTutorial/Bg/Body/Description/Text (TMP)"},
        {"id": "d", "en": "w", "objeto": "BrewTutorial/Bg/Heading/Text (TMP)"},
    ]
    assert popup_kinds(rows) == {"a": "aviso"}


def test_space_errors_reports_a_speaker_label_that_is_too_long():
    long_label = "X" * (SPEAKER_WIDTH + 1)
    assert space_errors("GUARD", long_label, "") == []
    assert space_errors("GUARD", long_label, "hablante") == [
        f"no cabe en la etiqueta de hablante: {SPEAKER_WIDTH + 1} caracteres"
    ]
    assert space_errors("GUARD", "GUARDIA", "hablante") == []


def test_space_errors_depends_on_where_the_string_is_shown():
    long_line, long_option = filled(BOX_LINES + 1), "x" * (OPTION_WIDTH + 1)
    assert space_errors("Hello.", long_line, "") == []
    assert space_errors("Hello.", long_line, "linea") == [
        f"no cabe en el cuadro de diálogo: ocupa {BOX_LINES + 1} líneas"
    ]
    assert space_errors("Go.", long_option, "linea") == []
    assert space_errors("Go.", long_option, "opcion") == [
        f"no cabe en una línea de opción: ancho {OPTION_WIDTH + 1}"
    ]


def test_pair_errors_reports_overflow_only_where_it_is_shown():
    row = {"id": "x", "es": filled(BOX_LINES + 1)}
    assert pair_errors("Hello.", row, TERMS) == []
    overflow = f"no cabe en el cuadro de diálogo: ocupa {BOX_LINES + 1} líneas"
    assert pair_errors("Hello.", row, TERMS, "linea") == [overflow]
    option = {"id": "x", "es": "x" * (OPTION_WIDTH + 1)}
    assert pair_errors("Go.", option, TERMS) == []
    assert len(pair_errors("Go.", option, TERMS, "opcion")) == 1


def test_scene_kinds_keeps_lines_and_options_of_a_scene():
    rows = [
        {"id": "a", "en": "x", "tipo": "linea"},
        {"id": "b", "en": "y", "tipo": "opcion"},
        {"id": "c", "en": "z", "objeto": "Menu"},
    ]
    assert scene_kinds(rows) == {"a": "linea", "b": "opcion"}


def test_kinds_of_treats_the_whole_speakers_file_as_labels():
    labels = [{"id": "a", "en": "GUARD", "objeto": "S"}, {"id": "b", "en": "MAN", "objeto": "S"}]
    assert kinds_of("interfaz/hablantes.jsonl", labels) == {"a": "hablante", "b": "hablante"}
    assert kinds_of("interfaz/influencia.jsonl", labels) == {"a": "panel", "b": "panel"}
    assert kinds_of("interfaz/alquimia.jsonl", labels) == {"a": "cuaderno", "b": "cuaderno"}
    assert kinds_of("interfaz/textos.jsonl", labels) == {}
    popup = [
        {"id": "a", "en": "x", "objeto": "BrewTutorial/Bg/Body/Description/Text (TMP)"},
        {"id": "b", "en": "y", "objeto": "BrewTutorial/Bg/Body/Text (TMP)"},
    ]
    assert kinds_of("interfaz/textos.jsonl", popup) == {"a": "aviso"}
    scene = [{"id": "a", "en": "x", "tipo": "linea"}]
    assert kinds_of("escenas/S.jsonl", scene) == {"a": "linea"}


def test_compare_errors_reports_unknown_ids():
    rows = [{"id": "a", "es": "Hola."}, {"id": "b", "es": "Adiós."}]
    assert compare_errors(rows, {"a": "Hello."}, TERMS) == ["b: el id no existe en el original"]


def test_compare_errors_checks_the_box_for_the_given_ids():
    rows = [{"id": "a", "es": filled(BOX_LINES + 1)}, {"id": "b", "es": filled(BOX_LINES + 1)}]
    errors = compare_errors(rows, {"a": "Hello.", "b": "Bye."}, TERMS, {"a": "linea"})
    assert len(errors) == 1 and errors[0].startswith("a: no cabe en el cuadro")


def test_compare_errors_checks_the_option_line_for_the_given_ids():
    rows = [{"id": "a", "es": "x" * (OPTION_WIDTH + 1)}, {"id": "b", "es": "Vete."}]
    kinds = {"a": "opcion", "b": "opcion"}
    errors = compare_errors(rows, {"a": "Go.", "b": "Leave."}, TERMS, kinds)
    assert len(errors) == 1 and errors[0].startswith("a: no cabe en una línea de opción")


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


def test_variant_group_is_the_part_of_a_scene_with_h_or_hl():
    assert variant_group("escenas/DTA1-P5-01H.jsonl") == "DTA1-P5"
    assert variant_group("escenas/DTA1-P5-06HL.jsonl") == "DTA1-P5"
    assert variant_group("escenas/DTA1-P6-1HL.jsonl") == "DTA1-P6"
    assert variant_group("escenas/DTA1-P3-4.jsonl") is None
    assert variant_group("interfaz/textos.jsonl") is None


def test_variant_errors_asks_for_the_same_translation_within_a_part():
    files = {
        "escenas/DTA1-P5-01H.jsonl": [{"id": "a", "es": "Hola."}, {"id": "b", "es": "Vete."}],
        "escenas/DTA1-P5-02HL.jsonl": [{"id": "a", "es": "Buenas."}, {"id": "b", "es": "Vete."}],
        "escenas/DTA1-P6-1H.jsonl": [{"id": "a", "es": "Saludos."}],
        "escenas/DTA1-P3-4.jsonl": [{"id": "a", "es": "Qué tal."}],
    }
    wrong = "escenas/DTA1-P5-02HL.jsonl: a: traducción distinta de la de escenas/DTA1-P5-01H.jsonl"
    assert variant_errors(files) == [wrong]


def test_format_errors_compares_the_variants_of_a_part(tmp_path):
    folder = tmp_path / "traduccion"
    write_jsonl(folder / "escenas" / "DTA1-P5-01H.jsonl", [{"id": "aaaaaaaaaaaa", "es": "Sí."}])
    write_jsonl(folder / "escenas" / "DTA1-P5-01HL.jsonl", [{"id": "aaaaaaaaaaaa", "es": "Sí."}])
    assert format_errors(folder) == []
    write_jsonl(folder / "escenas" / "DTA1-P5-01HL.jsonl", [{"id": "aaaaaaaaaaaa", "es": "Ya."}])
    assert len(format_errors(folder)) == 1


def test_content_errors_compares_with_the_originals(trees):
    folder, originals = trees
    assert content_errors(folder, originals, TERMS) == []
    write_jsonl(folder / "escenas" / "S.jsonl", [{"id": "aaaaaaaaaaaa", "es": "Hola.\n"}])
    write_jsonl(folder / "escenas" / "X.jsonl", [{"id": "aaaaaaaaaaaa", "es": "Hola."}])
    errors = content_errors(folder, originals, TERMS)
    assert errors[0].startswith("escenas/S.jsonl: aaaaaaaaaaaa: saltos de línea")
    assert errors[-1] == "escenas/X.jsonl: no corresponde a ningún archivo del juego"


def test_content_errors_checks_the_box_only_for_scene_lines(tmp_path):
    originals, folder = tmp_path / "originales", tmp_path / "traduccion"
    rows = [
        {"id": "aaaaaaaaaaaa", "en": "Hello.", "tipo": "linea"},
        {"id": "bbbbbbbbbbbb", "en": "Bye.", "tipo": "opcion"},
    ]
    write_jsonl(originals / "escenas" / "S.jsonl", rows)
    long = filled(BOX_LINES + 1)
    done = [{"id": "aaaaaaaaaaaa", "es": long}, {"id": "bbbbbbbbbbbb", "es": "Adiós."}]
    write_jsonl(folder / "escenas" / "S.jsonl", done)
    errors = content_errors(folder, originals, TERMS)
    assert len(errors) == 1 and "aaaaaaaaaaaa: no cabe en el cuadro" in errors[0]


def test_content_errors_checks_the_width_only_for_scene_options(tmp_path):
    originals, folder = tmp_path / "originales", tmp_path / "traduccion"
    rows = [
        {"id": "aaaaaaaaaaaa", "en": "Hello.", "tipo": "linea"},
        {"id": "bbbbbbbbbbbb", "en": "Bye.", "tipo": "opcion"},
    ]
    write_jsonl(originals / "escenas" / "S.jsonl", rows)
    wide = "x" * (OPTION_WIDTH + 1)
    done = [{"id": "aaaaaaaaaaaa", "es": wide}, {"id": "bbbbbbbbbbbb", "es": wide}]
    write_jsonl(folder / "escenas" / "S.jsonl", done)
    errors = content_errors(folder, originals, TERMS)
    assert len(errors) == 1 and "bbbbbbbbbbbb: no cabe en una línea de opción" in errors[0]


def test_content_errors_checks_the_length_only_for_speaker_labels(tmp_path):
    originals, folder = tmp_path / "originales", tmp_path / "traduccion"
    rows = [{"id": "aaaaaaaaaaaa", "en": "GUARD", "objeto": "S"}]
    long = "X" * (SPEAKER_WIDTH + 1)
    for name in ("hablantes", "textos"):
        write_jsonl(originals / "interfaz" / f"{name}.jsonl", rows)
        write_jsonl(folder / "interfaz" / f"{name}.jsonl", [{"id": "aaaaaaaaaaaa", "es": long}])
    errors = content_errors(folder, originals, TERMS)
    assert len(errors) == 1 and errors[0].startswith("interfaz/hablantes.jsonl: aaaaaaaaaaaa")


def test_pending_lists_untranslated_strings_per_file(trees):
    folder, originals = trees
    assert pending(folder, originals) == {
        "escenas/S.jsonl": [{"id": "bbbbbbbbbbbb", "en": "Bye."}],
        "interfaz/textos.jsonl": [{"id": "cccccccccccc", "en": "BACK"}],
    }
