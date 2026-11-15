# Mathey — a math mentor that never gives you the answer

**Datathon FME 2026 · Qualcomm challenge "Math on the Edge"** · runs entirely on an Arduino UNO Q, offline.

> ⚠️ **Draft (14 Nov 2026, afternoon).** Sections marked `TODO` get their final
> numbers on Sunday morning. Every number in this README must come from a logged
> run; the team log is the "Registre de resultats".

<!-- TODO: photo or 20-second GIF of the board with the LED matrix and the web page -->

Mathey helps students aged 10–14 learn to reason through Kangaroo
competition problems. When a student gets stuck, it never hands over the answer:
it asks how they thought about it, replies with one guiding question, and offers a
ladder of help — a strategy, the key fact, an easier "sibling" problem, the first
step — before the full solution, which the student has to ask for explicitly.
Everything runs on the board in the classroom: no internet, no accounts, and no
student data ever leaves the device.

## Why

- Math proficiency in Catalonia is falling in international assessments.
- A teacher with 25 students cannot sit next to each one when they get stuck.
- Chat AIs solve homework instead of teaching to reason, and student data of
  minors should not leave the school.
- The Kangaroo competition is huge (over 68,000 participants in Catalonia in 2024,
  per the M3Kang paper), and its problems are designed with traps: each wrong
  option encodes a typical mistake.

## What it does

| For | What |
|---|---|
| Student | Practice at their Elo; answer A–E; the LED matrix shows ✓ when the answer is right and ✗ when it is wrong |
| Student | "How did you think about it?" → if their sentence describes the typical mistake behind the option they chose, the prepared feedback arrives **instantly, without the model**; otherwise one Socratic question from the **on-board model** |
| Student | Five-rung help ladder; the solution only on explicit request |
| Student | Easy-reading mode (dyslexia): short sentences, one idea per line, large type |
| Student | Adaptive path by Elo: every first answer nudges the problem's rating and re-estimates the student's from all their answers (recent ones weigh more); the next problem is an unseen one near the student's Elo, weakest topic first |
| Student | **Bring your own problem** (chat): paste or snap a photo of homework → `laptop/read_image.py` reads the question and options A–E on the board and that text becomes the prompt → a Kangaroo problem with the same idea → the on-board model works through it step by step, streamed and clearly labelled "may be wrong, check each step" |

## How we use M3Kang

M3Kang (1,747 Kangaroo problems, 8 levels, 108 languages) is not a lookup table for
the model: **it is the mentor.**

1. **Verified teaching content per problem.** For the 517 problems of levels 0–3
   (grades 5–8), AI agents solved each problem **from its image without seeing the
   official answer**, then wrote a topic, the key idea, three graded hints, a
   step-by-step solution, the typical mistake behind each wrong option, and an
   easy-reading version. Content enters the mentor only if the agent's answer
   matches the official one: **509 of 517 verified (98.5%)**.
2. **"Sibling" problems.** Problems are linked by similarity of *method* (key idea +
   solution), not of story, so an easier problem with the same idea is one click away.
3. **Traps as data.** Kangaroo distractors become feedback for the student: each
   wrong option comes with the typical mistake behind it.
4. **Topics for error analysis.** All 1,747 problems carry one of five topics.
5. **We found errors in M3Kang's answer key.** Of the 8 problems where the blind
   solution disagreed with the official answer, 6 come from the same exam (level 2,
   2017). We checked two by hand and the official answer is wrong in both
   (problem 2: the sum is 9, option D, not B; problem 14: the key is 284, option E,
   not B). Disagreeing problems are simply left out of the mentor.

M3Kang is licensed for research use only: no problem text, image, or derived
content is in this repository.

## Architecture

```
 Laptop (screen only)                 Arduino UNO Q (4 GB)
 browser ──USB (adb forward)──►  Linux (Qualcomm QRB2210)
                                  ├─ App Lab app (port 7000)
                                  │   ├─ web_ui: static Next.js export
                                  │   ├─ /api/*: the mentor (Python, stdlib only)
                                  │   └─ SQLite: problem bank + student state
                                  ├─ llama-server :8081  Qwen3.5 0.8B (Socratic question, live)
                                  └─ llama-server :8082  bge-small (embeddings)
                                 Microcontroller (STM32) ── Bridge ── 8×13 LED matrix
```

- `web/` — Next.js static export (no Node on the board): landing at `/`, the app at
  `/app/` (Kangaroo challenge, chat) and `/placa/`. Without a board it switches to a
  demo mode with made-up problems, so it can be browsed and designed anywhere. Light "liquid glass"
  design with local Geist fonts; see [web/README.md](web/README.md).
- `mentor/` — the mentor logic: API routes, adaptive engine, help ladder, leak
  filter, similarity, LED frames, model client.
- `app/` — the Arduino App Lab app (Python adapter + LED sketch).
- `scripts/` — `build_bank.py` (build and verify the bank), `dev_server.py`
  (laptop server), `deploy_board.sh` (one-command deploy), `local_amb_placa.sh`
  (web and mentor on the laptop, the board's model through a self-healing SSH tunnel),
  `measure_socratic.py`, `measure_router.py`, `simulate_students.py`.
- `tests/` — unit tests for the leak filter and the no-model router
  (`python -m unittest discover tests`).
- `predict.py`, `copilot/`, `eval.py` — the official Reason entry point, kept
  independent of the mentor.

### Why the on-board model only asks questions

Alone, Qwen3.5 0.8B answers 22.5% of Kangaroo problems correctly — below the 25%
of always answering D (organizers' baseline). A model that cannot solve the problem
cannot explain it. With the verified solution in its context, its job changes from
*solving* to *asking a question about a known path*, which a small model can do.
Every model output passes a code filter and, if rejected or late, the mentor falls
back to the prepared typical-mistake feedback. The filter blocks the correct letter
in any form ("option C", "la C", "(C)"), the correct value also when written as a
word ("quatre", "veintidós", "twenty-two"), and, for live model output, the correct
value even when it also appears in the statement (`strict` mode).

### Using the model only when it adds something

The board serves one request at a time at ~5–6 tokens/s, so every call costs
seconds. Before asking the model, a no-model router (`mentor/router.py`) compares
the student's sentence with the trap of the option they chose — words, 4-letter
chunks, the operation behind the mistake ("added instead of subtracting") and the
numbers. If it clearly describes that trap, and no other, the verified feedback is
shown at once and the model stays free for the answers that need it. A wrong match
only ever shows verified content, so the threshold favours precision.

## Results

| Measure | Value | How |
|---|---|---|
| `predict.py` accuracy (hidden-test proxy: validation set) | `TODO` vs 22.5% baseline and 25% always-D | `eval.py --limit 0` on the board |
| Agent solutions matching the official answer | 509 / 517 (98.5%) | blind solve from the image, compared in code |
| Hints blocked by the leak filter | 12 of 1,527 (0.8%) with the first filter; none shown. `TODO`: re-measure with the current filter | `mentor/filters.py` on every hint (`scripts/build_bank.py`) |
| Leak filter test cases | 12 / 12 pass; the first filter let through 15 of the leaks we tested | `python -m unittest tests.test_filters` |
| "How did you think?" answered instantly, without the model | 44.8% of explanations; precision 97.7%, recall 70.0% (threshold 0.40) on 96 **invented** student sentences. `TODO`: re-measure on real students | `scripts/measure_router.py` on `eval/router_cases.jsonl` |
| Easy-reading (dyslexia) versions | words per sentence 13.2 → 7.8; long words per sentence 0.79 → 0.27; all statement numbers kept in 507/509 | `scripts/readability.py` |
| Socratic question latency on the board | `TODO` cold / warm | `scripts/measure_socratic.py` |
| Socratic question quality | `TODO` useful / useless / misleading of 30 | judged by hand |
| Adaptive engine convergence (Elo) | real bank (509 verified problems, Elo 800–1580), 10 profiles (true Elo 850–1450, claiming 5th or 8th grade): mean error of the last-10 Elo 55 points; worst 120 (a 1450 student who claims 5th grade); each profile stays within ±100 of its true Elo from problem 8–28 | `scripts/simulate_students.py --problems 30 --seeds 5` (5 students × 30 problems per profile) |
| RAM with everything running | `TODO` | `free -m` on the board |

## Error analysis

`TODO`: accuracy of `predict.py` by topic, language and level (tables), and ten
wrong answers explained one by one.

## What didn't work

- Letting the 0.8B model reason before answering (organizers: 17.5%, slower).
- Similarity on problem statements: it matched stories ("books", "blocks"), not
  mathematical ideas; we switched to similarity of the solution method.
- Our first leak filter only caught "option C", "(C)" and digits: "la C",
  answers written as words and correct values that also appear in the statement
  slipped through (15 of the cases we tested). We added letter and number-word
  detection and a strict mode for live model output, with tests.
- Sending every "how did you think?" sentence to the model: often the sentence
  just describes the trap of the chosen option, which the prepared content already
  answers, and the student waited ~10 s for nothing. A no-model router now handles
  those instantly.
- `TODO`

## Reproduce it

1. Set up the board with steps 0–8 of the
   [organizers' guide](https://github.com/mpous/datathon-UPC-maths-qualcomm-arduino-unoq).
2. Prepare M3Kang on the laptop (step 9 of the guide; `--save-images`).
3. `TODO`: generate the teaching content (agents) — document the exact procedure.
4. `python3 scripts/build_bank.py` → `data/mentor.db`.
5. Expose the models to the app container: see [app/README.md](app/README.md) (plan A).
6. `scripts/deploy_board.sh` (USB) or `BOARD_SSH=arduino@<ip> scripts/deploy_board.sh`.
7. `adb forward tcp:7070 tcp:7000` and open `http://127.0.0.1:7070` (landing; students start at `/app/`).

## Team

Subils · Alex · Dídac · David — `TODO`: roles and links.

## Credits and licenses

- **M3Kang**: Torres-Camps et al., 2026, [arXiv:2601.16218](https://arxiv.org/abs/2601.16218).
  Research use only; [dataset card](https://huggingface.co/datasets/qualcomm/M3Kang).
- **llama.cpp** (MIT), **Qwen3.5 0.8B** (Qwen team; GGUF by bartowski),
  **bge-small-en-v1.5** (BAAI; GGUF by CompendiumLabs), **RapidOCR** (Apache 2.0).
- Organizers' starter kit: [mpous/datathon-UPC-maths-qualcomm-arduino-unoq](https://github.com/mpous/datathon-UPC-maths-qualcomm-arduino-unoq).
- Our code: `TODO` license (MIT proposed).
