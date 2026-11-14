"""Estratègies generals per tema, escrites per nosaltres (no per la IA).

Es fan servir quan l'alumne porta un problema propi i no hi ha cap problema del
banc prou semblant, o quan la IA de la placa no respon. No depenen de cap
problema concret, així que mai poden revelar una resposta.
"""

BY_TOPIC = {
    "aritmètica": [
        "Escriu què saps i què et demanen. Després fes els càlculs d'un en un, sense saltar-te cap pas.",
        "Prova primer amb números més petits per veure com funciona, i després fes-ho amb els de l'enunciat.",
    ],
    "àlgebra": [
        "Posa un nom (una lletra) al que no saps i escriu amb paraules què li passa abans d'escriure l'equació.",
        "Comprova la teva resposta posant-la a l'enunciat: es compleix tot el que diu?",
    ],
    "geometria": [
        "Fes un dibuix gran i posa-hi totes les mides que diu l'enunciat. Marca què et demanen.",
        "Mira si pots partir la figura en trossos que coneixes (rectangles, triangles) o completar-la.",
    ],
    "combinatòria i probabilitat": [
        "Fes una llista ordenada de tots els casos, o un arbre, i compta'ls sense deixar-te'n cap ni repetir-ne.",
        "Pregunta't: l'ordre importa? Es pot repetir? Les respostes canvien com s'ha de comptar.",
    ],
    "lògica": [
        "Fes una taula amb el que diu cada pista i ves-hi marcant què és possible i què no.",
        "Suposa que una cosa és certa i mira si arribes a una contradicció. Si hi arribes, era falsa.",
    ],
}

GENERIC = "Torna a llegir l'enunciat a poc a poc i subratlla les dades i la pregunta. Què saps i què et demanen?"


def for_topic(topic, n=0):
    cards = BY_TOPIC.get(topic)
    return cards[n % len(cards)] if cards else GENERIC
