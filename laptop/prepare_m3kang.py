#!/usr/bin/env python3
"""Prepare M3Kang for the Arduino UNO Q, on your laptop.

M3Kang stores each problem as text plus an image. The text has the question
but not the five answer options: those only appear in the image. This script:

1. downloads the parquet shards you ask for from Hugging Face,
2. keeps the languages you ask for,
3. reads the options A to E from each image with OCR (RapidOCR, offline),
4. splits the problems into train and validation by problem ID, so a
   problem and its translations never land on both sides,
5. writes small JSONL files (no images) that you copy to the board.

Usage:
    python3 laptop/prepare_m3kang.py                      # English and Catalan
    python3 laptop/prepare_m3kang.py --languages eng,cat,esp
    python3 laptop/prepare_m3kang.py --val-years 2024     # hold out a whole year

Single image mode: read one or more problem images (PNG or JPEG) and print the
question and the options A to E as JSON, without touching the dataset:
    python3 laptop/prepare_m3kang.py --image problem.png
    python3 laptop/prepare_m3kang.py --image a.png b.jpg   # prints a JSON list

    {"file": "problem.png", "question": "...", "options": {"A": "12", ..., "E": "24"}}

The question is all the text above the options, one line per OCR row. The
options are {} when they are pictures or OCR misses a letter; the question is
then all the text in the image.
"""
import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
from collections import Counter

DATASET = "qualcomm/M3Kang"
SHARD = "data/{split}-{index:05d}-of-{total:05d}.parquet"
SHARDS = {"high_quality": 4, "standard": 10}
LETTERS = "ABCDE"


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--split", default="high_quality", choices=sorted(SHARDS))
    p.add_argument("--shards", default="0",
                   help="comma-separated shard numbers, or 'all'. Shard 0 of high_quality has "
                        "eng, cat, fra, esp, ind, deu, swh, vie, tur, zho, kor, arb, jpn, lit")
    p.add_argument("--parquet", nargs="*", help="use local parquet files instead of downloading")
    p.add_argument("--languages", default="eng,cat", help="M3Kang language codes, e.g. eng,cat,esp")
    p.add_argument("--val-fraction", type=float, default=0.15, help="share of problem IDs held out")
    p.add_argument("--val-years", default="", help="hold out these years instead, e.g. 2023,2024")
    p.add_argument("--out", default="data", help="output folder")
    p.add_argument("--no-ocr", action="store_true", help="skip OCR; options will be empty")
    p.add_argument("--save-images", action="store_true", help="also save problem images as PNG")
    p.add_argument("--limit", type=int, default=0, help="only process the first N rows (for testing)")
    p.add_argument("--image", nargs="+", metavar="PATH",
                   help="read these problem images and print their question and options as JSON")
    return p.parse_args()


def shard_paths(args):
    if args.parquet:
        return args.parquet
    from huggingface_hub import hf_hub_download
    total = SHARDS[args.split]
    indexes = range(total) if args.shards == "all" else [int(s) for s in args.shards.split(",")]
    paths = []
    for i in indexes:
        name = SHARD.format(split=args.split, index=i, total=total)
        print(f"Downloading {name} (cached after the first time)...", flush=True)
        paths.append(hf_hub_download(DATASET, name, repo_type="dataset"))
    return paths


# --- Reading the options from the image -------------------------------------
#
# OCR returns text boxes. The options are the last A..E sequence in reading
# order, usually on one row at the bottom. OCR noise we handle, seen on real
# M3Kang images: "A)21" (no space), "E16" (lost parenthesis), "C" and "13" in
# separate boxes, and ")768351" (parenthesis attached to the value).

MARKER = re.compile(r"^\s*([A-E])\s*([\)）\]:.]?)\s*(.*)$")


def reading_rows(boxes):
    """Group OCR boxes into rows (top to bottom), each sorted left to right."""
    items = []
    for box, text, _score in boxes:
        ys = [pt[1] for pt in box]
        xs = [pt[0] for pt in box]
        items.append({"x": min(xs), "y": (min(ys) + max(ys)) / 2, "h": max(ys) - min(ys), "text": text})
    items.sort(key=lambda it: it["y"])
    rows, current = [], []
    for it in items:
        if current and abs(it["y"] - current[-1]["y"]) > 0.6 * max(it["h"], current[-1]["h"]):
            rows.append(current)
            current = []
        current.append(it)
    if current:
        rows.append(current)
    return [sorted(row, key=lambda it: it["x"]) for row in rows]


def reading_order(boxes):
    """Sort OCR boxes into rows (top to bottom), then left to right."""
    return [it for row in reading_rows(boxes) for it in row]


def is_marker(text, letter, strict):
    m = MARKER.match(text)
    if not m or m.group(1) != letter:
        return None
    paren, rest = m.group(2), m.group(3)
    if paren:
        return rest
    if strict:
        return None
    # Without a parenthesis, only accept "C" alone or "E16"-style values,
    # so words such as "ADA" or figure labels with text are not markers.
    if rest == "" or re.match(r"^[-+−\d]", rest):
        return rest
    return None


def parse_options(boxes):
    """Return {"A": "12", ..., "E": "24"}, or {} when the options are not text."""
    return find_options(reading_order(boxes))[1]


def find_options(items):
    """Find the options in OCR items already in reading order.

    Returns (start, options): `start` is the index of the item where option A
    begins, or None when there is no A..E sequence; `options` is as in
    parse_options, so {} also when the five markers are there but the options
    are pictures.
    """
    starts = [i for i, it in enumerate(items) if is_marker(it["text"], "A", strict=True) is not None]
    for start in reversed(starts):  # the options are the last A..E sequence
        options, current, i = {}, None, start
        expected = iter(LETTERS)
        letter = next(expected)
        while i < len(items):
            text = items[i]["text"]
            rest = is_marker(text, letter, strict=(letter == "A")) if letter else None
            if rest is not None:
                current = letter
                options[current] = rest
                letter = next(expected, None)
            elif current:
                options[current] = (options[current] + " " + text).strip()
            i += 1
        if len(options) == 5:
            cleaned = {k: v.lstrip(")）] ").strip() for k, v in options.items()}
            if all(cleaned.values()):
                return start, cleaned
            return start, {}  # five markers, but the options are pictures
    return None, {}


OPTION_MARK = re.compile(r"^\s*([A-E])\s*[\)）]")  # "B)", "C) 12", "E)113"


def option_rows_start(rows):
    """Index of the first item of the option rows at the bottom, or None.

    For options the parser cannot read (pictures, garbled letters): a row counts
    as options when it has two or more "X)" markers, or nothing but markers.
    """
    first, index = None, sum(len(row) for row in rows)
    for row in reversed(rows):
        index -= len(row)
        marks = sum(1 for it in row if OPTION_MARK.match(it["text"]))
        if marks >= 2 or (marks and marks == len(row)):
            first = index
        else:
            break
    return first


def recover_options(items, start):
    """Options with exactly one "X)" lost by OCR, e.g. "B)9cm2 10cm2 D)11cm2".

    The second piece of the option before the missing letter becomes the
    missing option. Returns {} when the options do not fit that pattern.
    """
    parts, order = {}, []
    for it in items[start:]:
        m = OPTION_MARK.match(it["text"])
        if m and m.group(1) not in parts:
            order.append(m.group(1))
            rest = it["text"][m.end():].strip()
            parts[m.group(1)] = [rest] if rest else []
        elif order:
            parts[order[-1]].append(it["text"])
    missing = [letter for letter in LETTERS if letter not in parts]
    if order != sorted(order) or len(missing) != 1 or missing[0] == "A":
        return {}
    before = LETTERS[LETTERS.index(missing[0]) - 1]
    if len(parts.get(before, [])) != 2:
        return {}
    parts[missing[0]] = [parts[before].pop()]
    options = {letter: " ".join(parts[letter]).strip() for letter in LETTERS}
    return options if all(options.values()) else {}


def read_problem(image, ocr):
    """Read a problem image (PNG or JPEG bytes) into its question and options.

    Returns {"question": "...", "options": {"A": ..., "E": ...}}. The question is
    the text above the options, one line per OCR row; when no options are found
    it is all the text in the image.
    """
    # use_cls=False: the angle classifier turns long lines that are already
    # straight, and they get lost (often the first line of the question).
    boxes, _ = ocr(enhance(ocr, ocr.load_img(image)), use_cls=False)
    rows = reading_rows(boxes or [])
    items = [it for row in rows for it in row]
    start, options = find_options(items)
    if start is None:  # options as pictures or a letter misread: cut before them
        starts = [i for i, it in enumerate(items) if is_marker(it["text"], "A", strict=True) is not None]
        cuts = [i for i in (starts[-1] if starts else None, option_rows_start(rows)) if i is not None]
        start = min(cuts) if cuts else None
        if starts:
            options = recover_options(items, starts[-1])
    cut = start if start is not None else len(items)
    lines, seen = [], 0
    for row in rows:
        words = [it["text"] for it in row[:max(cut - seen, 0)]]
        seen += len(row)
        if words:
            lines.append(" ".join(words).strip())
        if seen >= cut:
            break
    return {"question": "\n".join(line for line in lines if line), "options": options}


LINE_HEIGHT = 48  # pixels per text line that RapidOCR reads best
MAX_ZOOM = 4.0
MAX_SIDE = 4000


def enhance(ocr, pixels):
    """Enlarge the image until text lines are ~48 px high, then sharpen it.

    At M3Kang's size (lines of ~32 px) RapidOCR glues the words together
    ("Lasumadedosnombres"). Same recipe as scripts/ocr_server.py: find the text
    first (detector only) to measure the line height, then zoom and sharpen.
    """
    import cv2  # comes with rapidocr_onnxruntime
    found, _ = ocr(pixels, use_det=True, use_cls=False, use_rec=False)
    if not found:
        return pixels
    side = lambda a, b: ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
    heights = sorted(min(side(box[0], box[3]), side(box[0], box[1])) for box in found)
    height = max(heights[len(heights) // 2], 1.0)  # the median line
    zoom = min(LINE_HEIGHT / height, MAX_ZOOM, MAX_SIDE / max(pixels.shape[:2]))
    if zoom > 1.1:
        pixels = cv2.resize(pixels, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_LANCZOS4)
        height *= zoom
    soft = cv2.GaussianBlur(pixels, (0, 0), height / 24)
    return cv2.addWeighted(pixels, 2.5, soft, -1.5, 0)


def read_images(paths):
    """Print the question and options of each image as JSON (--image mode)."""
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR(max_side_len=MAX_SIDE)  # by default it shrinks to 2,000 px and undoes the zoom
    results = []
    for path in paths:
        try:
            with open(path, "rb") as f:
                image = f.read()
        except OSError as error:  # report it and go on with the other images
            results.append({"file": path, "error": str(error)})
            continue
        try:
            results.append({"file": path, **read_problem(image, ocr)})
        except Exception as error:  # not an image RapidOCR can open
            results.append({"file": path, "error": f"{type(error).__name__}: {error}"})
    out = results[0] if len(results) == 1 else results
    print(json.dumps(out, ensure_ascii=False, indent=2))


def main():
    args = parse_args()
    if args.image:
        return read_images(args.image)
    import pyarrow.parquet as pq

    languages = set(args.languages.split(","))
    val_years = set(y for y in args.val_years.split(",") if y)
    os.makedirs(args.out, exist_ok=True)
    if args.save_images:
        os.makedirs(os.path.join(args.out, "images"), exist_ok=True)

    ocr = None
    if not args.no_ocr:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR()

    cache_path = os.path.join(args.out, ".ocr_cache.jsonl")
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            for line in f:
                row = json.loads(line)
                cache[row["key"]] = row["options"]
    cache_file = open(cache_path, "a")

    rows = []
    t0 = time.time()
    for path in shard_paths(args):
        table = pq.read_table(path, columns=["language"])
        wanted = [i for i, lang in enumerate(table.column(0).to_pylist()) if lang in languages]
        if not wanted:
            continue
        full = pq.read_table(path).take(wanted)
        for i in range(full.num_rows):
            if args.limit and len(rows) >= args.limit:
                break
            r = {c: full.column(c)[i].as_py() for c in ("id", "language", "level", "text_only", "label", "text")}
            key = f"{r['id']}|{r['language']}"
            image = full.column("image")[i].as_py()["bytes"]
            if args.save_images:
                with open(os.path.join(args.out, "images", key.replace("|", "_") + ".png"), "wb") as f:
                    f.write(image)
            if key in cache:
                options = cache[key]
            elif ocr:
                boxes, _ = ocr(image)
                options = parse_options(boxes or [])
                cache[key] = options
                cache_file.write(json.dumps({"key": key, "options": options}, ensure_ascii=False) + "\n")
            else:
                options = {}
            year = r["id"].split("_")[1]
            if val_years:
                split = "val" if year in val_years else "train"
            else:
                bucket = int(hashlib.sha256(r["id"].encode()).hexdigest(), 16) % 1000
                split = "val" if bucket < args.val_fraction * 1000 else "train"
            rows.append({
                "id": r["id"], "language": r["language"], "level": r["level"], "year": int(year),
                "text_only": r["text_only"], "text": r["text"].strip(), "options": options,
                "label": r["label"], "split": split,
            })
            if len(rows) % 100 == 0:
                rate = len(rows) / (time.time() - t0)
                print(f"  {len(rows)} rows, {rate:.1f} rows/s", flush=True)
    cache_file.close()

    for split in ("train", "val"):
        out = os.path.join(args.out, f"{split}.jsonl")
        with open(out, "w") as f:
            for r in rows:
                if r["split"] == split:
                    f.write(json.dumps({k: v for k, v in r.items() if k != "split"}, ensure_ascii=False) + "\n")

    report(rows, args.out)


def report(rows, out):
    if not rows:
        sys.exit("No rows matched. Check --languages and --shards.")
    by = Counter((r["split"], r["language"]) for r in rows)
    with_options = sum(1 for r in rows if r["options"])
    text_only = [r for r in rows if r["text_only"]]
    labels = Counter(r["label"] for r in rows if r["split"] == "train")
    top, count = labels.most_common(1)[0]
    print()
    print(f"Wrote {out}/train.jsonl and {out}/val.jsonl")
    for (split, lang), n in sorted(by.items()):
        print(f"  {split:5} {lang}: {n}")
    print(f"Options read from the image: {with_options}/{len(rows)} ({100 * with_options / len(rows):.0f}%)")
    if text_only:
        ok = sum(1 for r in text_only if r["options"])
        print(f"  of which text-only problems: {ok}/{len(text_only)} ({100 * ok / len(text_only):.0f}%)")
    print(f"Most common answer in train: {top} ({100 * count / sum(labels.values()):.1f}%). "
          f"Always answering {top} is the floor to beat.")


if __name__ == "__main__":
    main()
