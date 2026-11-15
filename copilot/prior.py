"""A prior over the five letters, learned from M3Kang's training set (team addition).

The 0.8B model, asked for one letter, carries no information: with its letter
bias removed it scores 19.9% on validation, and the English and Catalan versions
of the same problem rarely agree. The options themselves do carry some:

- the correct letter is not uniform (D is the most common, A the least);
- when the five options are numbers, the smallest and the largest are correct
  about 10% of the time each, and the three in the middle 22-29% each.

`scores(problem)` turns that into one number per letter (a conditional logit:
one shared weight per signal, softmax over the five letters). The weights are in
prior_weights.json, fitted on train.jsonl only by scripts/train_prior.py. They
are aggregate statistics: the file holds no problem text.

Standard library only: this runs on the board inside predict.py.
"""
import json
import os
import re

LETTERS = "ABCDE"
NAMES = (["pos_" + l for l in LETTERS] + ["noopt_" + l for l in LETTERS]
         + ["num_min", "num_2nd", "num_mid", "num_4th", "num_max"])
_RANK = ["num_min", "num_2nd", "num_mid", "num_4th", "num_max"]

_NUM = re.compile(r"^\$?(-?\d+(?:[.,]\d+)?)[^\d\s]{0,6}\$?$")
_FRAC = re.compile(r"^\$?(-?\d+)/(\d+)\$?$")
_TEXFRAC = re.compile(r"\\[dt]?frac\{(-?\d+)\}\{(\d+)\}")


def number(text):
    """The numeric value of an option such as "12", "3,5 cm", "2/3" or "\\frac{1}{4}"; None if it has none."""
    s = str(text).strip().replace("−", "-").replace("\u2009", "").replace(" ", "")
    m = _TEXFRAC.search(s) or _FRAC.match(s)
    if m:
        return float(m.group(1)) / float(m.group(2)) if float(m.group(2)) else None
    m = _NUM.match(s)
    return float(m.group(1).replace(",", ".")) if m else None


def features(problem):
    """{letter: [value of each signal in NAMES]}"""
    options = problem.get("options") or {}
    have = [l for l in LETTERS if l in options]
    values = {l: number(options[l]) for l in have}
    numeric = (len(have) == 5 and all(v is not None for v in values.values())
               and len(set(values.values())) == 5)
    order = sorted(have, key=lambda l: values[l]) if numeric else []
    out = {}
    for letter in LETTERS:
        f = dict.fromkeys(NAMES, 0.0)
        f[("pos_" if len(have) == 5 else "noopt_") + letter] = 1.0
        if numeric:
            f[_RANK[order.index(letter)]] = 1.0
        out[letter] = [f[n] for n in NAMES]
    return out


def _load():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prior_weights.json")
    try:
        with open(path) as f:
            data = json.load(f)
        return dict(zip(data["names"], data["weights"]))
    except (OSError, ValueError, KeyError):
        return {}


WEIGHTS = _load()


def scores(problem):
    """{letter: score}. Higher is more likely. All zeros if the weights file is missing."""
    weights = [WEIGHTS.get(n, 0.0) for n in NAMES]
    return {letter: sum(w * x for w, x in zip(weights, row))
            for letter, row in features(problem).items()}


def best(problem):
    """The most likely letter. Ties go to the earlier letter, so the answer is deterministic."""
    s = scores(problem)
    return max(LETTERS, key=lambda l: (s[l], -LETTERS.index(l)))
