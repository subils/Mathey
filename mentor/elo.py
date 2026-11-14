"""Elo per al Cangur: un número per a cada problema i un per a cada alumne.

Com als escacs, si l'alumne té més Elo que el problema, és probable que l'encerti;
si en té menys, és probable que falli. En acabar cada problema, l'Elo de l'alumne
puja si encerta i baixa si falla, i més com més inesperat era el resultat.

Elo inicial d'un problema (abans de tenir respostes d'alumnes):

    elo = BASE + LEVEL_STEP × nivell + SPREAD × posició

- `nivell`: el nivell del Cangur (0 = 5è de primària ... 7 = 2n de batxillerat).
- `posició`: on és la pregunta dins l'examen, de 0 (la primera) a 1 (l'última).
  Al Cangur les preguntes van de fàcil a difícil, en tres blocs de 3, 4 i 5 punts.
  Els examens dels nivells 0-1 tenen 24 preguntes; els dels nivells 2-7, 30.
- `SPREAD` > `LEVEL_STEP`, de manera que els nivells es solapen: l'última pregunta
  de 5è és més difícil que la primera de 6è, com passa de debò.

Adaptació al Cangur respecte dels escacs: les preguntes són de 5 opcions, així que
encertar a l'atzar passa un 20% de les vegades. L'encert esperat és

    E = 0.2 + 0.8 / (1 + 10 ** ((elo_problema - elo_alumne) / 400))

i per tant un encert d'un problema molt per sobre del nivell de l'alumne puja menys
que als escacs (podria haver estat sort), i una errada en un de molt fàcil baixa
gairebé el màxim.

Els Elo inicials són una estimació. Amb respostes reals, l'Elo dels problemes també
s'actualitza (amb una K petita), com fan les webs d'escacs amb els problemes tàctics.
"""

BASE = 800
# 110 i no 150: els problemes que surten el mateix any en dos nivells seguits (31
# parelles) queden amb el mateix Elo de mitjana amb 110; amb 150, la còpia del nivell
# alt sortia uns 70-95 punts més cara.
LEVEL_STEP = 110
SPREAD = 450
GUESS = 0.2  # 1 de cada 5 opcions
SCALE = 400

QUESTIONS = {0: 24, 1: 24}  # la resta de nivells: 30
DEFAULT_QUESTIONS = 30

# K de l'alumne: alta al principi (encara no sabem el seu nivell) i després més estable
K_NEW = 40
K_STABLE = 24
NEW_ATTEMPTS = 20
# K del problema: petita, perquè un sol alumne no en canviï gaire la dificultat
K_PROBLEM = 8

# Curs de l'alumne -> nivell del Cangur (com a mentor/config.py GRADE_LEVEL)
GRADE_LEVEL = {"5è": 0, "6è": 1, "1r ESO": 2, "2n ESO": 3, "3r ESO": 4, "4t ESO": 5,
               "1r batx": 6, "2n batx": 7}


def questions_in_exam(level):
    return QUESTIONS.get(level, DEFAULT_QUESTIONS)


def position(level, number):
    """Posició de la pregunta dins l'examen, de 0 (primera) a 1 (última)."""
    n = questions_in_exam(level)
    number = min(max(number, 1), n)
    return (number - 1) / (n - 1)


def block_points(level, number):
    """Punts de la pregunta al Cangur: 3, 4 o 5 segons el terç de l'examen."""
    n = questions_in_exam(level)
    third = n // 3
    return 3 + min((max(number, 1) - 1) // third, 2)


def problem_elo(level, number):
    """Elo inicial d'un problema a partir del nivell i del número de pregunta."""
    return round(BASE + LEVEL_STEP * level + SPREAD * position(level, number))


def initial_student_elo(level):
    """Elo inicial d'un alumne: al mig del primer bloc (3 punts) del seu nivell."""
    return round(BASE + LEVEL_STEP * level + SPREAD * (1 / 6))


def expected(student_elo, problem_elo_value):
    """Probabilitat d'encert, comptant que a l'atzar s'encerta 1 de cada 5."""
    chess = 1 / (1 + 10 ** ((problem_elo_value - student_elo) / SCALE))
    return GUESS + (1 - GUESS) * chess


def score(correct, hints_used=0):
    """Resultat del problema entre 0 i 1. Cada ajuda feta servir resta una mica."""
    if not correct:
        return 0.0
    return max(0.4, 1.0 - 0.15 * hints_used)


def update(student_elo, problem_elo_value, result, attempts=NEW_ATTEMPTS):
    """Torna (nou Elo de l'alumne, nou Elo del problema).

    `result` és 1 (encert), 0 (errada) o un valor entremig de score().
    `attempts` és quants problemes ha fet l'alumne abans d'aquest.
    """
    e = expected(student_elo, problem_elo_value)
    k = K_NEW if attempts < NEW_ATTEMPTS else K_STABLE
    new_student = student_elo + k * (result - e)
    new_problem = problem_elo_value - K_PROBLEM * (result - e)
    return round(new_student), round(new_problem)
