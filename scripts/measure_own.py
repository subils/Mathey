#!/usr/bin/env python3
"""Mesura «Porta el teu problema» amb la IA de la placa i prepara el full per jutjar-la.

    python3 scripts/measure_own.py                 # els 46 problemes de eval/own_problems.jsonl
    python3 scripts/measure_own.py --n 10 --only-warm

Per a cada problema del conjunt de prova (problemes d'escola originals, amb el
dubte que tindria un alumne i la pista que donaria un bon mentor):

1. Busca el problema semblant del banc (com fa la web).
2. Demana la pista a la IA **en fred** (sense haver llegit res abans) i **en
   calent** (després de llegir el problema i l'exemple, com passa mentre
   l'alumne escriu el seu dubte).
3. Passa el control: cap número que no sigui a l'enunciat o al dubte, i curta.

Escriu results/own-<hora>.csv amb la pista, la pista de referència (`bona_pista`),
el control i els temps, i una columna `judici` buida per jutjar-la a mà
(útil / inútil / enganyosa). Al final imprimeix les medianes.

Executar-ho a la placa dona els números del pitch. No toca la base d'alumnes.
"""
import argparse
import csv
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mentor import config, filters, llm, retrieval, service, strategies  # noqa: E402


def load(path, n):
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return rows[:n] if n else rows


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", default=os.path.join(ROOT, "eval", "own_problems.jsonl"))
    p.add_argument("--n", type=int, default=0, help="0 = tots")
    p.add_argument("--only-warm", action="store_true", help="no facis la mesura en fred")
    args = p.parse_args()

    if not llm.available(timeout=3):
        sys.exit(f"La IA no respon a {config.LLM_URL}. Engega llama-server o posa MENTOR_LLM_URL.")
    problems = load(args.input, args.n)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    path = os.path.join(ROOT, "results", f"own-{time.strftime('%Y%m%d-%H%M%S')}.csv")
    cold, warm, rejected, with_example = [], [], 0, 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["problema", "tema", "tema_endevinat", "germa", "semblanca", "dubte", "mode",
                         "pista_ia", "control", "segons_resposta", "segons_lectura_previa",
                         "tokens_llegits", "tokens_escrits", "bona_pista_referencia", "judici"])
        for k, item in enumerate(problems, 1):
            text, doubt = item["enunciat"], item["dubtes"][0]
            topic, _confidence = retrieval.guess_topic(text)
            hits = retrieval.find_similar(text, k=1)
            found = bool(hits) and hits[0]["score"] >= getattr(retrieval, "LOW_SCORE", 0.0)
            example = service._example(hits[0]["id"]) if found else None
            with_example += bool(example)
            strategy = strategies.for_topic(topic)
            for warm_first in ([True] if args.only_warm else [False, True]):
                warm_s = 0.0
                if warm_first:
                    started = time.perf_counter()
                    llm.warm_own(text, example)
                    warm_s = time.perf_counter() - started
                try:
                    reply, timings = llm.own_hint(text, example, doubt, strategy)
                except OSError as error:
                    print(f"[{k}] {item['id']}: error {error}")
                    continue
                invented = filters.new_numbers(reply, text, doubt)
                reason = (f"números nous: {', '.join(sorted(invented))}" if invented
                          else "massa llarga o buida" if not reply or len(reply.split()) > service.MAX_OWN_WORDS
                          else "ok")
                rejected += reason != "ok"
                seconds = timings.get("wall_seconds", 0)
                (warm if warm_first else cold).append(seconds)
                writer.writerow([item["id"], item["tema"], topic, hits[0]["id"] if found else "",
                                 round(hits[0]["score"], 3) if hits else "", doubt,
                                 "calent" if warm_first else "fred", reply, reason, seconds,
                                 round(warm_s, 2), timings.get("prompt_n"), timings.get("predicted_n"),
                                 item.get("bona_pista", ""), ""])
                f.flush()
                print(f"[{k}/{len(problems)}] {item['id']} {'calent' if warm_first else 'fred '} "
                      f"{seconds:5.1f} s  {reason:24.24}  {reply[:90]}")
    print(f"\nFitxer per jutjar: {path}")
    print(f"Problemes amb exemple semblant: {with_example} de {len(problems)}")
    if cold:
        print(f"En fred:   mediana {statistics.median(cold):.1f} s, pitjor {max(cold):.1f} s")
    if warm:
        print(f"En calent: mediana {statistics.median(warm):.1f} s, pitjor {max(warm):.1f} s")
    print(f"No passen el control: {rejected} de {len(cold) + len(warm)}")


if __name__ == "__main__":
    main()
