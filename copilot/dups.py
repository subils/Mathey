"""Find the same problem, already solved, in M3Kang (team addition).

Kangaroo papers share problems between levels of the same year, and M3Kang has
every problem in several languages. If the problem to answer is one of the
solved ones (data/train.jsonl, data/val.jsonl), its answer is known: no model
needed. Two ways to recognise it:

- same language: almost the same words (Jaccard >= 0.7), and the solved
  problem's correct VALUE is among the options. The letter is the one that holds
  that value here: levels reorder the options.
- any language: the same five options in the same order, and the same numbers
  in the statement. Words differ between languages; numbers and options don't.

Measured with train.jsonl as the index and val.jsonl as the questions
(15/11/2026): 20 of 562 rows found, 20 of 20 correct. Between the Catalan and
the English half of train, the options-and-numbers rule alone finds 1,060
problems and gets 1,041 right (98%).

The index is built in memory from the files on the board. Nothing from M3Kang
is stored in the repository. Standard library only.
"""
import collections
import json
import os
import re

from .config import CONFIG, ROOT

LETTERS = "ABCDE"
TEXT_MIN = 0.7      # word overlap to call two statements the same, same language
NUMBERS_MIN = 0.75  # overlap of the numbers in the statement, any language

_NUMBERING = re.compile(r"^\s*\d+\s*[.)]\s*")  # "13. " at the start: the problem's number in its paper


def _option(text):
    return re.sub(r"\s+", "", str(text).lower())


def entry(problem):
    text = _NUMBERING.sub("", str(problem.get("text", "")).strip())
    options = problem.get("options") or {}
    return {
        "id": problem.get("id"),
        "words": frozenset(re.findall(r"[^\W_]+", text.lower())),
        "numbers": collections.Counter(re.findall(r"\d+", text)),
        "options": tuple(_option(options[l]) for l in LETTERS) if len(options) == 5 else None,
        "label": problem.get("label"),
        "level": str(problem.get("level")), "year": str(problem.get("year")),
    }


def _jaccard(a, b):
    union = len(a | b)
    return len(a & b) / union if union else 0.0


def _counter_jaccard(a, b):
    union = sum((a | b).values())
    return sum((a & b).values()) / union if union else 1.0


class Index:
    def __init__(self, paths):
        self.entries = []
        for path in paths:
            if not os.path.isabs(path):
                path = os.path.join(ROOT, path)
            try:
                with open(path) as f:
                    for line in f:
                        if line.strip():
                            problem = json.loads(line)
                            if problem.get("label") in LETTERS and problem.get("text"):
                                self.entries.append(entry(problem))
            except (OSError, ValueError):
                continue  # no data on this board: predict.py answers without it

    def match(self, problem, exclude_id=None):
        """Return (letter, kind, score, id of the solved problem) or None."""
        q = entry(problem)
        best = None
        for e in self.entries:
            if exclude_id is not None and e["id"] == exclude_id:
                continue
            words = _jaccard(q["words"], e["words"]) if len(q["words"]) >= 6 else 0.0
            found = None
            if q["options"] and e["options"]:
                value = e["options"][LETTERS.index(e["label"])]
                if words >= TEXT_MIN and value in q["options"]:
                    found = (LETTERS[q["options"].index(value)], "same words, same value", words)
                elif q["options"] == e["options"]:
                    numbers = _counter_jaccard(q["numbers"], e["numbers"])
                    similar_length = abs(len(q["words"]) - len(e["words"])) <= 0.5 * max(len(q["words"]), len(e["words"]))
                    if numbers >= NUMBERS_MIN and similar_length and (sum(q["numbers"].values()) >= 2 or words >= 0.5):
                        found = (e["label"], "same options, same numbers", 0.5 + numbers / 2)
            elif (not q["options"] and not e["options"] and words >= 0.95
                  and q["level"] == e["level"] and q["year"] == e["year"]):
                # options in a picture: only the very same problem (other levels reorder the pictures)
                found = (e["label"], "same problem, options in a picture", words)
            if found and (best is None or found[2] > best[2]):
                best = found + (e["id"],)
        return best


_index = None


def default_index():
    """The index named by DUP_INDEX_FILES in config.env, loaded once. Empty if the files aren't there."""
    global _index
    if _index is None:
        paths = [p.strip() for p in CONFIG.get("DUP_INDEX_FILES", "").split(",") if p.strip()]
        _index = Index(paths)
    return _index
