"""Dibuixos de la matriu de LEDs de la placa: 8 files x 13 columnes, brillantor 0-7.

La mateixa funció serveix per a la placa (l'app d'App Lab els envia pel Bridge)
i per a la web (que els simula). Res de parpellejos: un dibuix fix per estat.
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
DIGITS = {
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
}


def _grid(pattern):
    return [[ON if ch == "#" else 0 for ch in row] for row in pattern]


def _blank():
    return [[0] * COLS for _ in range(ROWS)]


def check():
    return _grid(CHECK)


def cross():
    return _grid(CROSS)


def thinking():
    return _grid(THINKING)


def idle():
    return _grid(IDLE)


def level(n, streak=0):
    """El nivell del Cangur (0-3) a l'esquerra i la ratxa com a barra a la dreta."""
    grid = _blank()
    glyph = DIGITS.get(str(max(0, min(3, n))), DIGITS["0"])
    for r, row in enumerate(glyph):
        for c, ch in enumerate(row):
            if ch == "#":
                grid[r + 1][c + 1] = ON
    for i in range(min(streak, 7)):  # barra de ratxa, de baix a dalt
        grid[ROWS - 1 - i][11] = ON
        grid[ROWS - 1 - i][12] = ON
    return grid
