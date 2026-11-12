# Vampire: The Masquerade - Oaths & Ashes — Traducción al español

Mod no oficial de traducción al español del videojuego *Vampire: The Masquerade - Oaths & Ashes*.

## Estado

Las herramientas para extraer el texto del juego, aplicar la traducción y validarla están
hechas. La traducción todavía no ha empezado y no hay una versión instalable.

## Estructura del repositorio

- `traduccion/` — glosario y textos traducidos (`escenas/` e `interfaz/`).
- `tools/` — herramientas en Python para extraer, construir y validar.
- `tests/` — tests de las herramientas y de los datos de la traducción.
- `docs/` — documentación para jugadores.

## Para quien quiera colaborar

Hace falta una copia del juego y Python 3.12. El repositorio se clona dentro de la carpeta de
instalación del juego.

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m tools.extraer     # texto original a originales/ (solo local)
.venv/Scripts/python.exe -m tools.construir   # aplica traduccion/ a los archivos del juego
.venv/Scripts/python.exe -m tools.validar     # errores y cadenas sin traducir
.venv/Scripts/python.exe -m pytest
```

`tools.construir --restaurar` devuelve el juego a su estado original. Antes de modificar nada,
las herramientas guardan una copia de cada archivo original en `respaldo/` y comprueban su hash.

Si el juego recibe un parche, las herramientas lo detectan y se niegan a actuar hasta que se
renueve la copia con `tools.respaldo`.

## Aviso legal

Este es un proyecto de fans sin ánimo de lucro, sin relación con los desarrolladores ni con los
titulares de los derechos del juego. El repositorio no contiene archivos originales del juego:
necesitas una copia legítima para usar el mod.
