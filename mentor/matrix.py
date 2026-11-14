"""Dibuixos de la matriu de LEDs de la placa: 8 files x 13 columnes, brillantor 0-7.

La mateixa funció serveix per a la placa (l'app d'App Lab els envia pel Bridge)
i per a la web (que els simula). Res de parpellejos: un dibuix fix per estat.
Només hi ha quatre estats: ✓ (resposta correcta), ✗ (incorrecta), «pensant»
mentre respon el model, i la K en repòs (problema nou, sense resposta encara).
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
IDLE = [  # una K de Cangur
    ".............",
    "....#...#....",
    "....#..#.....",
    "....#.#......",
    "....##.......",
    "....#.#......",
    "....#..#.....",
    "....#...#....",
]


def _grid(pattern):
    return [[ON if ch == "#" else 0 for ch in row] for row in pattern]


def check():
    return _grid(CHECK)


def cross():
    return _grid(CROSS)


def thinking():
    return _grid(THINKING)


def idle():
    return _grid(IDLE)
