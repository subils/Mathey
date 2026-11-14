#!/usr/bin/env python3
"""Alumnes simulats: l'Elo del mentor troba l'Elo real de cada alumne?

    python3 scripts/simulate_students.py
    python3 scripts/simulate_students.py --problems 40 --seeds 5

Cada alumne simulat té un Elo real que el mentor no coneix, i comença amb l'Elo
del curs que diu fer (que pot no coincidir). Encerta cada problema amb la
probabilitat que dona el mateix model del mentor (mentor/elo.py: expected), a
partir del seu Elo real i el del problema. Fa servir el codi del mentor
(mentor/service.py) i una base d'estat temporal, així que no toca els alumnes
de veritat.

Imprimeix, per a cada perfil, l'Elo on acaba, la mitjana dels últims 10
problemes, l'error respecte del real i a partir de quin problema queda a
±TOLERANCE de l'Elo real. Són els números de «el motor adaptatiu convergeix».
"""
import argparse
import os
import random
import statistics
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_tmp = tempfile.mkdtemp(prefix="mentor-sim-")
os.environ["MENTOR_STATE_DB"] = os.path.join(_tmp, "state.db")
os.environ["MENTOR_LLM_URL"] = "http://127.0.0.1:9"  # cap IA: la simulació no la necessita

from mentor import elo, service, store  # noqa: E402

GRADES = ["5è", "2n ESO"]  # el curs que diu fer: el més baix i el més alt
TRUE_ELOS = [850, 1000, 1150, 1300, 1450]
TOLERANCE = 100


def label_of(pid):
    return store.one(store.bank(), "SELECT label FROM problems WHERE id = ? AND lang = 'cat'", (pid,))["label"]


def simulate(true_elo, grade, n, rng):
    sid = service.create_session({"alias": f"sim-{true_elo}-{grade}", "grade": grade})["student"]
    ratings = []
    for _ in range(n):
        problem = service.next_problem({"student": sid})["problem"]
        if not problem:
            break
        correct = rng.random() < elo.expected(true_elo, problem["elo"])
        label = label_of(problem["id"])
        letter = label if correct else rng.choice([x for x in "ABCDE" if x != label])
        result = service.answer({"student": sid, "problem_id": problem["id"], "letter": letter})
        ratings.append(result["elo"])
    return ratings


def first_stable(ratings, target):
    """Primer problema a partir del qual l'Elo no s'allunya més de TOLERANCE del real."""
    for i in range(len(ratings)):
        if all(abs(x - target) <= TOLERANCE for x in ratings[i:]):
            return i + 1
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--problems", type=int, default=30)
    p.add_argument("--seeds", type=int, default=5)
    args = p.parse_args()

    span = service._elo_range()
    print(f"Elo dels problemes amb contingut verificat: de {span[0]} a {span[1]}" if span else "Banc buit")
    print(f"{args.seeds} alumnes per perfil, {args.problems} problemes cadascun\n")
    print(f"{'Elo real':>8} {'curs que diu':>13} {'Elo inicial':>12} {'Elo final':>10} "
          f"{'mitjana últims 10':>18} {'error':>6} {'estable al problema':>20}")
    for true_elo in TRUE_ELOS:
        for grade in GRADES:
            finals, tails, stable = [], [], []
            for seed in range(args.seeds):
                ratings = simulate(true_elo, grade, args.problems, random.Random(10 * true_elo + seed))
                if not ratings:
                    continue
                finals.append(ratings[-1])
                tails.append(statistics.mean(ratings[-10:]))
                s = first_stable(ratings, true_elo)
                if s:
                    stable.append(s)
            if finals:
                tail = statistics.mean(tails)
                print(f"{true_elo:>8} {grade:>13} {elo.initial_elo_for_grade(grade, 3):>12} "
                      f"{statistics.mean(finals):>10.0f} {tail:>18.0f} {tail - true_elo:>+6.0f} "
                      f"{(f'{statistics.median(stable):.0f}' if stable else '-'):>20}")


if __name__ == "__main__":
    main()
