# CLAUDE.md

Mod no oficial de traducción al español de España de *Vampire: The Masquerade - Oaths & Ashes*
(versión final del juego, solo en inglés). Repo público: `JGreywarden/vtm-oaths-and-ashes-es`.

Idioma de trabajo: español. Responde al usuario siempre en español.

## Reglas que no se rompen

- El repo vive **dentro de la carpeta de instalación del juego**. El `.gitignore` ignora todo
  salvo lo listado. Nunca subas archivos del juego, texto original en inglés ni los manuales.
- Los archivos del juego solo se modifican con el comando de construcción, nunca a mano.
  Antes de tocarlos: comprobar que el juego no está abierto y que existe copia en `respaldo/`.
- `respaldo/` contiene los originales verificados por hash. No se borra ni se sobrescribe.
  Única excepción: renovarlo tras un parche del juego con `tools.respaldo`, y solo cuando el
  usuario lo pida (ver «Tras un parche del juego»).
- Los tests nunca escriben en la carpeta del juego: construyen en una carpeta temporal.
- Commit y push solo cuando el usuario lo pida. Mensajes de commit en español.
- Ninguna dependencia nueva sin que una necesidad real la justifique.

## Stack

- Python 3.12 en `.venv` (`requirements.txt` con versiones fijadas).
- UnityPy 1.25.4 para leer y escribir los archivos de Unity.
- pytest para tests y ruff para formato y estilo (config en `pyproject.toml`).
- GitHub Actions: ruff + pytest en cada push.
- Distribución (más adelante): instalador `.exe` con PyInstaller en GitHub Releases. No se
  instala ni se construye hasta que haya una versión que publicar.

## Estructura

```
CLAUDE.md  README.md  requirements.txt  pyproject.toml
traduccion/
  glosario.csv          términos: en, es, categoria, estado, notas
  personajes.csv        género y tratamiento de cada personaje (crear al empezar a traducir)
  escenas/              un .jsonl por escena (DTA0-P1-1.jsonl…)
  interfaz/             un .jsonl por tipo de texto: hablantes, requisitos, diario,
                        misiones, alquimia, influencia y textos
tools/                  código python y hashes.json (versión del juego y sha-256 de
                        sus originales)
tests/                  tests de pytest
docs/                   documentación para jugadores

# solo en local, ignorado por git
.venv/  respaldo/  originales/  prueba/  manuales_referencia/  .construido.json
```

## Arquitectura

Tres pasos, cada uno un módulo pequeño de `tools/`:

1. **extraer** (`tools/extraer.py`): `respaldo/` → `originales/` (texto en inglés, solo local),
   con la misma estructura de carpetas que `traduccion/`. Cada fila lleva `id`, `en` y contexto
   (`tipo` y `hablante` en las escenas, `objeto` en la interfaz).
2. **traducir**: se editan los `.jsonl` de `traduccion/`.
3. **construir** (`tools/construir.py`): `respaldo/` + `traduccion/` → archivos parcheados en
   la carpeta del juego. Antes comprueba que el juego no está abierto, que la versión
   instalada es la del respaldo y que cada respaldo coincide con `tools/hashes.json`; si
   falta un respaldo, lo crea desde el original.
4. **validar** (`tools/validar.py`): errores de los datos y recuento de cadenas sin traducir.

Módulos de apoyo: `cadenas` (cadenas serializadas e `id`), `esquemas` (formato de cada clase
con texto, solo datos), `lector` (lee un objeto con su esquema y sustituye textos), `juego`
(borde con UnityPy), `respaldo` y `traducciones` (lectura de `.jsonl` y reparto por archivo).

Formato de traducción, una cadena por línea:

```json
{"id": "3f9a1c2b7d40", "es": "Texto traducido."}
```

- `id` = primeros 12 caracteres hexadecimales del SHA-1 del texto original en UTF-8.
- El `id` vale dentro de su archivo: una frase repetida en la misma escena se traduce una vez.
- Las líneas y opciones de una escena van en `escenas/<escena>.jsonl`. Las etiquetas de
  hablante de todas las escenas van juntas en `interfaz/hablantes.jsonl`, y los textos de
  opción bloqueada en `interfaz/requisitos.jsonl`.
- Una cadena del juego sin `id` en su archivo está sin traducir. Si un texto no debe cambiar
  (un nombre, un número), se pone en `es` igual que el original.
- Campo opcional `"sin_glosario": ["stake"]`: términos del glosario que en esa frase no
  tienen su sentido de ambientación («the stakes are high»).
- Construir parte siempre de `respaldo/`, nunca de un archivo ya parcheado. Un archivo al que
  no le toca ninguna traducción se copia tal cual, así que sin traducciones el juego queda
  idéntico al original.

```bash
.venv/Scripts/python.exe -m tools.extraer
.venv/Scripts/python.exe -m tools.construir              # aplica traduccion/
.venv/Scripts/python.exe -m tools.construir prueba       # aplica otra carpeta (pruebas)
.venv/Scripts/python.exe -m tools.construir --restaurar  # devuelve los originales al juego
.venv/Scripts/python.exe -m tools.validar                # errores y cadenas pendientes
.venv/Scripts/python.exe -m tools.validar escenas/DTA0-P1-1.jsonl  # lista las pendientes
.venv/Scripts/python.exe -m tools.respaldo               # renueva respaldo/ tras un parche
```

### Tras un parche del juego

Steam reescribe los archivos que cambian y deja el respaldo desfasado. `tools/hashes.json`
guarda el `buildid` de Steam al que pertenece el respaldo; si el instalado es otro, `extraer`
y `construir` (también `--restaurar`) se niegan a actuar, porque mezclarían dos versiones.

1. Con el juego cerrado y el visto bueno del usuario, `python -m tools.respaldo`: sustituye
   `respaldo/` por los archivos instalados y regenera `tools/hashes.json`.
2. Si avisa de que algún archivo sigue parcheado por el mod (Steam solo repone lo que
   cambia; lo sabe por `.construido.json`), el usuario verifica la integridad de los
   archivos en Steam y se repite el paso 1.
3. `tools.extraer` y `pytest`: si un formato ha cambiado, falla el test de esquemas.
4. `tools.validar` dice qué traducciones han quedado huérfanas («el id no existe en el
   original») y qué cadenas nuevas hay pendientes. Después, `tools.construir`.

### Datos técnicos del juego (verificados)

- Unity 6000.3.17f1, IL2CPP, sin árboles de tipos: los `MonoBehaviour` se tratan como bytes.
- Versión de referencia: `buildid` 26625395 de Steam (parche del 12-11-2026). El parche
  cambió unas 200 cadenas y partió `DTA1-P2-3` en `DTA1-P2-3A` y `DTA1-P2-3B`; todos los
  esquemas siguieron valiendo.
- Cadena serializada: longitud `int32` little-endian + UTF-8 + relleno con ceros hasta
  múltiplo de 4.
- Lectura y escritura: `obj.get_raw_data()`, `obj.set_raw_data()`, `serialized_file.save()`.
- El nombre del objeto es la cadena que empieza en el byte 28 de sus datos. En los bytes 16 a
  28 está el puntero a su script; el nombre de la clase se lee de los `MonoScript` de
  `globalgamemanagers.assets`.
- **El texto visible se localiza por esquema, no por heurística.** `tools/esquemas.py`
  describe campo a campo cada clase con texto y el lector exige consumir el objeto exacto.
  La sustitución es por posición: una línea igual a un identificador no se confunde con él.
- Escena (`DialogueTreeSO`): lista de nodos; cada nodo tiene líneas y opciones.
  - Línea: número, hablante, texto, dos claves de retrato (`THOMASGREY`), dos claves de fondo
    (`OPERABALCONY`), música y eventos.
  - Opción: texto, nodo de destino, texto de opción bloqueada, condiciones y eventos (aquí
    están las variables, los nombres de tipos de C# y los métodos).
  - El hablante es la etiqueta que se muestra (`MADAME KIEZ`, `THE LIVING ARCHIVE`), distinta
    de la clave de retrato (`MADAMEKIEZ`). Se traduce.
  - El texto de opción bloqueada mezcla mensajes (`Hunger too high`) con notas de desarrollo
    (`Alice got map`); está por confirmar jugando si se ve en pantalla.
  - Etiquetas presentes: solo `<i>` y `<b>`. Las escenas no tienen saltos de línea. Hay 15
    líneas con espacios de ancho cero y 2 hablantes con espacios duros: son restos de edición
    y no se reproducen en la traducción.
- Las 295 escenas están en `resources.assets`:
  - 166 de los actos, `DTA{acto}-P{parte}-{escena}` (actos 0 a 3: 10, 62, 72 y 22 escenas).
  - 5 finales: `DTENDINGNEUTRALA`/`B`, `DTENDINGPOSITIVE1`/`2` y `DTENDNEGATIVE`.
  - 20 de alimentación: `DTA-FEEDING*` son de Alice y `DTL-FEEDING*` de Lenz (10 y 10).
  - 104 de juego político: `DTA1-PL*` (32), `DTA2-PL*` (16), `DTA2-PLOTPL*` (41) y
    `PL-FINAL*` (15). Las 89 primeras tienen una sola línea y de una a tres opciones.
- Sufijos `H` y `HL`: `H` es la variante con Alice con mano y `HL` con Alice sin mano
  («hand lost»). Dependen de la variable `AliceLostHand` y las `HL` usan los retratos
  `ALICEHANDLESS`. Unas parejas tienen el texto casi idéntico y otras son rutas distintas
  (en la parte 5 del acto 1, la ruta `HL` tiene una escena más).
- Interfaz: diario (`JournalSubCategory`, `JournalMainCategory`), misiones
  (`MainStoryMissionData`, `PoliticalPlayMissionData`), fórmulas (`FormulaDefinitionSO`),
  distritos y bandas (`DistrictInfo`, `GangInfo`) y textos sueltos (`TextMeshProUGUI`).
- Archivos con texto (todos con respaldo y hash): `resources.assets`, `sharedassets1.assets`,
  `sharedassets3.assets` y `level1` a `level14` (`level8` son los créditos).
- No se traducen: los `UI.Text` (panel de depuración de Unity) ni los logros (en los archivos
  solo hay identificadores; el nombre y la descripción están en Steam).
- Las fuentes del juego muestran bien `¿ ¡ ñ Ñ ü á é í ó ú « » — …` (comprobado en el juego).
- Comprobado en el juego con una traducción de prueba (12-11-2026): se ven la línea, el texto
  de opción y la etiqueta de hablante traducidos, y cambiar la etiqueta no afecta al retrato
  ni al avance del diálogo.
- El juego muestra en versalitas los botones y las etiquetas de hablante. Los botones de los
  avisos emergentes son estrechos: «Confirmar (prueba)» se partió en dos líneas. Conviene
  que esos textos sean tan cortos como el original.
- Hay texto visible incrustado en el código, fuera de los archivos que tratan las
  herramientas: el aviso superior «MASQUERADE SYSTEM UPDATED!» une el título del diario con
  un literal ` UPDATED!` de `il2cpp_data/Metadata/global-metadata.dat`. Pendiente de
  inventariar y resolver en la fase 3.
- El archivo reescrito pesa algo menos que el original; el juego lo carga sin problemas.
- Volumen: 25.339 cadenas y 394.000 palabras en las escenas; 1.472 cadenas y 52.000 palabras
  en la interfaz (de ellas, 548 cadenas del diario).

## Código

- KISS, DRY, YAGNI. Lo más simple que funcione; nada «por si acaso».
- Funciones pequeñas (unas 20 líneas como máximo), una sola responsabilidad.
- Funciones puras siempre que se pueda; la lectura y escritura de archivos va en los bordes.
- Identificadores en inglés. Comentarios y docstrings en español y **en minúsculas**.
- Comenta el porqué, no el qué.
- Cada función tiene su test. Se escribe el test junto con la función, no después.
- Una única fuente de verdad por dato: el glosario para términos, los `.jsonl` para textos.

## Tests

- No se hace commit con tests en rojo ni con avisos de ruff.
- Los tests que necesitan archivos del juego se marcan `@pytest.mark.game` y se saltan solos
  si el juego no está (en GitHub Actions no hay copia del juego).
- `tests/test_juego_real.py` comprueba sobre el juego real que todos los objetos encajan en
  su esquema: si una actualización cambia un formato, falla ahí.
- Además del código se validan los datos de `traduccion/` (`tests/test_datos.py`):
  - etiquetas (`<i>`, `<b>`…) y saltos de línea iguales que en el original;
  - mismos espacios al principio y al final, sin dobles espacios ni caracteres invisibles;
  - ninguna traducción vacía, ningún `id` repetido, mal formado o que no exista en el juego;
  - si el original contiene un término del glosario (`oficial` o `aprobado`), la traducción
    usa su forma aprobada, salvo excepción declarada con `sin_glosario`;
  - el glosario no tiene filas duplicadas ni mal formadas.
- Las comprobaciones que comparan con el original necesitan `originales/` y solo se ejecutan
  en local; en GitHub Actions se comprueban el formato de los `.jsonl` y el glosario.

```bash
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format .
```

## Traducción

### Criterios generales

- Español de España. Traducción **fiel**: no se suaviza el lenguaje malsonante ni la violencia,
  y no se añade ni se quita contenido.
- Se conservan exactamente las etiquetas, los saltos de línea (`\n`, `\r\n`) y cualquier
  variable. Solo cambia el texto visible.
- Hay dos narradores en primera persona: Alice (mujer) y Lenz (hombre). Cuidar la
  concordancia de género en cada escena.
- Tratamiento (tú/usted) según `personajes.csv`; no se cambia a mitad de una relación sin
  motivo en el original.
- Ortotipografía española: `¿` y `¡` de apertura, comillas angulares `« »` (dentro de ellas,
  `“ ”`), raya `—` pegada al inciso, y `…` como un solo carácter.

### Glosario

- `traduccion/glosario.csv` manda. Antes de traducir un término de ambientación, se consulta.
- Estados: `oficial` (atestiguado en los manuales en español), `aprobado` (decidido por el
  usuario), `propuesto` (propuesta sin validar), `pendiente` (falta decisión del usuario).
- Un término nuevo entra primero en el glosario como `propuesto` o `pendiente`, se pregunta
  al usuario y solo después se usa.
- Si un término aparece en los manuales, gana la forma del manual sobre cualquier preferencia.
- Para buscar un término: `manuales_referencia/txt/en/` y `manuales_referencia/txt/es/`.
  Solo se toman los términos; nunca se copian pasajes de los manuales al repo.

### Mayúsculas

Se usan **las palabras del manual con las mayúsculas del juego**: si el original escribe el
término en minúscula, la traducción también.

- Mayúscula: Vástago, Crepuscular, Abrazo, Beso, Bestia, Ansia, Mascarada, Tradiciones,
  Disciplinas, Camarilla, Anarquista, Vínculo de Sangre, Elíseo, Capilla y todos los cargos
  (Príncipe, Barón, Justicar, Arconte, Regente, Sheriff, Azote).
- Minúscula: sire, chiquillo, ghoul, sangre débil, refugio, dominio, ganado, recipiente,
  letargo, diablerie, vitae, no-vida, no-muerto, muerte definitiva, secta, coterie, antiguo.
- `Clan` va en mayúscula solo junto al nombre (Clan Ventrue). `Sangre` va en mayúscula solo
  cuando el original la lleva.

### Nombres propios

- Se traducen facciones, objetos y lugares descriptivos: Rosa Negra, Loto Rojo, Caza Salvaje,
  Mandato Rojo, Mercado Nocturno, Archivo Viviente.
- Se traducen los **apodos** de personas (Crow → Cuervo, sus Corvatos); se conservan los
  nombres y apellidos reales.
- No se traducen los nombres de locales (Bacchanalia, Tantalos, Namenslos) ni los topónimos
  de Berlín que no tengan forma española asentada.
- Ante un apodo o nombre nuevo dudoso, se pregunta al usuario.

## Flujo de trabajo

1. Se traduce por **bloques de escenas** seguidas, para que el usuario pueda jugar con fluidez.
2. Al terminar un bloque: tests en verde, construir y avisar al usuario.
3. El usuario revisa jugando y comunica correcciones; se aplican antes del bloque siguiente.
4. Las dudas de traducción se agrupan y se preguntan juntas, no una a una.
5. Las imágenes con texto incrustado se valoran caso por caso con el usuario.

## Fases

Cada fase se cierra solo cuando se cumple su criterio. La historia se traduce en orden de
juego y el bloque de revisión natural es la «parte» (`P{n}`) de cada acto.

0. **Preparación** (cerrada): repo, glosario, prueba técnica en el juego y este documento.
1. **Herramientas** (cerrada): `requirements.txt`, `pyproject.toml`, GitHub Actions y los módulos
   extraer, construir y validar con sus tests. *Cierre:* sin traducciones, construir deja el
   juego igual; con una, se ve en el juego; tests en verde.
2. **Piloto, el prólogo**: acto 0, parte 1 (4 escenas) y `personajes.csv`. *Cierre:* el
   usuario lo juega y aprueba el estilo (tono, tú/usted, palabrotas, ortotipografía).
3. **Interfaz y sistemas**: menús, opciones, tutoriales, diario, fichas de personaje,
   misiones y escenas de alimentación. *Cierre:* todo lo que no es historia, revisado.
4. **Acto 0 (resto) y acto 1**: 6 + 62 escenas. *Cierre:* cada bloque jugado y revisado.
5. **Acto 2**: 72 escenas en 13 partes. *Cierre:* igual.
6. **Acto 3 y finales**: 22 escenas y 4 finales. *Cierre:* el juego se completa en español.
7. **Revisión global**: coherencia de todo el texto, imágenes con texto incrustado y
   correcciones acumuladas. *Cierre:* ninguna cadena sin traducir ni aviso de validación.
8. **Publicación**: instalador `.exe`, instrucciones en el README y versión 1.0 en GitHub
   Releases. *Cierre:* alguien sin Python instala y desinstala el mod.

Peso aproximado del texto: acto 0, 8 %; acto 1, 37 %; acto 2, 35 %; acto 3, 20 %.

**Fase actual: 2, sin empezar.** Al cerrar una fase, se actualiza esta línea.
