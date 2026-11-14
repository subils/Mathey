#!/usr/bin/env python3
"""Mesura la pregunta socràtica de la IA de la placa i prepara el full per jutjar-la.

    python3 scripts/measure_socratic.py --n 30
    MENTOR_LLM_URL=http://127.0.0.1:8081 python3 scripts/measure_socratic.py --n 5

Per a cada problema verificat (a l'atzar, sempre els mateixos amb la mateixa
llavor) agafa una opció incorrecta amb error típic i simula que l'alumne explica
aquest error en primera persona. Després:

1. **En fred:** pregunta socràtica sense haver llegit el problema abans.
2. **En calent:** primer `warm()` (com fa la web quan s'obre el problema), i
   després la mateixa pregunta. És el cas real.

Escriu results/socratic-<hora>.csv amb el text, el filtre i els temps, i una
columna `judici` buida per a David (útil / inútil / enganyosa). Al final
imprimeix les medianes. Executar-ho a la placa és el que dona els números del
pitch; al portàtil només serveix per provar l'script.
"""
import argparse
import csv
import os
import random
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mentor import config, filters, llm, store  # noqa: E402


def cases(n, seed):
    rows = store.query(store.bank(), """
        SELECT c.id, c.solution, c.traps, c.options, p.text, p.label, p.level, c.topic
        FROM content c JOIN problems p ON p.id = c.id AND p.lang = 'cat'
        WHERE c.verified = 1 ORDER BY c.id""")
    rng = random.Random(seed)
    rng.shuffle(rows)
    out = []
    for r in rows:
        traps = store.loads(r["traps"], {})
        options = store.loads(r["options"], {})
        wrong = [(l, t) for l, t in sorted(traps.items()) if t and l != r["label"]]
        if not wrong:
            continue
        letter, trap = wrong[rng.randrange(len(wrong))]
        out.append({**r, "solution": store.loads(r["solution"], []), "options": options,
                    "letter": letter, "trap": trap})
        if len(out) >= n:
            break
    return out


def run(case, warm_first):
    if warm_first:
        started = time.perf_counter()
        llm.warm(case["text"], case["solution"])
        warm_s = time.perf_counter() - started
    else:
        warm_s = 0.0
    chosen = f"{case['letter']}) {case['options'].get(case['letter'], '')}"
    said = f"He fet això: {case['trap'][0].lower()}{case['trap'][1:]}"
    text, timings = llm.socratic(case["text"], case["solution"], chosen, case["trap"], said)
    correct_option = case["options"].get(case["label"], "")
    reason = filters.leaks(text, case["label"], correct_option, case["text"], strict = True) or (
        "" if filters.is_question(text) else "no és una pregunta curta")
    return text, timings, warm_s, reason, said


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--n", type=int, default=30)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--only-warm", action="store_true", help="no facis la mesura en fred")
    args = p.parse_args()

    if not llm.available(timeout=3):
        sys.exit(f"La IA no respon a {config.LLM_URL}. Engega llama-server o posa MENTOR_LLM_URL.")
    selected = cases(args.n, args.seed)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    path = os.path.join(ROOT, "results", f"socratic-{time.strftime('%Y%m%d-%H%M%S')}.csv")
    cold, warm, rejected = [], [], 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["problema", "nivell", "tema", "opcio", "alumne_diu", "mode", "pregunta",
                         "filtre", "segons_resposta", "segons_lectura_previa", "tokens_llegits",
                         "tokens_escrits", "judici"])
        for k, case in enumerate(selected, 1):
            modes = [True] if args.only_warm else [False, True]
            for warm_first in modes:
                try:
                    text, timings, warm_s, reason, said = run(case, warm_first)
                except OSError as error:
                    print(f"[{k}] {case['id']}: error {error}")
                    continue
                seconds = timings.get("wall_seconds", 0)
                (warm if warm_first else cold).append(seconds)
                rejected += bool(reason)
                writer.writerow([case["id"], case["level"], case["topic"], case["letter"], said,
                                 "calent" if warm_first else "fred", text, reason or "ok", seconds,
                                 round(warm_s, 2), timings.get("prompt_n"), timings.get("predicted_n"), ""])
                f.flush()
                print(f"[{k}/{len(selected)}] {case['id']} {'calent' if warm_first else 'fred '} "
                      f"{seconds:5.1f} s  {reason or 'ok':22.22}  {text[:80]}")
    print(f"\nFitxer per jutjar: {path}")
    if cold:
        print(f"En fred:   mediana {statistics.median(cold):.1f} s, pitjor {max(cold):.1f} s")
    if warm:
        print(f"En calent: mediana {statistics.median(warm):.1f} s, pitjor {max(warm):.1f} s")
    print(f"Rebutjades pel filtre: {rejected} de {len(cold) + len(warm)}")


if __name__ == "__main__":
    main()
