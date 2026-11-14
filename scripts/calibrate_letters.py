#!/usr/bin/env python3
"""Calibrate the letter bias of the model for predict.py (team addition).

    python3 scripts/calibrate_letters.py --limit 200          # on the board, models running
    python3 scripts/calibrate_letters.py --limit 200 --languages eng

The model answers some letters far too often (organizers: 21 D and 14 A out of
40). This script asks it for the log probability of each letter on TRAINING
problems only (never validation), and writes results/letter_bias.json with

    bias(L) = mean logprob of L over the problems  -  log(share of L in the labels)

predict.py then picks argmax(logprob(L) - bias(L)) when config.env has
LETTER_BIAS_FILE=results/letter_bias.json. Measure the change with
`python3 eval.py --limit 50 --name calibrated` against the baseline on the same
50 validation problems before keeping it.

It also prints the accuracy on these training problems with and without the
correction (in-sample: only a sanity check, not the number to report).
"""
import argparse
import json
import math
import os
import random
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from copilot import llm  # noqa: E402

LETTERS = "ABCDE"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", default=os.path.join(ROOT, "data", "train.jsonl"))
    p.add_argument("--limit", type=int, default=200)
    p.add_argument("--languages", default="", help="e.g. eng,cat")
    p.add_argument("--only-with-options", action="store_true", default=True)
    p.add_argument("--out", default=os.path.join(ROOT, "results", "letter_bias.json"))
    args = p.parse_args()

    with open(args.input) as f:
        problems = [json.loads(line) for line in f if line.strip()]
    langs = set(filter(None, args.languages.split(",")))
    problems = [x for x in problems if (not langs or x["language"] in langs)
                and (x.get("options") or not args.only_with_options)]
    random.Random(7).shuffle(problems)
    problems = problems[:args.limit]

    rows = []
    for n, problem in enumerate(problems, 1):
        try:
            letter, timings = llm.answer_letter(problem, timeout=60, want_logprobs=True)
        except OSError as error:
            print(f"[{n}] {problem['id']}: {error}")
            continue
        scores = timings.get("letter_logprobs", {})
        rows.append((problem["label"], letter, scores))
        print(f"[{n}/{len(problems)}] {problem['id']} label {problem['label']} greedy {letter} "
              f"letters seen {''.join(sorted(scores))}", flush=True)

    usable = [r for r in rows if len(r[2]) >= 2]
    if not usable:
        sys.exit("No letter log probabilities came back. Check that this llama-server version "
                 "returns logprobs/top_logprobs or n_probs with a grammar.")
    floor = min(v for _, _, s in usable for v in s.values()) - 1.0
    mean = {L: sum(s.get(L, floor) for _, _, s in usable) / len(usable) for L in LETTERS}
    labels = Counter(label for label, _, _ in rows)
    prior = {L: (labels[L] + 1) / (len(rows) + 5) for L in LETTERS}
    bias = {L: mean[L] - math.log(prior[L]) for L in LETTERS}

    def pick(scores):
        return max(scores, key=lambda k: scores[k] - bias[k])

    greedy_ok = sum(label == letter for label, letter, _ in rows)
    calib_ok = sum(label == (pick(s) if len(s) >= 2 else letter) for label, letter, s in rows)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({"bias": bias, "mean_logprob": mean, "prior": prior, "n": len(rows),
                   "usable": len(usable), "source": os.path.basename(args.input)}, f, indent=2)
    print(f"\nWrote {args.out}")
    print(f"Greedy letters:     {dict(Counter(letter for _, letter, _ in rows))}")
    print(f"Calibrated letters: {dict(Counter(pick(s) if len(s) >= 2 else l for _, l, s in rows))}")
    print(f"True labels:        {dict(labels)}")
    print(f"In-sample accuracy: greedy {greedy_ok}/{len(rows)}, calibrated {calib_ok}/{len(rows)} "
          f"(sanity check only; measure on validation with eval.py)")


if __name__ == "__main__":
    main()
