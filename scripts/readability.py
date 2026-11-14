#!/usr/bin/env python3
"""Llegibilitat de la versió «lectura fàcil» (mode dislèxia) contra l'enunciat original.

    python3 scripts/readability.py

Mesures que proposen els organitzadors: paraules per frase i paraules llargues
per frase. També comprova que la versió fàcil conserva tots els números de
l'enunciat original (la matemàtica no ha de canviar). Llegeix data/mentor.db i
només imprimeix xifres agregades (cap text de M3Kang).
"""
import os
import re
import sqlite3
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mentor.filters import _numbers  # noqa: E402

LONG = 9  # lletres: «paraula llarga» a partir d'aquí


def sentences(text, by_line=False):
    text = re.sub(r"^\s*\d+\.\s*", "", text or "")  # treu el número del problema
    parts = text.split("\n") if by_line else re.split(r"(?<=[.?!:;])\s+", text.replace("\n", " "))
    return [p.strip() for p in parts if re.search(r"\w", p)]


def words(sentence):
    return re.findall(r"[\wÀ-ÿ·'’-]+", sentence)


def stats(texts, by_line):
    wps, lps = [], []
    for t in texts:
        for s in sentences(t, by_line):
            w = words(s)
            wps.append(len(w))
            lps.append(sum(1 for x in w if len(x) >= LONG))
    return statistics.mean(wps), statistics.mean(lps), len(wps)


def main():
    db = sqlite3.connect(os.path.join(ROOT, "data", "mentor.db"))
    rows = db.execute("""SELECT p.text, c.easy_text FROM content c
        JOIN problems p ON p.id = c.id AND p.lang = 'cat' WHERE c.verified = 1 AND c.easy_text != ''""").fetchall()
    if not rows:
        sys.exit("No hi ha contingut verificat. Executa abans scripts/build_bank.py")
    original = stats([r[0] for r in rows], by_line=False)
    easy = stats([r[1] for r in rows], by_line=True)
    kept = sum(1 for text, easy_text in rows
               if _numbers(re.sub(r"^\s*\d+\.\s*", "", text)) <= _numbers(easy_text))
    print(f"Problemes: {len(rows)}")
    print(f"Paraules per frase:           original {original[0]:.1f}  ·  lectura fàcil {easy[0]:.1f}")
    print(f"Paraules llargues per frase:  original {original[1]:.2f}  ·  lectura fàcil {easy[1]:.2f}")
    print(f"Conserven tots els números de l'enunciat: {kept} de {len(rows)} ({100 * kept / len(rows):.0f}%)")


if __name__ == "__main__":
    main()
