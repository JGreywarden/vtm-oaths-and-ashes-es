"""comprobaciones sobre los datos de traduccion/ y listado de cadenas sin traducir."""

import csv
import re
import sys
import textwrap
import unicodedata
from pathlib import Path

from tools.cadenas import ZERO_WIDTH
from tools.rutas import GLOSSARY, ORIGINALS, TRANSLATION
from tools.traducciones import jsonl_files, load_jsonl

TAG = re.compile(r"<[^<>]+>")
NEWLINE = re.compile(r"\r\n|\n")
ID = re.compile(r"[0-9a-f]{12}")
# escena con variante: con mano (h) o sin mano (hl); el grupo es el acto y la parte
VARIANT = re.compile(r"(.+-P\d+)-\d+HL?")
COLUMNS = ["en", "es", "categoria", "estado", "notas"]
STATES = {"oficial", "aprobado", "propuesto", "pendiente"}
ENFORCED = {"oficial", "aprobado"}
INVISIBLE = ZERO_WIDTH
# el cuadro de diálogo no desplaza el texto: medido en el juego, caben cuatro líneas de
# unos 78 caracteres con una letra proporcional; el ancho se deja algo por debajo
BOX_WIDTH = 76
BOX_LINES = 4
# una opción va en una sola línea y la siguiente se dibuja justo debajo: si se parte, la
# pisa. medido en el juego, cabe un ancho de unos 56 caracteres contando cada mayúscula
# como 1,4, porque las etiquetas de poder en mayúsculas ocupan bastante más
OPTION_WIDTH = 56
CAPITAL = 1.4
# la etiqueta de hablante va en una línea encima del texto: si se parte, lo pisa. medido
# en el juego, 21 caracteres caben y 25 no; la etiqueta más larga del original tiene 22
SPEAKER_WIDTH = 22
SPEAKERS = "interfaz/hablantes.jsonl"
# el recuadro de una banda en el mapa de influencia no desplaza el texto: medido en el
# juego, caben 13 líneas de unos 50 caracteres, contando la línea en blanco entre párrafos
PANEL_WIDTH = 50
PANEL_LINES = 13
PANELS = "interfaz/influencia.jsonl"
# en el cuaderno del laboratorio la línea de efecto va en posición fija debajo de la ficha
# y las flechas, debajo del efecto: un texto que ocupa más líneas que el original pisa lo
# que tiene debajo. medido en el juego: unos 53 caracteres por línea y dos líneas de efecto
NOTEBOOK_WIDTH = 53
NOTEBOOK_LINES = 2
NOTEBOOK = "interfaz/alquimia.jsonl"
# archivos cuyas cadenas se muestran todas en el mismo sitio
FILE_KINDS = {SPEAKERS: "hablante", PANELS: "panel", NOTEBOOK: "cuaderno"}
# en un aviso emergente con leyenda, la leyenda va en posición fija debajo del párrafo: si
# el párrafo ocupa más líneas que el original, la pisa. se compara con unos 74 caracteres
POPUP_WIDTH = 74
DESCRIPTION = re.compile(r"(.+)/Bg/Body/Description\d*/Text \(TMP\)")
LEGEND = re.compile(r"(.+)/Bg/Body/Text \(TMP\)")

Term = tuple[str, re.Pattern, list[str]]


def load_glossary(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def glossary_errors(rows: list[dict]) -> list[str]:
    """filas mal formadas o repetidas; la fila 1 es la cabecera."""
    errors, seen = [], set()
    for number, row in enumerate(rows, start=2):
        if list(row) != COLUMNS or None in row.values():
            errors.append(f"glosario, fila {number}: número de columnas incorrecto")
        elif not row["en"] or not row["es"] or row["estado"] not in STATES:
            errors.append(f"glosario, fila {number}: término vacío o estado desconocido")
        elif row["en"] in seen:
            errors.append(f"glosario, fila {number}: término repetido ({row['en']})")
        seen.add(row.get("en"))
    return errors


def term_pattern(term: str) -> re.Pattern:
    """el término entero, con plural o posesivo; un término en mayúscula exige la mayúscula.

    una contracción no es el término: «haven’t» no contiene «haven».
    """
    body = re.escape(term)
    if term.startswith("the "):
        body = "[Tt]" + body[1:]
    flags = re.IGNORECASE if term == term.lower() else 0
    return re.compile(rf"\b{body}(?:e?s|['’]s)?\b(?!['’]\w)", flags)


def stem(form: str) -> str:
    """raíz aproximada, para aceptar género y número: abrazado, abrazada, abrazados."""
    form = re.sub(r"^(el|la|los|las) ", "", form.lower())
    root = form.rstrip("s").rstrip("aeo")
    return root if len(root) >= 4 else form


def plain(text: str) -> str:
    """minúsculas y sin tildes: el plural de «barón» es «barones» y pierde la suya."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def stems(forms: str) -> list[str]:
    """raíz sin tildes de cada forma aprobada de un término («a / b»)."""
    return [plain(stem(form)) for form in forms.split(" / ")]


def compile_terms(glossary: list[dict]) -> list[Term]:
    """solo obligan los términos ya decididos; los propuestos y pendientes aún no."""
    rows = [row for row in glossary if row["estado"] in ENFORCED]
    return [(r["en"], term_pattern(r["en"]), stems(r["es"])) for r in rows]


def missing_terms(en: str, es: str, terms: list[Term]) -> list[str]:
    """términos del glosario presentes en el original cuya forma aprobada falta."""
    lowered = plain(es)
    found = (t for t in terms if t[1].search(en))
    return [term for term, _pattern, stems in found if not any(s in lowered for s in stems)]


def same_tags(en: str, es: str) -> bool:
    return sorted(TAG.findall(en)) == sorted(TAG.findall(es))


def same_newlines(en: str, es: str) -> bool:
    return NEWLINE.findall(en) == NEWLINE.findall(es)


def edges(text: str) -> tuple[str, str]:
    """espacios y saltos del principio y del final, sin contar los caracteres invisibles."""
    text = text.replace(INVISIBLE, "")
    return text[: len(text) - len(text.lstrip())], text[len(text.rstrip()) :]


def clean_spacing(en: str, es: str) -> bool:
    """sin caracteres invisibles ni dobles espacios nuevos, y con los mismos bordes."""
    doubled = "  " in es and "  " not in en
    return INVISIBLE not in es and not doubled and edges(en) == edges(es)


def box_lines(text: str) -> int:
    """líneas que ocupa un texto en el cuadro de diálogo; las etiquetas no ocupan sitio."""
    return len(textwrap.wrap(TAG.sub("", text), BOX_WIDTH))


def fits_box(en: str, es: str) -> bool:
    """lo que pasa de la última línea del cuadro no se ve.

    si el original ya se pasa, basta con no ocupar más líneas que él.
    """
    return box_lines(es) <= max(BOX_LINES, box_lines(en))


def option_width(text: str) -> float:
    """ancho aproximado de una opción; las etiquetas no ocupan sitio."""
    shown = TAG.sub("", text).strip()
    return sum(CAPITAL if char.isupper() else 1 for char in shown)


def fits_option(en: str, es: str) -> bool:
    """una opción que se parte en dos líneas pisa la siguiente.

    si el original ya es más ancho, basta con no pasarse de él.
    """
    return option_width(es) <= max(OPTION_WIDTH, option_width(en))


def fits_speaker(en: str, es: str) -> bool:
    """una etiqueta de hablante que se parte en dos líneas pisa el texto del diálogo.

    si el original ya es más largo, basta con no pasarse de él.
    """
    return len(es.strip()) <= max(SPEAKER_WIDTH, len(en.strip()))


def wrapped_lines(text: str, width: int) -> int:
    """líneas que ocupa un texto con ese ancho; un párrafo vacío ocupa una."""
    paragraphs = NEWLINE.split(TAG.sub("", text))
    return sum(max(1, len(textwrap.wrap(p, width))) for p in paragraphs)


def panel_lines(text: str) -> int:
    """líneas que ocupa un texto en un recuadro del mapa de influencia."""
    return wrapped_lines(text, PANEL_WIDTH)


def popup_lines(text: str) -> int:
    """líneas que ocupa el párrafo de un aviso emergente."""
    return wrapped_lines(text, POPUP_WIDTH)


def notebook_lines(text: str) -> int:
    """líneas que ocupa un texto en el cuaderno del laboratorio."""
    return wrapped_lines(text, NOTEBOOK_WIDTH)


def fits_notebook(en: str, es: str) -> bool:
    """caben las líneas del original o, si es más corto, las de una línea de efecto."""
    return notebook_lines(es) <= max(NOTEBOOK_LINES, notebook_lines(en))


def fits_popup(en: str, es: str) -> bool:
    """el párrafo de un aviso con leyenda no puede ocupar más líneas que el original."""
    return popup_lines(es) <= popup_lines(en)


def fits_panel(en: str, es: str) -> bool:
    """lo que pasa de la última línea del recuadro se sale por debajo.

    si el original ya se pasa, basta con no ocupar más líneas que él.
    """
    return panel_lines(es) <= max(PANEL_LINES, panel_lines(en))


def row_errors(row: dict) -> list[str]:
    """lo que se puede comprobar sin el original."""
    errors = []
    if not ID.fullmatch(str(row.get("id"))):
        errors.append("id mal formado")
    if not isinstance(row.get("es"), str) or not row["es"].strip():
        errors.append("traducción vacía")
    return errors


def file_errors(rows: list[dict]) -> list[str]:
    ids = [row.get("id") for row in rows]
    repeated = sorted({i for i in ids if ids.count(i) > 1})
    errors = [f"{i}: id repetido" for i in repeated]
    return errors + [f"{row.get('id')}: {e}" for row in rows for e in row_errors(row)]


def space_errors(en: str, es: str, kind: str) -> list[str]:
    """lo que no cabe donde se muestra; kind dice dónde: una línea, una opción, un aviso…"""
    if kind == "panel" and not fits_panel(en, es):
        return [f"no cabe en el recuadro del mapa: ocupa {panel_lines(es)} líneas"]
    if kind == "cuaderno" and not fits_notebook(en, es):
        lines = f"ocupa {notebook_lines(es)} líneas y el original {notebook_lines(en)}"
        return [f"no cabe en el cuaderno del laboratorio: {lines}"]
    if kind == "aviso" and not fits_popup(en, es):
        lines = f"ocupa {popup_lines(es)} líneas y el original {popup_lines(en)}"
        return [f"pisa la leyenda del aviso: {lines}"]
    if kind == "linea" and not fits_box(en, es):
        return [f"no cabe en el cuadro de diálogo: ocupa {box_lines(es)} líneas"]
    if kind == "opcion" and not fits_option(en, es):
        return [f"no cabe en una línea de opción: ancho {option_width(es):.0f}"]
    if kind == "hablante" and not fits_speaker(en, es):
        return [f"no cabe en la etiqueta de hablante: {len(es.strip())} caracteres"]
    return []


def pair_errors(en: str, row: dict, terms: list[Term], kind: str = "") -> list[str]:
    """compara una traducción con su original; kind dice dónde se muestra la cadena."""
    es, errors = row["es"], []
    if not same_tags(en, es):
        errors.append("etiquetas distintas del original")
    if not same_newlines(en, es):
        errors.append("saltos de línea distintos del original")
    if not clean_spacing(en, es):
        errors.append("espacios distintos del original o caracteres invisibles")
    errors += space_errors(en, es, kind)
    missing = set(missing_terms(en, es, terms)) - set(row.get("sin_glosario", []))
    return errors + [f"falta el término del glosario: {term}" for term in sorted(missing)]


def compare_errors(
    rows: list[dict],
    originals: dict[str, str],
    terms: list[Term],
    kinds: dict[str, str] | None = None,
) -> list[str]:
    """kinds: de cada id, si es línea u opción de una escena."""
    errors, kinds = [], kinds or {}
    for row in rows:
        en = originals.get(row["id"])
        if en is None:
            found = ["el id no existe en el original"]
        else:
            found = pair_errors(en, row, terms, kinds.get(row["id"], ""))
        errors += [f"{row['id']}: {e}" for e in found]
    return errors


def scene_kinds(rows: list[dict]) -> dict[str, str]:
    """las líneas van al cuadro de diálogo y las opciones a su lista; la interfaz no lleva tipo."""
    return {row["id"]: row["tipo"] for row in rows if row.get("tipo")}


def popup_kinds(rows: list[dict]) -> dict[str, str]:
    """párrafos de los avisos emergentes que llevan una leyenda debajo."""
    names = {row["id"]: str(row.get("objeto")) for row in rows}
    legends = {match[1] for match in map(LEGEND.match, names.values()) if match}
    paragraphs = {key: DESCRIPTION.match(name) for key, name in names.items()}
    return {key: "aviso" for key, match in paragraphs.items() if match and match[1] in legends}


def kinds_of(name: str, rows: list[dict]) -> dict[str, str]:
    """dónde se muestra cada cadena: hay archivos enteros de etiquetas o de recuadros."""
    if name in FILE_KINDS:
        return {row["id"]: FILE_KINDS[name] for row in rows}
    return popup_kinds(rows) | scene_kinds(rows)


def untranslated(originals: list[dict], translated: set[str]) -> list[dict]:
    return [row for row in originals if row["id"] not in translated]


def variant_group(name: str) -> str | None:
    """parte a la que pertenece una escena con variante h o hl; none si no tiene variante.

    las dos rutas de una parte no se emparejan por número: la hl puede ir desplazada.
    """
    match = VARIANT.fullmatch(Path(name).stem)
    return match[1] if match else None


def variant_errors(files: dict[str, list[dict]]) -> list[str]:
    """entre las variantes de una parte, mismo id (mismo original) pide misma traducción."""
    errors, seen = [], {}
    for name, rows in files.items():
        group = variant_group(name)
        for row in rows if group else []:
            first, es = seen.setdefault((group, row.get("id")), (name, row.get("es")))
            if es != row.get("es"):
                errors.append(f"{name}: {row.get('id')}: traducción distinta de la de {first}")
    return errors


def format_errors(folder: Path) -> list[str]:
    """errores de formato de todos los archivos; no necesita los originales."""
    loaded = {name: load_jsonl(path) for name, path in jsonl_files(folder).items()}
    errors = [f"{name}: {e}" for name, rows in loaded.items() for e in file_errors(rows)]
    return errors + variant_errors(loaded)


def content_errors(folder: Path, originals: Path, terms: list[Term]) -> list[str]:
    """errores frente al texto original, que solo existe en local."""
    errors, sources = [], jsonl_files(originals)
    for name, path in jsonl_files(folder).items():
        if name not in sources:
            errors.append(f"{name}: no corresponde a ningún archivo del juego")
            continue
        source = load_jsonl(sources[name])
        texts = {row["id"]: row["en"] for row in source}
        well_formed = [row for row in load_jsonl(path) if not row_errors(row)]
        found = compare_errors(well_formed, texts, terms, kinds_of(name, source))
        errors += [f"{name}: {e}" for e in found]
    return errors


def pending(folder: Path, originals: Path) -> dict[str, list[dict]]:
    """cadenas sin traducir de cada archivo del juego."""
    done = jsonl_files(folder)
    result = {}
    for name, path in jsonl_files(originals).items():
        ids = {row.get("id") for row in load_jsonl(done[name])} if name in done else set()
        result[name] = untranslated(load_jsonl(path), ids)
    return result


def main(args: list[str]) -> None:
    glossary = load_glossary(GLOSSARY)
    errors = glossary_errors(glossary) + format_errors(TRANSLATION)
    errors += content_errors(TRANSLATION, ORIGINALS, compile_terms(glossary))
    todo = pending(TRANSLATION, ORIGINALS)
    for name in args:
        print("\n".join(f"{name}: {row['id']}: {row['en']!r}" for row in todo.get(name, [])))
    print("\n".join(errors))
    left = sum(len(rows) for rows in todo.values())
    print(f"{len(errors)} errores; {left} cadenas sin traducir en {len(todo)} archivos")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
