#!/usr/bin/env python3
"""Mesura el router sense IA (mentor/router.py) i ajuda a triar-ne el llindar.

    python3 scripts/measure_router.py
    python3 scripts/measure_router.py --cases eval/router_cases.jsonl --show-errors

Els casos (eval/router_cases.jsonl) són problemes INVENTATS per l'equip, no de
M3Kang: cada un té les trampes de les opcions incorrectes i frases d'alumne
marcades a mà amb `match` = la frase descriu la trampa de l'opció triada.

Imprimeix, per a cada llindar:
- precisió: de les respostes a l'instant, quantes eren encertades (la frase sí
  que descrivia la trampa). És el que importa: un error aquí dona a l'alumne
  l'error típic d'una altra cosa.
- cobertura: de les frases que descrivien la trampa, quantes s'han respost a
  l'instant (la resta van a la IA, com abans).
- a l'instant: % de totes les explicacions que no necessiten la IA.

El llindar triat és el més baix amb precisió >= 95% (--min-precision).
Cal tornar-lo a mesurar amb frases reals d'alumnes quan n'hi hagi (taula
`explanations` de state.db).
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mentor import router  # noqa: E402


def commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "?"


def load(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                problem = json.loads(line)
                for case in problem["cases"]:
                    rows.append({**case, "id": problem["id"], "traps": problem["traps"]})
    return rows


def evaluate(rows, threshold):
    tp = fp = fn = tn = 0
    errors = []
    for r in rows:
        d = router.route(r["said"], r["letter"], r["traps"], threshold=threshold)
        if d.instant and r["match"]:
            tp += 1
        elif d.instant:
            fp += 1
            errors.append(("fals positiu", r, d))
        elif r["match"]:
            fn += 1
            errors.append(("fals negatiu", r, d))
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall,
            "instant": (tp + fp) / len(rows), "errors": errors}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cases", default=os.path.join(ROOT, "eval", "router_cases.jsonl"))
    p.add_argument("--min-precision", type=float, default=0.95)
    p.add_argument("--show-errors", action="store_true", help="llista els errors del llindar actual")
    args = p.parse_args()

    rows = load(args.cases)
    positives = sum(r["match"] for r in rows)
    print(f"Router sense IA · commit {commit()} · {len(rows)} frases "
          f"({positives} descriuen la trampa, {len(rows) - positives} no) · llindar actual {router.THRESHOLD}\n")
    print("Llindar | precisió | cobertura | a l'instant | FP | FN")
    print("--------|----------|-----------|-------------|----|----")
    chosen = None
    for t in [x / 100 for x in range(10, 65, 5)]:
        m = evaluate(rows, t)
        mark = " ←" if abs(t - router.THRESHOLD) < 1e-9 else ""
        print(f"  {t:.2f}  |  {m['precision']:6.1%}  |  {m['recall']:6.1%}   |   {m['instant']:6.1%}    | "
              f"{m['fp']:2d} | {m['fn']:2d}{mark}")
        if chosen is None and m["precision"] >= args.min_precision:
            chosen = t
    print(f"\nLlindar més baix amb precisió >= {args.min_precision:.0%}: {chosen}")

    if args.show_errors:
        m = evaluate(rows, router.THRESHOLD)
        print(f"\nErrors amb el llindar actual ({router.THRESHOLD}):")
        for kind, r, d in m["errors"]:
            print(f"  [{kind}] {r['id']} {r['letter']} «{r['said']}» -> {d.score:.2f}, {d.reason}")


if __name__ == "__main__":
    main()
