"""Dibuixos de la matriu de LEDs de la placa: 8 files x 13 columnes, brillantor 0-7.

La mateixa funció serveix per a la placa (l'app d'App Lab els envia pel Bridge)
i per a la web (que els simula). Res de parpellejos: un dibuix fix per estat.
Només hi ha quatre estats: ✓ (resposta correcta), ✗ (incorrecta), «pensant»
mentre respon el model, i apagada mentre s'espera una resposta. El ✓ i el ✗ duren
uns segons (service.RESULT_SECONDS) i després la matriu s'apaga.
"""
ROWS, COLS = 8, 13
ON = 7

CHECK = [
    ".............",
    "...........#.",
    "..........##.",
    ".........##..",
    "..#.....##...",
    "..##...##....",
    "...##.##.....",
    "....###......",
]
CROSS = [
    ".............",
    "...#.....#...",
    "....#...#....",
    ".....#.#.....",
    "......#......",
    ".....#.#.....",
    "....#...#....",
    "...#.....#...",
]
THINKING = [
    ".............",
    ".............",
    ".............",
    "..#...#...#..",
    "..#...#...#..",
    ".............",
    ".............",
    ".............",
]


def _grid(pattern):
    return [[ON if ch == "#" else 0 for ch in row] for row in pattern]


def check():
    return _grid(CHECK)


def cross():
    return _grid(CROSS)


def thinking():
    return _grid(THINKING)


def blank():
    """Tots els LEDs apagats: en espera, sense cap resultat per mostrar."""
    return [[0] * COLS for _ in range(ROWS)]
