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

L'Elo de l'ALUMNE no se suma i resta resposta a resposta (vegeu estimate()): cada
cop es torna a calcular amb totes les seves respostes, les recents pesant més. Així
l'Elo de partida (el del curs) deixa de pesar de seguida si no era el bo.
"""
import math

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

# K de l'alumne (només per a update(), el mètode clàssic; el mentor fa servir
# estimate()): com més problemes fa, menys es mou l'Elo per cada resposta.
# 1. Col·locació (els PLACEMENT_ATTEMPTS primers): K molt alta, perquè l'Elo inicial
#    només ve del curs que diu fer l'alumne i pot estar lluny del real. Amb alumnes
#    simulats (scripts/simulate_students.py), passar de 40 a 100 en aquests problemes
#    redueix l'error dels mal situats de ~177 a ~109 punts després de 30 problemes,
#    sense empitjorar els que ja comencen a prop del seu Elo real.
# 2. Nou (fins a NEW_ATTEMPTS): encara ajustant.
# 3. Estable: canvis petits.
K_PLACEMENT = 100
PLACEMENT_ATTEMPTS = 8
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


def initial_elo_for_grade(grade, max_level=7):
    """Elo inicial d'un alumne a partir del curs que diu fer (5è, 6è, 1r ESO...)."""
    return initial_student_elo(min(GRADE_LEVEL[grade], max_level))


def led_level(rating, max_level=7):
    """El nivell del Cangur que correspon a un Elo. NOMÉS per a la matriu de LEDs.

    És l'invers d'initial_student_elo(): un alumne nou de 6è (985) surt nivell 1, i
    a mesura que el seu Elo puja o baixa, el número de la matriu el segueix. Res
    més del mentor fa servir nivells d'alumne: tot es decideix amb l'Elo.
    """
    level = round((rating - BASE - SPREAD / 6) / LEVEL_STEP)
    return max(0, min(max_level, level))


def expected(student_elo, problem_elo_value):
    """Probabilitat d'encert, comptant que a l'atzar s'encerta 1 de cada 5."""
    chess = 1 / (1 + 10 ** ((problem_elo_value - student_elo) / SCALE))
    return GUESS + (1 - GUESS) * chess


def score(correct, hints_used=0):
    """Resultat del problema entre 0 i 1. Cada ajuda feta servir resta una mica."""
    if not correct:
        return 0.0
    return max(0.4, 1.0 - 0.15 * hints_used)


def k_student(attempts):
    """K de l'alumne segons quants problemes ha fet abans d'aquest."""
    if attempts < PLACEMENT_ATTEMPTS:
        return K_PLACEMENT
    if attempts < NEW_ATTEMPTS:
        return K_NEW
    return K_STABLE


# --------------------------------------------------- Elo de l'alumne: estimació
#
# En comptes de sumar i restar K × (resultat − esperat) a cada resposta, es busca
# l'Elo que millor explica TOTES les respostes de l'alumne alhora (com fan els
# tests adaptatius tipus PISA). Es prova cada Elo possible de GRID i es mira:
#   - com d'acord està amb l'Elo de partida (el del curs), amb marge PRIOR_SD;
#   - com de probables són les seves respostes si l'alumne tingués aquest Elo.
# El resultat és la mitjana de tots els Elo possibles ponderada per aquesta
# probabilitat.
#
# Les respostes antigues pesen menys (meitat cada HALF_LIFE respostes): un alumne
# que aprèn no queda frenat per com responia fa setmanes.
#
# Amb alumnes simulats (30 problemes), l'error dels que comencen lluny del seu Elo
# real baixa de ~97 a ~75 punts, prop del mínim teòric amb 30 respostes A–E (~77),
# sense empitjorar els que comencen a prop.

PRIOR_SD = 250
HALF_LIFE = 40
GRID = range(300, 2501, 5)
MAX_ANSWERS = 4 * HALF_LIFE  # més enllà, el pes és < 1/16: no val la pena comptar-les


def estimate(start, answers, prior_sd=PRIOR_SD, half_life=HALF_LIFE):
    """Elo de l'alumne a partir de totes les seves respostes.

    `start`: l'Elo de partida (el del curs).
    `answers`: [(Elo del problema quan el va fer, resultat de score()), ...], de la
    més antiga a la més recent.
    """
    answers = list(answers)[-MAX_ANSWERS:]
    n = len(answers)
    weighted = [(p, s, 0.5 ** ((n - 1 - i) / half_life)) for i, (p, s) in enumerate(answers)]
    logs = []
    for t in GRID:
        lp = -0.5 * ((t - start) / prior_sd) ** 2
        for p, s, w in weighted:
            e = min(max(expected(t, p), 1e-9), 1 - 1e-9)
            lp += w * (s * math.log(e) + (1 - s) * math.log(1 - e))
        logs.append(lp)
    top = max(logs)
    weights = [math.exp(x - top) for x in logs]
    return round(sum(t * x for t, x in zip(GRID, weights)) / sum(weights))


def update(student_elo, problem_elo_value, result, attempts=NEW_ATTEMPTS):
    """Torna (nou Elo de l'alumne, nou Elo del problema), a l'estil dels escacs.

    El mentor en fa servir el NOU ELO DEL PROBLEMA; el de l'alumne el calcula amb
    estimate(). La part de l'alumne es manté per comparar els dos mètodes.

    `result` és 1 (encert), 0 (errada) o un valor entremig de score().
    `attempts` és quants problemes ha fet l'alumne abans d'aquest.
    """
    e = expected(student_elo, problem_elo_value)
    new_student = student_elo + k_student(attempts) * (result - e)
    new_problem = problem_elo_value - K_PROBLEM * (result - e)
    return round(new_student), round(new_problem)
