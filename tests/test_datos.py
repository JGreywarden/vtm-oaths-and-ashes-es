"""validación de los datos de traduccion/, además de la del código."""

import pytest

from tools.rutas import GLOSSARY, ORIGINALS, TRANSLATION
from tools.validar import (
    compile_terms,
    content_errors,
    format_errors,
    glossary_errors,
    load_glossary,
)


def test_glossary_is_well_formed():
    assert glossary_errors(load_glossary(GLOSSARY)) == []


def test_translation_files_are_well_formed():
    assert format_errors(TRANSLATION) == []


@pytest.mark.game
def test_translations_match_the_originals():
    """etiquetas, saltos de línea, espacios y glosario; necesita originales/, que es local."""
    if not ORIGINALS.exists():
        pytest.skip("falta originales/: ejecuta python -m tools.extraer")
    terms = compile_terms(load_glossary(GLOSSARY))
    assert content_errors(TRANSLATION, ORIGINALS, terms) == []
