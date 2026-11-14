#!/usr/bin/env python3
"""Construeix el banc del mentor (data/mentor.db) a partir de M3Kang i del contingut preparat.

    python3 scripts/build_bank.py
    python3 scripts/build_bank.py --source research/qualcomm-repo/data --out data/mentor.db

Fa tres coses:
1. Carrega els problemes (train i val, català i anglès) amb la resposta oficial.
2. Carrega el contingut generat pels agents (data/generated/*_output.jsonl) i el
   **verifica**: la resposta de l'agent ha de coincidir amb l'oficial, i cap pista
   pot contenir la resposta. Només el contingut verificat arriba a l'alumne.
3. Calcula els problemes semblants (TF-IDF sobre el text en anglès).

El fitxer resultant conté problemes de M3Kang: no es puja mai a GitHub.
"""
import argparse
import glob
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mentor import filters, similarity  # noqa: E402
from mentor.store import BANK_SCHEMA  # noqa: E402

TOPICS = {"geometria", "àlgebra", "aritmètica", "combinatòria i probabilitat", "lògica"}


def load_problems(source):
    rows = []
    for split in ("train", "val"):
        path = os.path.join(source, f"{split}.jsonl")
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    r["split"] = split
                    rows.append(r)
    return rows


def load_generated(generated, pattern="*_output.jsonl"):
    items = {}
    for path in sorted(glob.glob(os.path.join(generated, pattern))):
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except ValueError:
                    print(f"  ! línia il·legible: {os.path.basename(path)}:{n}")
                    continue
                items[item["id"]] = item  # l'últim guanya
    return items


def check(item, label, statement=""):
    """Torna (verificat, llista de problemes trobats, pistes netes)."""
    found = []
    if item.get("resposta") != label:
        found.append(f"resposta de l'agent {item.get('resposta')} ≠ oficial {label}")
    if item.get("tema") not in TOPICS:
        found.append(f"tema desconegut: {item.get('tema')}")
    hints = list(item.get("pistes") or [])
    if len(hints) != 3:
        found.append(f"{len(hints)} pistes en lloc de 3")
    option = (item.get("opcions") or {}).get(label, "")
    clean = []
    for k, h in enumerate(hints, 1):
        reason = filters.leaks(h, label, option, statement)
        if reason:
            found.append(f"pista {k}: {reason}")
            clean.append(None)
        else:
            clean.append(h)
    if not item.get("solucio"):
        found.append("sense solució")
    verified = not any(f.startswith(("resposta", "tema", "sense")) for f in found)
    return verified, found, clean


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", default=os.path.join(ROOT, "research", "qualcomm-repo", "data"))
    p.add_argument("--generated", default=None, help="per defecte, <source>/generated")
    p.add_argument("--out", default=os.path.join(ROOT, "data", "mentor.db"))
    args = p.parse_args()
    generated = args.generated or os.path.join(args.source, "generated")

    import sqlite3
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    tmp = args.out + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    db = sqlite3.connect(tmp)
    db.executescript(BANK_SCHEMA)

    problems = load_problems(args.source)
    db.executemany("INSERT OR REPLACE INTO problems VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        (r["id"], r["language"], r["level"], r.get("year"), int(bool(r.get("text_only"))), r["text"],
         json.dumps(r.get("options") or {}, ensure_ascii=False), r["label"], r["split"]) for r in problems])
    labels = {r["id"]: r["label"] for r in problems if r["language"] == "cat"}
    statements = {r["id"]: r["text"] for r in problems if r["language"] == "cat"}
    print(f"Problemes: {len(labels)} ({len(problems)} files amb els dos idiomes)")

    # Contingut complet (pilot i lots); els fitxers topics_* només porten el tema
    items = {**load_generated(generated, "pilot_output.jsonl"), **load_generated(generated, "batch_*_output.jsonl")}
    stats = {"total": 0, "verificats": 0, "resposta diferent": 0, "pistes bloquejades": 0}
    mismatches = []
    for pid, item in items.items():
        if pid not in labels:
            continue
        stats["total"] += 1
        verified, found, clean = check(item, labels[pid], statements.get(pid, ""))
        stats["verificats"] += verified
        if any(f.startswith("resposta") for f in found):
            stats["resposta diferent"] += 1
            mismatches.append(pid)
        stats["pistes bloquejades"] += sum(1 for h in clean if h is None)
        db.execute("INSERT OR REPLACE INTO content VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            pid, "cat", item.get("tema"), item.get("idea_clau"),
            json.dumps(clean, ensure_ascii=False), json.dumps(item.get("solucio") or [], ensure_ascii=False),
            json.dumps(item.get("trampes") or {}, ensure_ascii=False), item.get("enunciat_facil"),
            json.dumps(item.get("opcions") or {}, ensure_ascii=False), item.get("resposta"),
            item.get("seguretat"), int(verified), json.dumps(found, ensure_ascii=False)))
    print("Contingut preparat: " + ", ".join(f"{k} {v}" for k, v in stats.items()))
    if mismatches:
        print("  Resposta diferent (fora del banc): " + ", ".join(sorted(mismatches)))

    # Tema de tots els problemes: el del contingut (nivells 0-3) i el classificat (nivells 4-7)
    topic_rows = {pid: (item.get("tema"), "contingut") for pid, item in items.items()
                  if pid in labels and item.get("tema") in TOPICS}
    for pid, item in load_generated(generated, "topics_*_output.jsonl").items():
        if pid in labels and pid not in topic_rows and item.get("tema") in TOPICS:
            topic_rows[pid] = (item["tema"], "classificació")
    db.executemany("INSERT OR REPLACE INTO topics VALUES (?, ?, ?)",
                   [(pid, t, src) for pid, (t, src) in topic_rows.items()])
    print(f"Temes: {len(topic_rows)} de {len(labels)} problemes")

    started = time.perf_counter()
    # Reserva: semblança de l'enunciat en anglès, per a tots els problemes
    english = {r["id"]: r["text"] for r in problems if r["language"] == "eng"}
    near = similarity.neighbors(english, k=30)
    # Problemes amb contingut: semblança del mètode (tema + idea clau + solució)
    method = {}
    for pid, item in items.items():
        if pid in labels:
            method[pid] = " ".join([item.get("tema") or "", item.get("tema") or "", item.get("idea_clau") or "",
                                    " ".join(item.get("solucio") or [])])
    if len(method) > 1:
        near.update(similarity.neighbors(method, k=30))
    db.executemany("INSERT OR REPLACE INTO neighbors VALUES (?, ?, ?, ?)", [
        (pid, rank, other, score) for pid, pairs in near.items() for rank, (score, other) in enumerate(pairs)])
    print(f"Problemes semblants: {len(near)} problemes, {time.perf_counter() - started:.1f} s")

    db.executemany("INSERT OR REPLACE INTO meta VALUES (?, ?)", [
        ("built_at", time.strftime("%Y-%m-%d %H:%M:%S")),
        ("stats", json.dumps(stats, ensure_ascii=False)),
    ])
    db.commit()
    db.close()
    os.replace(tmp, args.out)
    print(f"Escrit {args.out} ({os.path.getsize(args.out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
