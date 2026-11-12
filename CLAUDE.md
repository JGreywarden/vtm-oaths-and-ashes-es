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
  interfaz/             un .jsonl por archivo de interfaz
tools/                  código python
tests/                  tests de pytest
docs/                   documentación para jugadores

# solo en local, ignorado por git
.venv/  respaldo/  originales/  manuales_referencia/
```

## Arquitectura

Tres pasos, cada uno un módulo pequeño de `tools/`:

1. **extraer**: juego → `originales/` (texto en inglés, solo local).
2. **traducir**: se editan los `.jsonl` de `traduccion/`.
3. **construir**: `respaldo/` + `traduccion/` → archivos parcheados en la carpeta del juego.

Formato de traducción, una cadena por línea:

```json
{"id": "3f9a1c2b7d40", "es": "Texto traducido."}
```

- `id` = primeros 12 caracteres hexadecimales del SHA-1 del texto original en UTF-8.
- El `id` vale dentro de su archivo: una frase repetida en la misma escena se traduce una vez.
- Una cadena del juego sin `id` en su archivo está sin traducir; debe poder listarse.
- Construir parte siempre de `respaldo/`, nunca de un archivo ya parcheado.

### Datos técnicos del juego (verificados)

- Unity 6000.3.17f1, IL2CPP, sin árboles de tipos: los `MonoBehaviour` se tratan como bytes.
- Cadena serializada: longitud `int32` little-endian + UTF-8 + relleno con ceros hasta
  múltiplo de 4. Se sustituye buscando la cadena original empaquetada exacta.
- Lectura y escritura: `obj.get_raw_data()`, `obj.set_raw_data()`, `serialized_file.save()`.
- El nombre del objeto es la cadena que empieza en el byte 28 de sus datos.
- Escenas: 165 `MonoBehaviour` en `resources.assets`, nombrados `DTA{acto}-P{parte}-{escena}`
  (actos 0 a 3: 10, 61, 72 y 22 escenas). Los sufijos `H` y `HL` son variantes de una misma
  escena (significado por confirmar).
- Fuera de los actos: 4 finales (`DTEND*`) y unas 20 escenas de alimentación
  (`DTA-FEEDING*`, `DTL-FEEDING*`).
- Interfaz (menús, botones): en `sharedassets1.assets` y en los archivos `level*`.
- Dentro de una escena hay también cadenas que no son texto visible (identificadores de
  fondo como `OPERABALCONY`, nombres de tipos de C#, números de línea). No se traducen.
- Las fuentes del juego muestran bien `¿ ¡ ñ Ñ ü á é í ó ú « » — …` (comprobado en el juego).
- El archivo reescrito pesa algo menos que el original; el juego lo carga sin problemas.
- Volumen aproximado: 17.800 cadenas únicas, 360.000 palabras.

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
- Además del código se validan los datos de `traduccion/`:
  - etiquetas (`<i>`, `<b>`…) y saltos de línea iguales que en el original;
  - ninguna traducción vacía;
  - si el original contiene un término del glosario, la traducción usa su forma aprobada;
  - el glosario no tiene filas duplicadas ni mal formadas.

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
1. **Herramientas**: `requirements.txt`, `pyproject.toml`, GitHub Actions y los módulos
   extraer, construir y validar con sus tests. *Cierre:* sin traducciones, construir deja el
   juego igual; con una, se ve en el juego; tests en verde.
2. **Piloto, el prólogo**: acto 0, parte 1 (4 escenas) y `personajes.csv`. *Cierre:* el
   usuario lo juega y aprueba el estilo (tono, tú/usted, palabrotas, ortotipografía).
3. **Interfaz y sistemas**: menús, opciones, tutoriales, diario, fichas de personaje,
   misiones y escenas de alimentación. *Cierre:* todo lo que no es historia, revisado.
4. **Acto 0 (resto) y acto 1**: 6 + 61 escenas. *Cierre:* cada bloque jugado y revisado.
5. **Acto 2**: 72 escenas en 13 partes. *Cierre:* igual.
6. **Acto 3 y finales**: 22 escenas y 4 finales. *Cierre:* el juego se completa en español.
7. **Revisión global**: coherencia de todo el texto, imágenes con texto incrustado y
   correcciones acumuladas. *Cierre:* ninguna cadena sin traducir ni aviso de validación.
8. **Publicación**: instalador `.exe`, instrucciones en el README y versión 1.0 en GitHub
   Releases. *Cierre:* alguien sin Python instala y desinstala el mod.

Peso aproximado del texto: acto 0, 8 %; acto 1, 37 %; acto 2, 35 %; acto 3, 20 %.

**Fase actual: 1, sin empezar.** Al cerrar una fase, se actualiza esta línea.
