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
  personajes.csv        género, quién es y tratamiento de cada personaje
  escenas/              un .jsonl por escena (DTA0-P1-1.jsonl…)
  interfaz/             un .jsonl por tipo de texto: hablantes, requisitos, diario,
                        misiones, alquimia, influencia, textos y codigo
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
(borde con UnityPy), `literales` (textos del código, en `global-metadata.dat`), `respaldo` y
`traducciones` (lectura de `.jsonl` y reparto por archivo).

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
3. `tools.extraer` y `pytest`: si un formato ha cambiado, falla el test de esquemas; si
   cambia el formato del metadato o desaparece un literal de la lista cerrada, fallan los
   tests de literales.
4. `tools.validar` dice qué traducciones han quedado huérfanas («el id no existe en el
   original») y qué cadenas nuevas hay pendientes. Después, `tools.construir`.

### Datos técnicos del juego (verificados)

- Unity 6000.3.17f1, IL2CPP, sin árboles de tipos: los `MonoBehaviour` se tratan como bytes.
- Versión de referencia: `buildid` 26726684 de Steam (parche del 17-11-2026, sin notas).
  Cambió 57 cadenas por 61 nuevas en 23 archivos: 14 líneas de 9 escenas ya traducidas de
  los actos 0 y 1 (entre ellas, la mano que pierde Alice pasa a ser la izquierda), textos
  de 12 escenas sin traducir de los actos 2 y 3, y 12 textos de misión del acto 1, que
  ahora llevan delante «PRESENT: ALICE» o «EARLIER: LENZ'S ACCOUNT»; añadió un aviso
  emergente (`FinalAct2FeedingWarning`). No cambió ningún literal de la lista `VISIBLE`.
  Parches anteriores: 26698024 (16-11-2026) cambió 40 cadenas por 43 nuevas (opciones del
  prólogo y de la parte 3 del acto 1, 11 escenas sin traducir y 6 textos de misiones),
  quitó el nombre de líder añadido a la banda Zahir-Kara y cambió el literal «Older
  autosave {0}» por «Other autosave {0}»; 26674484 (15-11-2026)
  retocó textos de los actos 1 y 2, cambió la opción «Low-quality Textures» por
  «High-quality Textures» y añadió el historial de autoguardado; 26657688 (14-11-2026)
  reescribió parte del acto 1 (unas 180 cadenas nuevas en 22 escenas), eliminó `DTA1-P0-3`,
  añadió a 22 misiones el aviso «this mission ends the night» y una opción de menú;
  26625395 (12-11-2026) partió `DTA1-P2-3` en `DTA1-P2-3A` y `DTA1-P2-3B`. En los cinco
  casos Steam repuso todos los archivos con texto y todos los esquemas siguieron valiendo.
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
- Las 294 escenas están en `resources.assets`:
  - 165 de los actos, `DTA{acto}-P{parte}-{escena}` (actos 0 a 3: 10, 61, 72 y 22 escenas).
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
  `sharedassets3.assets`, `level1` a `level14` (`level8` son los créditos) y
  `il2cpp_data/Metadata/global-metadata.dat` (el respaldo conserva esa ruta).
- No se traducen: los `UI.Text` (panel de depuración de Unity) ni los logros (en los archivos
  solo hay identificadores; el nombre y la descripción están en Steam).
- Las fuentes del juego muestran bien `¿ ¡ ñ Ñ ü á é í ó ú « » — …` (comprobado en el juego).
- Comprobado en el juego con una traducción de prueba (12-11-2026): se ven la línea, el texto
  de opción y la etiqueta de hablante traducidos, y cambiar la etiqueta no afecta al retrato
  ni al avance del diálogo.
- El juego muestra en versalitas los botones y las etiquetas de hablante. Los botones de los
  avisos emergentes son estrechos: «Confirmar (prueba)» se partió en dos líneas. Conviene
  que esos textos sean tan cortos como el original.
- Hay texto visible incrustado en el código (`interfaz/codigo.jsonl`): son literales de
  `global-metadata.dat` (versión 39 de metadatos). En el byte 8 de la cabecera van posición,
  tamaño y número de la tabla de literales y de su bloque de datos; la tabla son `uint32` con
  la posición de cada literal en el bloque (el último es el final) y cada literal es UTF-8
  sin longitud ni terminador.
  - Para traducir se añade un bloque nuevo al final del archivo y se apunta la cabecera a
    él: ninguna otra sección se mueve y sin traducciones el archivo sale idéntico.
  - Un literal se comparte con todo el código (motor y librerías incluidos), así que solo se
    traducen los de la lista cerrada `VISIBLE` de `tools/literales.py`, guardada por `id`.
    Entra en ella un literal que solo usa el código del juego y que no es una clave.
  - Son claves y no se tocan: `Auto` (tipo de guardado, va a `metadata.json` de la partida),
    `Slot{0}` (carpeta de la partida), los nombres de las acciones del mando (`Submit`,
    `Cancel`, `Navigate`…) y los nombres de variables. El aviso «… UPDATED!» une el título
    del diario con un literal; lo mismo «<banda> Leader:» y «Slot <n>».
  - Quién usa un literal se averigua en `GameAssembly.dll`: cada literal tiene una casilla de
    8 bytes en `.data` con el valor `0xA0000001 + 2·índice`, y el código la lee con una
    dirección relativa; las funciones se delimitan con `.pdata`. El código propio del juego
    ocupa el principio de la sección `il2cpp`.
  - El juego enlaza solo los términos del diario dentro de los diálogos: busca el título de
    cada entrada (sin «The » ni «Clan » delante) con sufijos de plural ingleses.
- El archivo reescrito pesa algo menos que el original; el juego lo carga sin problemas.
- Volumen: 25.405 cadenas y 395.000 palabras en las escenas; 1.515 cadenas y 52.000 palabras
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
  - las líneas de escena caben en el cuadro de diálogo (cuatro líneas de 76 caracteres);
  - las opciones de escena caben en una línea (ancho 56, contando cada mayúscula como 1,4);
  - las etiquetas de hablante caben en una línea (22 caracteres);
  - los textos del mapa de influencia caben en su recuadro (13 líneas de 50 caracteres);
  - el párrafo de un aviso emergente con leyenda no ocupa más líneas que el original;
  - los textos del cuaderno del laboratorio no ocupan más líneas que el original (53
    caracteres por línea; una línea de efecto puede ocupar dos);
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

### Estilo aprobado en el piloto

Decisiones que el usuario aprobó jugando el prólogo; valen para todo el juego.

- Narración en presente, como el original. Pretérito perfecto para lo que acaba de ocurrir
  («me has interrumpido») y `vosotros` para el plural.
- Sin leísmo, laísmo ni loísmo: «capturarlo», «le rozo la sien».
- Las opciones que son acciones van en imperativo de tú («Mira el escenario.»); las que son
  frases dichas se traducen como diálogo.
- Los poderes de Disciplina entre corchetes van en mayúsculas, con el nombre del manual:
  `[COMPELER]`, `[MENTE OLVIDADIZA]`.
- Palabrotas con su fuerza: «prat» → «cretino», «bastard» → «cabrón», «Damn it» → «Maldita sea».
- Los Vástagos se tutean entre sí. Un mortal trata de usted a un desconocido; un Vástago tutea
  al mortal al que somete y lo trata de usted mientras finge ser uno de ellos.
- Los mensajes citados dentro de la narración van entre « ».
- Medidas imperiales, a métricas («half an inch» → «un centímetro»).
- Erratas del original: se traduce lo que quiso decir.
- Palabras que confunden fuera de contexto se evitan aunque sean correctas: «chandelier» es
  «lámpara de araña» la primera vez y «lámpara» después, nunca «araña» a secas.

### Estilo aprobado en la fase 3

Decisiones de la interfaz y los sistemas que el usuario aprobó; valen para todo el juego.

- Un personaje al que el original trata de «they» (Tuyet, Doctor Morgan) se traduce con
  redacción correcta sin marcas de género. Nunca «elle» ni desdobles.
- Interfaz: «Opciones» para Settings y Options, «Diario», «Misiones» (no «Registro de
  misiones», que no cabe en la pestaña) y «Ranura» para los perfiles de guardado.
- Botones cortos, como el original: NAVEGAR, ATRÁS, SIGUIENTE, ELEGIR, ACEPTAR, DESTILAR.
- Créditos: los cargos se traducen como áreas («Programación») y los nombres no se tocan.
- Fichas del diario: `<b>Nacimiento</b>`, `<b>Abrazo</b>`, `<b>Ghoul desde</b>`,
  `<b>Generación</b>: 10.ª`, `<b>Afiliación</b>: Anarquistas (…)`.
- Misiones: «Cacería:» (Alice), «Reposición:» (Lenz) y «Toma de X».
- Alimentación: Alice trata de usted mientras finge y tutea al dominar; Lenz tutea a todos.
  Las palabras alemanas y los títulos de canciones no se traducen.
- Un texto que el juego pega detrás de otro lleva una forma que no dependa del género ni
  del número de lo que tiene delante: «<título> — ACTUALIZACIÓN», «<banda> — Líder:».

Pendiente de comprobar jugando (si algo se ve mal, se corrige en su bloque):

- si los textos de opción bloqueada se ven en pantalla (`DTA1-P0-2`, `DTA1-P2-1`,
  `DTA1-P2-2`): 13 parecen mensajes y 26 notas de desarrollo;
- el género del título de acto «EL TESTIGO», la etiqueta «DE LENZ» del laboratorio y cómo
  suena «de por no-vida»;
- los narradores deducidos de tres misiones (Hacène en `A2-P14-1` y `A2-P16-1`, Lucinde
  en `A3-P5-1`) y dónde sale «Bajos fondos de Berlín»;
- literales del código que siguen en inglés por si son claves: los nombres de modo
  seguidos de « Mode on», «Choose », «End Mission» y el formato de fecha de la ranura;
- las etiquetas del historial de autoguardado, que entraron en la lista `VISIBLE` por su
  forma de etiqueta, sin comprobar su uso en `GameAssembly.dll`. «Otro autoguardado {0}» se
  ve bien en la pantalla de cargar partida (comprobado el 16-11-2026). Desde ese parche la
  lista la encabeza «Guardado actual» («Current save»), por comprobar; «Último
  autoguardado» ya no salió en esa pantalla. Falta confirmar que los autoguardados se
  siguen cargando.

### Estilo aprobado en la fase 4

Decisiones de la historia que el usuario aprobó antes de traducir; valen para todo el juego.

- Fórmulas de tratamiento: «Ms» y «Mrs» son «señora» («señora Lytelton»), «Mr» es «señor».
  «Lady Justicar Lucinde» es «la dama Justicar Lucinde».
- La jerarquía manda sobre el tuteo entre Vástagos: a Lucinde se la trata de usted (salvo
  Étienne) y ella tutea a todos. El servicio trata de usted a Alice; ella tutea al Conductor y
  al Archivo Viviente, y trata de usted al Conserje.
- La insolencia de un personaje va en lo que dice, no en saltarse el tratamiento.
- El francés, el alemán y otros idiomas del original se dejan como están; se traduce solo la
  glosa que el original pone detrás («<i>WIR BLUTEN GLEICH</i>. Sangramos igual.»).
- Las etiquetas entre corchetes que el original escribe en minúscula se traducen en
  minúscula: `[Mentira]`, `[Pelea]`, `[Media verdad]`.
- Los motes de clan llevan la forma del diario (Rata de Alcantarilla, Costra, Tirano).
- La pantalla de muerte «YOU ARE NO MORE...» es «YA NO EXISTES…» en todas las escenas.
- «bounty» es «botín», como en el prólogo; «intelligence» es «informes» o «información».
- Las variantes H y HL de una escena llevan la misma traducción donde el original es igual.
- El cuadro de diálogo muestra cuatro líneas de unos 76 caracteres y no desplaza el texto:
  lo que pasa de ahí no se ve (comprobado en el juego el 15-11-2026). Si la traducción fiel
  no cabe, se aprieta la redacción sin quitar contenido. `tools.validar` lo da como error
  («no cabe en el cuadro de diálogo»), salvo que el original ya ocupe esas mismas líneas.
- Una opción ocupa una sola línea y la siguiente se dibuja justo debajo: si se parte en
  dos, su segunda línea pisa la opción siguiente (comprobado en el juego el 16-11-2026).
  Cabe un ancho de unos 56 caracteres contando cada mayúscula como 1,4, así que una etiqueta
  de poder larga (`[MIRADA ATERRADORA]`) deja poco sitio al resto. `tools.validar` lo da
  como error («no cabe en una línea de opción»), salvo que el original ya sea igual de ancho.
- La etiqueta de hablante ocupa una sola línea encima del texto: si se parte en dos, su
  segunda línea pisa el diálogo (comprobado en el juego el 16-11-2026 con «MIEMBRO DE LOS
  ZAHIR-KARA»). Caben 22 caracteres, como la etiqueta más larga del original, así que se
  quita la preposición: «MIEMBRO ZAHIR-KARA», «LÍDER ZAHIR-KARA», «MENSAJERO ROSA NEGRA».
  `tools.validar` lo da como error («no cabe en la etiqueta de hablante»).
- Tratamiento en el acto 1: Ldescu, Sofia y la Viejecita del Mercado Nocturno, de usted (corte
  y edad); Heribert, Läuschen, Cuervo, Yaşar y la Caza Salvaje, de tú. A los mortales
  desconocidos de la calle Alice los trata de usted, y a un niño, de tú.
- El dicho de la Viejecita lleva la forma del manual: «Una Bestia soy para en Bestia no
  convertirme». Adrian llama a Alice «pelirroja» (Red).
- Cuando dos escenas comparten texto (las dos versiones del encuentro con Cuervo, las
  variantes H y HL), la segunda se ensambla reutilizando por `id` lo ya traducido.
- Tratamiento en la parte 3 del acto 1: Madame Kiez y Alice, de usted; las muñecas de sangre
  tratan de usted a Alice salvo Sangría, que la tutea; Alice las tutea a todas. Con Oraya, de
  usted mientras dura la farsa de la tirada de tarot y de tú desde que Alice habla claro.
- Tarot con los nombres españoles: Arcanos Mayores, El Ermitaño, Los Enamorados, La
  Emperatriz, La Torre, Rey de Espadas, Rey de Bastos, Dos de Oros; «reversed» es «invertido».
- Un libro o una película que el original cita por su título inglés lleva el título con que
  se publicó en España (<i>Cadáver exquisito</i>, <i>El hombre de mimbre</i>).
- En la narración, los turistas de las ruinas son «el borracho», «la streamer» y «el cámara».
- Fadwa y Alice se tutean. Antes de que Alice la vea, «Boss» en boca de sus hombres es «quien
  manda», para no adelantar que es una mujer (el original juega con esa sorpresa).
- Una errata del original que duplica una frase se traduce una sola vez.
- Un miembro del Loto Rojo es «un Loto» o «una Loto», como el original dice «a Lotus». Müller y
  Alice se tutean. «Tower preserve me» es «Que la Torre me ampare». La opción de la Bestia
  «ATTACK.» es «ATACA.».
- Parte 5 del acto 1: la ruta sin mano (HL) lleva dos escenas propias y luego va desplazada
  un número respecto a la ruta con mano (`02H` ≈ `03HL`, `03H` ≈ `04HL`, `04H` ≈ `05HL`,
  `05H` ≈ `06HL`). `tools.validar` exige la misma traducción para un mismo original entre
  las escenas H y HL de una misma parte.
- Tratamiento en la parte 5: Sofia y Alice siguen de usted; Shang trata de usted a Alice y
  ella pasa a tutearlo; Heribert y May, de tú; el Conductor, de usted a Alice. Vika y el
  portero del Namenslos tutean a Alice, y ella los trata de usted salvo cuando usa un poder.
- Tuyet aparece sin nombre en el Namenslos: «la otra persona», sin marcas de género.
- «Run-off» es «Última Ronda» (forma del manual, ya usada en el diario). «Crow's hideout»
  es «la guarida de Cuervo» y «haven», «refugio».
- Segundo encuentro con Cuervo (parte 5): sigue tuteando a Alice aunque la llame «señora
  Egerton» (su nombre de casada). «Keeper» a secas es «la Guardiana»; «Elder» con mayúscula
  en el original es «Antiguo». «Hmm.» se deja igual, distinto de sus «Mm.» y «Hm.».
- Poderes de la parte 6: `[MESMERISMO]` y `[ATEMORIZAR]`, con los nombres del manual.
- Casa de empeños (parte 6): la «torch» de la Caza Salvaje es «la linterna» (ultravioleta);
  «destroy» entre vampiros es «destruir». El «uh» con que Lenz titubea es «eh».
- Lenz narrador (partes 7 a 10): tutea a todo el mundo; frases cortas, tacos con toda su
  fuerza («joder», «me cago en todo», «puto») y jerga de droga: «chute» (fix, hit), «mono»
  (craving, withdrawal), «colocón» y «subidón» (high), «bajón» (crash), «tanda» (batch),
  «alijo» (stash), «piti» (cig), «potar». Sig es «el Camello» y Alice, «la Tirana
  pelirroja». La Caza Salvaje son «los skins» o «los nazis». «unlife» es «no-vida».
- Tratamiento con Lenz: de tú con Sig, Shang, Ida, Vika, May, Oraya y Läuschen. Madame
  Kiez lo trata de usted («Herr Lenz», sin traducir) y él la tutea.
- May en la narración de Lenz (`DTA1-P8-1`) va sin marcas de género, porque ahí el
  original usa «they»; y «your master», dicho de Tuyet, se resuelve sin «amo» ni «ama»
  («a quien sirve May», «Saluda a Tuyet de mi parte»).
- Fórmulas de alquimia en las opciones, con el nombre del glosario: `[PERDICIÓN DEL
  CARCELERO]`, `[ALCANCE LEJANO]`, `[MANDAGLOIRE]`, `[NEBLINA]`, `[IMITADOR]`, `[ELEVADA]`,
  `[ESPEJO DE CONFIANZA]`, `[DETENER LA ARENA QUE CAE]` y `[ENCHUFE]`. «El», la forma corta
  de Elevate, es «Ele» para que no se lea como artículo. `[RUMOR]` se deja igual y «the
  Den», el sótano del Bacchanalia, es «el Antro» (aprobados el 16-11-2026).
- Tarot de Oraya con Lenz: El Carro, La Muerte y El Loco; «upright» es «al derecho».
- Las onomatopeyas se adaptan: «ZAS», «CRAC», «Tilín, tilín», «chof, chof», «Ñam».
- Pantalla de máscaras: «Vía: Fuerza» y «Vía: Diplomacia» («Enfoque: Diplomacia» se partía en
  dos líneas). Sus franjas de color están en posiciones fijas, así que cada epígrafe ocupa
  las mismas líneas que el original (La Azote 4, 2, 4 y 3; La Guardiana 3, 4, 4 y 3, a unos
  62 caracteres por línea). Vale para cualquier panel con adornos fijos detrás del texto.
- Aviso del mapa de Berlín: el título cabe en una línea de unos 43 caracteres («ATA BERLÍN
  CON JURAMENTOS O HAZLA CENIZAS») y el icono de la luna de la fila de cacería va en
  posición fija, a unos 23 caracteres: «CACERÍA: CUESTA UNA FASE», con «fase» en vez de
  «fase de la noche» y la excepción declarada con `sin_glosario`.
- Avisos emergentes con leyenda (alquimia, adicción, Ansia y Bestia…): la leyenda va en
  posición fija debajo del párrafo, así que el párrafo no puede ocupar más líneas que el
  original (unos 74 caracteres por línea) y cada etiqueta de la leyenda va en una sola
  línea, tan corta como la inglesa (comprobado en el juego el 17-11-2026 con el aviso de
  alquimia: «ICONO: ALQUIMIA DE SANGRE DÉBIL»). `tools.validar` da como error el párrafo
  que se pasa («pisa la leyenda del aviso»); el largo de las etiquetas no lo comprueba.
- Cuaderno del laboratorio: la línea de «Efecto» va en posición fija debajo de la ficha de
  la fórmula, y las flechas, debajo del efecto. La ficha no puede ocupar más líneas que el
  original (unas 19 de 53 caracteres) y el efecto, más de dos (comprobado en el juego el
  17-11-2026 con la infusión colérica y con la Ceniza). El nombre de la fórmula en «Base
  de:» no se toca aunque parta la línea: se recorta en el resto de la ficha, sin quitar
  ingredientes ni pasos. `tools.validar` lo da como error («no cabe en el cuaderno del
  laboratorio»).
- Textos de misión del acto 1 (desde el parche del 17-11-2026): la primera línea sitúa el
  relato. «PRESENT: ALICE» es «PRESENTE: ALICE» y «EARLIER: LENZ'S ACCOUNT», «ANTES: EL
  RELATO DE LENZ».
- La mano que pierde Alice es la izquierda desde ese mismo parche; el original solo cambió
  las líneas que lo decían (`DTA1-P3-17`, `DTA1-P5-02HL`, `DTA1-P5-05HL` y una escena de
  alimentación) y la traducción sigue en cada línea lo que diga el original.
- «squat» es «okupa», pero «casa okupa» la primera vez que Lenz se lo dice a Alice
  (`DTA1-P7-1`), donde «okupa» a secas se lee como la persona.
- Ficha de banda del mapa de influencia: el recuadro no desplaza el texto y lo que pasa de
  la línea 13 se sale por debajo (comprobado en el juego el 16-11-2026 con los Zmey). Caben
  13 líneas de unos 50 caracteres, contando la línea en blanco entre párrafos; las fichas
  se dejan en 12 para tener margen. `tools.validar` lo da como error («no cabe en el
  recuadro del mapa»). Las fichas de distrito van en otro recuadro, sin medir: la más
  larga del original ocupa 10 líneas y ninguna traducción pasa de ahí.
- Panel de distrito del mapa de influencia: las etiquetas van delante de un valor en posición
  fija: «Gobernante:» (caben unos 12 caracteres) y «Controlado por:» (unos 16, en letra más
  pequeña), sin «del distrito», que ya lo dice la cabecera del panel.

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
2. **Piloto, el prólogo** (cerrada): acto 0, parte 1 (4 escenas) y `personajes.csv`. *Cierre:* el
   usuario lo juega y aprueba el estilo (tono, tú/usted, palabrotas, ortotipografía).
3. **Interfaz y sistemas** (cerrada): menús, opciones, tutoriales, diario, fichas de
   personaje, misiones, escenas de alimentación y textos del código. *Cierre:* todo lo que
   no es historia, revisado.
4. **Acto 0 (resto) y acto 1** (cerrada): 6 + 61 escenas, más las 32 de juego político del
   acto 1 (`DTA1-PL*`). Se tradujo en 11 bloques, uno por parte. *Cierre:* cada bloque
   jugado y revisado.
5. **Acto 2**: 72 escenas en 13 partes. *Cierre:* igual.
6. **Acto 3 y finales**: 22 escenas y 5 finales. *Cierre:* el juego se completa en español.
7. **Revisión global**: coherencia de todo el texto, imágenes con texto incrustado y
   correcciones acumuladas. *Cierre:* ninguna cadena sin traducir ni aviso de validación.
8. **Publicación**: instalador `.exe`, instrucciones en el README y versión 1.0 en GitHub
   Releases. *Cierre:* alguien sin Python instala y desinstala el mod.

Peso aproximado del texto: acto 0, 8 %; acto 1, 37 %; acto 2, 35 %; acto 3, 20 %.

**Fase actual: 5, sin empezar.** La fase 4 se cerró el 17-11-2026: el usuario jugó y
aprobó los 11 bloques (acto 0, partes 2 y 3; acto 1 entero con su juego político) y las
dudas de cada uno. Los actos 0 y 1 no tienen ninguna cadena sin traducir; quedan en inglés
los actos 2 y 3 y los finales. Al cerrar una fase, se actualiza esta línea.
