"""comprobaciones sobre los datos de traduccion/ y listado de cadenas sin traducir."""

import csv
import re
import sys
from pathlib import Path

from tools.rutas import GLOSSARY, ORIGINALS, TRANSLATION
from tools.traducciones import jsonl_files, load_jsonl

TAG = re.compile(r"<[^<>]+>")
NEWLINE = re.compile(r"\r\n|\n")
ID = re.compile(r"[0-9a-f]{12}")
COLUMNS = ["en", "es", "categoria", "estado", "notas"]
STATES = {"oficial", "aprobado", "propuesto", "pendiente"}
ENFORCED = {"oficial", "aprobado"}
INVISIBLE = "​"

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


def compile_terms(glossary: list[dict]) -> list[Term]:
    """solo obligan los términos ya decididos; los propuestos y pendientes aún no."""
    rows = [row for row in glossary if row["estado"] in ENFORCED]
    return [(r["en"], term_pattern(r["en"]), [stem(f) for f in r["es"].split(" / ")]) for r in rows]


def missing_terms(en: str, es: str, terms: list[Term]) -> list[str]:
    """términos del glosario presentes en el original cuya forma aprobada falta."""
    lowered = es.lower()
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


def pair_errors(en: str, row: dict, terms: list[Term]) -> list[str]:
    """compara una traducción con su original."""
    es, errors = row["es"], []
    if not same_tags(en, es):
        errors.append("etiquetas distintas del original")
    if not same_newlines(en, es):
        errors.append("saltos de línea distintos del original")
    if not clean_spacing(en, es):
        errors.append("espacios distintos del original o caracteres invisibles")
    missing = set(missing_terms(en, es, terms)) - set(row.get("sin_glosario", []))
    return errors + [f"falta el término del glosario: {term}" for term in sorted(missing)]


def compare_errors(rows: list[dict], originals: dict[str, str], terms: list[Term]) -> list[str]:
    errors = []
    for row in rows:
        en = originals.get(row["id"])
        found = ["el id no existe en el original"] if en is None else pair_errors(en, row, terms)
        errors += [f"{row['id']}: {e}" for e in found]
    return errors


def untranslated(originals: list[dict], translated: set[str]) -> list[dict]:
    return [row for row in originals if row["id"] not in translated]


def format_errors(folder: Path) -> list[str]:
    """errores de formato de todos los archivos; no necesita los originales."""
    files = jsonl_files(folder).items()
    return [f"{name}: {e}" for name, path in files for e in file_errors(load_jsonl(path))]


def content_errors(folder: Path, originals: Path, terms: list[Term]) -> list[str]:
    """errores frente al texto original, que solo existe en local."""
    errors, sources = [], jsonl_files(originals)
    for name, path in jsonl_files(folder).items():
        if name not in sources:
            errors.append(f"{name}: no corresponde a ningún archivo del juego")
            continue
        texts = {row["id"]: row["en"] for row in load_jsonl(sources[name])}
        well_formed = [row for row in load_jsonl(path) if not row_errors(row)]
        errors += [f"{name}: {e}" for e in compare_errors(well_formed, texts, terms)]
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
