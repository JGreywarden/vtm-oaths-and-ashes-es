"""esquemas de las clases con texto visible, deducidos de los bytes del juego.

un esquema es una tupla de elementos:
  un entero       ese número de bytes sin texto (enteros, booleanos, punteros)
  "str"           una cadena que no se ve: identificador, clave, nombre de tipo
  "text:grupo"    una cadena de texto visible; el grupo decide en qué .jsonl se traduce
  una lista       número de elementos (int32) y el esquema de la lista repetido
  "rest"          el resto del objeto, cuando ya no contiene cadenas
"""

PPTR = 12
HEAD = (28, "str")  # cabecera de monobehaviour y nombre del objeto

# una llamada de unityevent: destino, tipo, método, modo, argumentos y estado
CALLS = [PPTR, "str", "str", 4, PPTR, "str", 8, "str", 8]
# condición o cambio sobre una variable de diálogo: variables, clave y valores
VARIABLE = [PPTR, "str", 16]
# música, dos valores de volumen y efectos de sonido (guid de fmod)
AUDIO = ("str", 8, [20])

LINE = ["str", "text:hablantes", "text:linea", "str", "str", "str", "str", *AUDIO, CALLS]
CHOICE = [
    "text:opcion",
    8,  # termina la misión, fin de la partida
    "str",  # nodo siguiente
    4,
    "str",  # nodo siguiente en modo bestia
    8,
    "str",  # nodo siguiente en frenesí
    8 + 2 * PPTR + 8,  # disciplina, coste, dos iconos y dos marcas de condición
    "text:requisitos",
    VARIABLE,
    [PPTR, 12, "str", 4],  # condiciones sobre los datos del jugador
    [12, PPTR],  # condiciones de inventario
    36,  # campos que valen cero en todo el juego
    VARIABLE,
    CALLS,
    PPTR + 4,  # fórmula de alquimia y cantidad
    *AUDIO,
]
NODE = ["str", LINE, CHOICE, PPTR + 4]
DIALOGUE_TREE = (*HEAD, NODE, ["str", PPTR], ["str", 2 * PPTR])

# título y descripción; antes, las variables que desbloquean la misión
MISSION = (
    *HEAD,
    "str",
    24,
    VARIABLE,
    20,
    "text:misiones",
    "text:misiones",
    16 + PPTR + 16,
    [PPTR],
    [PPTR],
    "str",  # música
)

SCHEMAS = {
    "DialogueTreeSO": DIALOGUE_TREE,
    # título, cuerpo y ficha de una entrada del diario
    "Adhik.JournalSystem.JournalSubCategory": (
        *HEAD,
        "str",
        "text:diario",
        16,
        "text:diario",
        "text:diario",
        PPTR,
    ),
    "Adhik.JournalSystem.JournalMainCategory": (
        *HEAD,
        "str",
        "text:diario",
        16,
        "text:diario",
        [PPTR],
        4,
    ),
    "VTM.Gameplay.Mission.MainStoryMissionData": (*MISSION, 24),
    "VTM.Gameplay.Mission.PoliticalPlayMissionData": (*MISSION, 36),
    # nombre, descripción y efecto de una fórmula
    "VTM.Gameplay.AlchemySystem.FormulaDefinitionSO": (
        *HEAD,
        "str",
        *["text:alquimia"] * 3,
        "rest",
    ),
    # nombre, descripción y dos veces el gobernante del distrito
    "VTM.Gameplay.Influence.DistrictInfo": (
        *HEAD,
        4,
        "text:influencia",
        "text:influencia",
        4,
        "text:influencia",
        8,
        "text:influencia",
        4,
    ),
    # nombre de la banda y diez textos: nombres y descripciones del líder según lo que se sabe
    "VTM.Gameplay.Influence.GangInfo": (
        *HEAD,
        4,
        *["text:influencia"] * 11,
        9 * PPTR + 16,
        [PPTR],
        12,
    ),
    # campos de graphic y maskablegraphic, el evento de recorte y después el texto
    "TMPro.TextMeshProUGUI": (*HEAD, PPTR + 16 + 4 + 16 + 4, CALLS, "text:textos", "rest"),
}
