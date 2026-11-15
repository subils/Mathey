#!/usr/bin/env python3
"""Fit the letter prior of predict.py on M3Kang's training set (laptop: needs numpy and scipy).

    python3 scripts/train_prior.py                 # writes copilot/prior_weights.json
    python3 scripts/train_prior.py --check-only    # prints the numbers, writes nothing

A conditional logit over the five letters (copilot/prior.py has the signals).
Fitted on data/train.jsonl only; data/val.jsonl is only measured. It prints the
accuracy by 5-fold cross-validation on train (both languages of a problem stay
in the same fold) and on validation, next to always answering D.
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.optimize import minimize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from copilot import prior  # noqa: E402

L = prior.LETTERS


def load(name):
    with open(os.path.join(ROOT, "data", name)) as f:
        return [json.loads(line) for line in f if line.strip()]


def matrix(rows):
    x = np.array([[prior.features(p)[l] for l in L] for p in rows])
    return x, np.array([L.index(p["label"]) for p in rows]), [p["id"] for p in rows]


def fit(x, y, l2):
    def loss(w):
        s = x @ w
        s = s - s.max(1, keepdims=True)
        logp = s - np.log(np.exp(s).sum(1, keepdims=True))
        grad = ((np.exp(logp) - np.eye(5)[y])[:, :, None] * x).sum((0, 1)) / len(y) + l2 * w / len(y)
        return -logp[np.arange(len(y)), y].mean() + l2 * (w @ w) / (2 * len(y)), grad
    return minimize(loss, np.zeros(x.shape[2]), jac=True, method="L-BFGS-B").x


def accuracy(x, y, w):
    return float(((x @ w).argmax(1) == y).mean())


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--l2", type=float, default=1.0)
    p.add_argument("--check-only", action="store_true")
    p.add_argument("--out", default=os.path.join(ROOT, "copilot", "prior_weights.json"))
    args = p.parse_args()

    xt, yt, ids = matrix(load("train.jsonl"))
    xv, yv, _ = matrix(load("val.jsonl"))
    fold = {u: i % 5 for i, u in enumerate(sorted(set(ids)))}
    f = np.array([fold[u] for u in ids])
    cv = float(np.mean([accuracy(xt[f == k], yt[f == k], fit(xt[f != k], yt[f != k], args.l2)) for k in range(5)]))
    w = fit(xt, yt, args.l2)
    val = accuracy(xv, yv, w)
    print(f"train {len(yt)} rows: {100 * accuracy(xt, yt, w):.1f}%   5-fold CV: {100 * cv:.1f}%")
    print(f"validation {len(yv)} rows: {100 * val:.1f}% ({int(round(val * len(yv)))}/{len(yv)})   "
          f"always D: {100 * float(np.mean(yv == 3)):.1f}%")
    print("weights: " + ", ".join(f"{n} {x:+.2f}" for n, x in zip(prior.NAMES, w)))
    if not args.check_only:
        with open(args.out, "w") as out:
            json.dump({"names": prior.NAMES, "weights": [round(float(x), 4) for x in w], "l2": args.l2,
                       "fitted_on": "data/train.jsonl", "train_rows": len(yt),
                       "cv_accuracy": round(cv, 4), "val_accuracy": round(val, 4)}, out, indent=1)
            out.write("\n")
        print(f"written: {args.out}")


if __name__ == "__main__":
    main()
