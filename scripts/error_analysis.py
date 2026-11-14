#!/usr/bin/env python3
"""Error analysis of predict.py by topic, language, level and figure (deliverable).

    python3 scripts/error_analysis.py                       # latest results/eval-*.csv
    python3 scripts/error_analysis.py results/eval-....csv --markdown results/error_analysis.md

Joins the per-problem rows that eval.py writes with the topic of each problem
(table `topics` of data/mentor.db, built by scripts/build_bank.py) and prints
accuracy tables with the number of problems next to each value, plus the
predicted-vs-true letter matrix. With --markdown it also writes the tables in a
file ready for the README. The tables only hold ids, counts and percentages: no
M3Kang text.
"""
import argparse
import csv
import glob
import os
import sqlite3
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVELS = {0: "5è prim.", 1: "6è prim.", 2: "1r ESO", 3: "2n ESO", 4: "3r ESO", 5: "4t ESO", 6: "1r batx.", 7: "2n batx."}


def load_topics(db_path):
    if not os.path.exists(db_path):
        return {}
    db = sqlite3.connect(db_path)
    try:
        return dict(db.execute("SELECT id, topic FROM topics"))
    except sqlite3.OperationalError:
        return {}


def load_figures(db_path):
    if not os.path.exists(db_path):
        return {}
    db = sqlite3.connect(db_path)
    return {pid: not bool(t) for pid, t in db.execute("SELECT id, text_only FROM problems WHERE lang = 'cat'")}


def table(title, groups, order=None):
    keys = order if order else sorted(groups, key=str)
    lines = [f"\n### {title}\n", "| | Encerts | Problemes | Encert |", "|---|---:|---:|---:|"]
    for key in keys:
        if key not in groups:
            continue
        hits = groups[key]
        lines.append(f"| {key} | {sum(hits)} | {len(hits)} | {100 * sum(hits) / len(hits):.1f}% |")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", nargs="?", help="per defecte, l'últim results/eval-*.csv")
    p.add_argument("--db", default=os.path.join(ROOT, "data", "mentor.db"))
    p.add_argument("--markdown", help="escriu les taules en aquest fitxer")
    args = p.parse_args()

    path = args.csv or max(glob.glob(os.path.join(ROOT, "results", "eval-*.csv")), default=None, key=os.path.getmtime)
    if not path:
        sys.exit("No hi ha cap results/eval-*.csv. Executa abans: python3 eval.py --limit 0")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    topics = load_topics(args.db)
    figures = load_figures(args.db)

    by = defaultdict(lambda: defaultdict(list))
    predicted, truth = Counter(), Counter()
    confusion = Counter()
    for r in rows:
        ok = r["correct"] in ("1", "True", "true")
        by["Per tema"][topics.get(r["id"], "sense tema")].append(ok)
        by["Per idioma"][r["language"]].append(ok)
        level = int(r["level"]) if r.get("level", "").isdigit() else None
        by["Per nivell"][f"{level} ({LEVELS.get(level, '?')})" if level is not None else "?"].append(ok)
        if r["id"] in figures:
            by["Amb o sense figura"]["amb figura" if figures[r["id"]] else "només text"].append(ok)
        by["Opcions llegides per OCR"]["sí" if r.get("has_options") in ("True", "1") else "no"].append(ok)
        predicted[r["answer"]] += 1
        truth[r["label"]] += 1
        confusion[(r["label"], r["answer"])] += 1

    hits = [r["correct"] in ("1", "True", "true") for r in rows]
    out = [f"## Anàlisi d'errors de `predict.py`\n",
           f"Fitxer: `{os.path.relpath(path, ROOT)}` · {len(rows)} problemes · "
           f"encert global {sum(hits)}/{len(rows)} = {100 * sum(hits) / max(len(rows), 1):.1f}% "
           f"(sempre D: {100 * truth['D'] / max(len(rows), 1):.1f}%; atzar: 20%)"]
    for title in ("Per tema", "Per idioma", "Per nivell", "Amb o sense figura", "Opcions llegides per OCR"):
        if by[title]:
            out.append(table(title, by[title]))
    out.append("\n### Lletres: veritat (files) contra predicció (columnes)\n")
    out.append("| | " + " | ".join("ABCDE") + " | Total |")
    out.append("|---|" + "---:|" * 6)
    for t in "ABCDE":
        out.append(f"| **{t}** | " + " | ".join(str(confusion[(t, q)]) for q in "ABCDE") + f" | {truth[t]} |")
    out.append("| **Predites** | " + " | ".join(str(predicted[q]) for q in "ABCDE") + f" | {len(rows)} |")
    text = "\n".join(out)
    print(text)
    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\nEscrit {args.markdown}")


if __name__ == "__main__":
    main()
