#!/usr/bin/env python3
"""Alumnes simulats: el motor adaptatiu porta cada alumne al seu nivell real?

    python3 scripts/simulate_students.py
    python3 scripts/simulate_students.py --problems 30 --seeds 5

Cada alumne simulat té un nivell real (0-3) que el mentor no coneix, i comença
al nivell del curs que diu fer (que pot no coincidir). Respon bé amb probabilitat
alta si el problema és del seu nivell o inferior, i amb probabilitat d'endevinar
si és més difícil. Fa servir el mateix codi del mentor (mentor/service.py) i una
base d'estat temporal, així que no toca els alumnes de veritat.

Imprimeix, per a cada perfil, el nivell on acaba i quants problemes triga a
arribar-hi. Són els números de «el motor adaptatiu convergeix».
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

from mentor import service, store  # noqa: E402

GRADES = ["5è", "6è", "1r ESO", "2n ESO"]
P_OK = 0.85     # encert si el problema és del seu nivell o més fàcil
P_GUESS = 0.25  # encert si és més difícil (endevinar + alguna sort)


def label_of(pid):
    return store.one(store.bank(), "SELECT label FROM problems WHERE id = ? AND lang = 'cat'", (pid,))["label"]


def simulate(ability, grade, n, rng):
    sid = service.create_session({"alias": f"sim-{ability}-{grade}", "grade": grade})["student"]
    levels = []
    for _ in range(n):
        nxt = service.next_problem({"student": sid})
        problem = nxt["problem"]
        if not problem:
            break
        correct = rng.random() < (P_OK if problem["level"] <= ability else P_GUESS)
        label = label_of(problem["id"])
        letter = label if correct else rng.choice([x for x in "ABCDE" if x != label])
        result = service.answer({"student": sid, "problem_id": problem["id"], "letter": letter})
        levels.append(result["level"])
    return levels


def first_stable(levels, target):
    """Primer problema a partir del qual l'alumne no s'allunya més d'1 nivell del real."""
    for i in range(len(levels)):
        if all(abs(x - target) <= 1 for x in levels[i:]):
            return i + 1
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--problems", type=int, default=25)
    p.add_argument("--seeds", type=int, default=5)
    args = p.parse_args()

    counts = store.query(store.bank(), """SELECT p.level, COUNT(*) AS n FROM content c
        JOIN problems p ON p.id = c.id AND p.lang = 'cat' WHERE c.verified = 1 GROUP BY p.level""")
    print("Problemes verificats per nivell:", {r["level"]: r["n"] for r in counts})
    print(f"{args.seeds} alumnes per perfil, {args.problems} problemes cadascun\n")
    print(f"{'nivell real':>11} {'curs que diu':>13} {'nivell final':>13} {'mitjana últims 10':>18} {'estable al problema':>20}")
    for ability in range(4):
        for grade in (GRADES[0], GRADES[3]):
            finals, tails, stable = [], [], []
            for seed in range(args.seeds):
                levels = simulate(ability, grade, args.problems, random.Random(1000 * ability + seed))
                if not levels:
                    continue
                finals.append(levels[-1])
                tails.append(statistics.mean(levels[-10:]))
                s = first_stable(levels, ability)
                if s:
                    stable.append(s)
            if finals:
                print(f"{ability:>11} {grade:>13} {statistics.mean(finals):>13.1f} {statistics.mean(tails):>18.2f} "
                      f"{(f'{statistics.median(stable):.0f}' if stable else '-'):>20}")


if __name__ == "__main__":
    main()
