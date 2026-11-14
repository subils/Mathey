#!/usr/bin/env python3
"""Escriu data/problems_elo.json: tots els problemes de M3Kang amb el seu Elo.

    python3 scripts/build_elo.py --source ../datathon-UPC-maths-qualcomm-arduino-unoq/data

La fórmula i les regles d'actualització són a mentor/elo.py i es copien al camp
"elo_model" del fitxer, perquè l'app no les hagi d'endevinar.

El fitxer conté problemes de M3Kang (llicència només per a recerca): queda a
data/, que no es puja a GitHub.
"""
import argparse
import collections
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mentor import elo  # noqa: E402

ID = re.compile(r"^lvl-(\d)_(\d{4})_(\d+)$")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", default=os.path.join(ROOT, "research", "qualcomm-repo", "data"))
    p.add_argument("--out", default=os.path.join(ROOT, "data", "problems_elo.json"))
    args = p.parse_args()

    problems = {}
    for split in ("train", "val"):
        with open(os.path.join(args.source, f"{split}.jsonl"), encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                m = ID.match(r["id"])
                if not m:
                    print(f"  ! id inesperat, s'omet: {r['id']}")
                    continue
                level, number = int(m[1]), int(m[3])
                item = problems.setdefault(r["id"], {
                    "id": r["id"],
                    "elo": elo.problem_elo(level, number),
                    "level": level,
                    "year": r.get("year") or int(m[2]),
                    "number": number,
                    "points": elo.block_points(level, number),
                    "label": r["label"],
                    "split": split,
                    "text_only": bool(r.get("text_only")),
                    "text": {},
                    "options": {},
                    "image": {},
                })
                lang = r["language"]
                item["text"][lang] = r["text"]
                item["options"][lang] = r.get("options") or {}
                item["image"][lang] = f"{r['id']}_{lang}.png"
                if item["label"] != r["label"]:
                    print(f"  ! {r['id']}: resposta diferent segons l'idioma")

    rows = sorted(problems.values(), key=lambda x: (x["elo"], x["id"]))
    for r in rows:
        # Sense opcions de text (són dibuixos): cal mostrar la imatge per respondre
        r["needs_image"] = not all(len(o) == 5 for o in r["options"].values())

    out = {
        "elo_model": {
            "description": "Elo inicial = BASE + LEVEL_STEP*nivell + SPREAD*posició (0 primera pregunta, "
                           "1 última). Encert esperat = GUESS + (1-GUESS)/(1+10^((elo_problema-elo_alumne)/SCALE)).",
            "BASE": elo.BASE, "LEVEL_STEP": elo.LEVEL_STEP, "SPREAD": elo.SPREAD,
            "GUESS": elo.GUESS, "SCALE": elo.SCALE,
            "questions_per_exam": {str(lv): elo.questions_in_exam(lv) for lv in range(8)},
            "K_student_new": elo.K_NEW, "K_student_stable": elo.K_STABLE,
            "new_student_attempts": elo.NEW_ATTEMPTS, "K_problem": elo.K_PROBLEM,
            "initial_student_elo": {grade: elo.initial_student_elo(lv) for grade, lv in elo.GRADE_LEVEL.items()},
            "level_range": {str(lv): [elo.problem_elo(lv, 1), elo.problem_elo(lv, elo.questions_in_exam(lv))]
                            for lv in range(8)},
            "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "problems": rows,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"Escrit {args.out}: {len(rows)} problemes ({os.path.getsize(args.out) / 1e6:.1f} MB)")
    print(f"Elo de {rows[0]['elo']} a {rows[-1]['elo']}")
    bins = collections.Counter(r["elo"] // 100 * 100 for r in rows)
    for b in sorted(bins):
        print(f"  {b}-{b + 99}: {bins[b]:4d} {'#' * (bins[b] // 5)}")


if __name__ == "__main__":
    main()
