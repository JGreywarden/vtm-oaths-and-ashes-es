"""rutas del proyecto; el repo vive dentro de la carpeta de instalación del juego."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Vampire the Masquerade Oaths & Ashes_Data"
BACKUP = ROOT / "respaldo"
ORIGINALS = ROOT / "originales"
TRANSLATION = ROOT / "traduccion"
GLOSSARY = TRANSLATION / "glosario.csv"
HASHES = Path(__file__).with_name("hashes.json")
GAME_EXE = "Vampire the Masquerade Oaths & Ashes.exe"
# steam apunta aquí la versión instalada; está en steamapps/, dos carpetas por encima
MANIFEST = ROOT.parent.parent / "appmanifest_4191110.acf"
# hash de los archivos que escribió la última construcción (solo local)
BUILT = ROOT / ".construido.json"
