#!/usr/bin/env python3
"""Mesura el lector d'imatges (scripts/ocr_server.py) amb les imatges de M3Kang.

    python3 scripts/eval_ocr.py                          # 60 imatges en català, nivells 0-3
    python3 scripts/eval_ocr.py --n 100 --levels 0-7 --lang eng
    research/qualcomm-repo/.venv/bin/python scripts/eval_ocr.py --degrade        # foto de mòbil simulada
    python3 scripts/eval_ocr.py --url http://127.0.0.1:8084 --db ... --images ...   # a la placa

Tria N problemes del banc amb una llavor fixa, envia la imatge de cada un al
servei (amb mentor/ocr.py, el mateix client que fa servir el mentor) i compara el
text llegit amb l'enunciat del dataset:

- **Paraules**: quantes paraules de l'enunciat surten al text llegit. La imatge
  també porta les opcions i de vegades una figura, i l'enunciat del dataset no:
  per això es mesura què es recupera de l'enunciat, no què sobra.
  Es dona exacte (amb accents) i sense comptar accents ni ela geminada: la
  diferència és el que es perd en diacrítics.
- **En ordre**: la part de l'enunciat que surt en el mateix ordre (subseqüència
  comuna més llarga). Baixa quan les línies es barregen amb una figura.
- **Números**: quants números de l'enunciat surten al text llegit. En
  matemàtiques són el que més importa. Compte: un número perdut de l'enunciat
  que també surti a les opcions compta com a trobat; és un sostre.
- **Símbols**: × ÷ + = % € ° < > √ ^ de l'enunciat que surten al text llegit.
- **Segons per imatge**: el que espera el mentor, de la petició a la resposta.

Amb --degrade la imatge s'espatlla abans d'enviar-la com ho faria una foto de
mòbil (més petita, torta, desenfocada, amb ombra, soroll i compressió JPEG). Cal
cv2 i numpy: el python3 del sistema no els té; el virtualenv dels organitzadors, sí.

Només imprimeix números agregats: cap text de M3Kang. Desa els mateixos números
(i els de cada imatge, per identificador) a results/ocr-<hora>.json, que no es
puja a GitHub. Biblioteca estàndard, més cv2 i numpy només per a --degrade.
"""
import argparse
import hashlib
import json
import math
import os
import random
import re
import sqlite3
import statistics
import subprocess
import sys
import time
import unicodedata
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mentor import ocr  # noqa: E402

_WORD = re.compile(r"[^\W\d_]+(?:·[^\W\d_]+)*")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
SYMBOLS = "×÷+=%€°<>√^"

# Una foto de mòbil, de més bona a més dolenta. Les imatges de M3Kang fan 1.653
# píxels d'ample amb línies d'uns 31 píxels d'alt: «escala 0,6» vol dir línies de 19.
DEGRADE = {
    "lleu": {"scale": 0.8, "angle": 1.5, "blur": 0.6, "shadow": 0.9, "noise": 2.0, "quality": 80},
    "mitja": {"scale": 0.6, "angle": 3.0, "blur": 1.0, "shadow": 0.8, "noise": 4.0, "quality": 60},
    "fort": {"scale": 0.45, "angle": 6.0, "blur": 1.5, "shadow": 0.65, "noise": 7.0, "quality": 40},
}


# --- Comparar textos ---------------------------------------------------------------

def fold(text):
    """Sense accents ni ela geminada: separa «s'ha perdut la paraula» de «s'ha perdut l'accent»."""
    text = re.sub(r"l[·.•∙‧-]l", "ll", text)
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def words(text, folded=False):
    text = unicodedata.normalize("NFC", text or "").lower()
    return _WORD.findall(fold(text) if folded else text)


def numbers(text):
    return [n.replace(",", ".") for n in _NUMBER.findall(text or "")]


def found(wanted, have):
    """Quants elements de `wanted` són a `have`, comptant repeticions."""
    stock = Counter(have)
    return sum(min(count, stock[item]) for item, count in Counter(wanted).items())


def in_order(wanted, have):
    """Llargada de la subseqüència comuna més llarga."""
    previous = [0] * (len(have) + 1)
    for a in wanted:
        current = [0]
        for j, b in enumerate(have, 1):
            current.append(previous[j - 1] + 1 if a == b else max(previous[j], current[j - 1]))
        previous = current
    return previous[-1]


def compare(statement, read):
    """Els comptadors d'una imatge: enunciat del dataset contra text llegit."""
    exact, exact_read = words(statement), words(read)
    plain, plain_read = words(statement, True), words(read, True)
    accented = [w for w in exact if fold(w) != w]
    wanted_symbols = [ch for ch in statement if ch in SYMBOLS]
    return {
        "words": len(exact), "words_exact": found(exact, exact_read),
        "words_plain": found(plain, plain_read), "words_order": in_order(plain, plain_read),
        "accented": len(accented), "accented_exact": found(accented, exact_read),
        "accented_plain": found([fold(w) for w in accented], plain_read),
        "numbers": len(numbers(statement)), "numbers_found": found(numbers(statement), numbers(read)),
        "symbols": len(wanted_symbols), "symbols_found": found(wanted_symbols, [ch for ch in read if ch in SYMBOLS]),
    }


# --- Espatllar la imatge com una foto de mòbil ---------------------------------------

def degrade(data, params, rng):
    """PNG net -> JPEG com el d'una foto: més petit, tort, desenfocat, amb ombra i soroll."""
    import cv2
    import numpy as np

    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("cv2 no ha pogut obrir la imatge")
    if image.dtype != np.uint8:
        image = (image / 257).astype(np.uint8)
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.shape[2] == 4:  # la transparència, sobre blanc
        alpha = image[:, :, 3:4].astype(np.float32) / 255
        image = (image[:, :, :3] * alpha + 255 * (1 - alpha)).astype(np.uint8)
    # 1. Torta: el full no queda mai recte. El fons que apareix és gris clar, com una taula.
    height, width = image.shape[:2]
    angle = rng.choice((-1, 1)) * rng.uniform(0.5, 1.0) * params["angle"]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    cos, sin = abs(matrix[0, 0]), abs(matrix[0, 1])
    new_width, new_height = int(width * cos + height * sin) + 1, int(width * sin + height * cos) + 1
    matrix[0, 2] += new_width / 2 - width / 2
    matrix[1, 2] += new_height / 2 - height / 2
    image = cv2.warpAffine(image, matrix, (new_width, new_height), flags=cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=(225, 225, 225))
    # 2. Més petita: el text ocupa menys píxels que a la imatge neta
    image = cv2.resize(image, None, fx=params["scale"], fy=params["scale"], interpolation=cv2.INTER_AREA)
    # 3. Desenfocada
    if params["blur"]:
        image = cv2.GaussianBlur(image, (0, 0), params["blur"])
    # 4. Ombra d'un costat a l'altre i soroll del sensor
    height, width = image.shape[:2]
    direction = rng.uniform(0, 2 * math.pi)
    ramp = (np.linspace(0, 1, width, dtype=np.float32)[None, :] * math.cos(direction)
            + np.linspace(0, 1, height, dtype=np.float32)[:, None] * math.sin(direction))
    ramp = (ramp - ramp.min()) / max(float(ramp.max() - ramp.min()), 1e-6)
    light = 1 - (1 - params["shadow"]) * ramp
    noise = np.random.default_rng(rng.getrandbits(32)).normal(0, params["noise"], image.shape)
    image = np.clip(image.astype(np.float32) * light[:, :, None] + noise, 0, 255).astype(np.uint8)
    # 5. JPEG
    done, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, params["quality"]])
    if not done:
        raise ValueError("cv2 no ha pogut escriure el JPEG")
    return encoded.tobytes()


# --- La mostra ---------------------------------------------------------------------

def parse_levels(text):
    levels = set()
    for part in text.split(","):
        low, _, high = part.strip().partition("-")
        levels.update(range(int(low), int(high or low) + 1))
    return sorted(levels)


def sample(db_path, images, lang, levels, n, seed):
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    marks = ",".join("?" * len(levels))
    rows = db.execute(f"SELECT id, level, text_only, text FROM problems WHERE lang = ? AND level IN ({marks}) "
                      "ORDER BY id", [lang] + levels).fetchall()
    db.close()
    rows = [row for row in rows if os.path.isfile(os.path.join(images, f"{row[0]}_{lang}.png"))]
    if not rows:
        sys.exit(f"No hi ha cap problema «{lang}» dels nivells {levels} amb imatge a {images}.")
    chosen = random.Random(seed).sample(rows, min(n, len(rows)))
    return sorted(chosen), len(rows)


def commit():
    """El commit del repositori; amb «+canvis» si el lector o aquest script en tenen de no desats."""
    def git(*args):
        done = subprocess.run(["git", "-C", ROOT] + list(args), stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, timeout=5)
        return done.stdout.decode().strip()
    try:
        head = git("rev-parse", "--short", "HEAD")
        dirty = git("status", "--porcelain", "--", "scripts/ocr_server.py", "scripts/eval_ocr.py", "mentor/ocr.py")
    except (OSError, subprocess.SubprocessError):
        return None
    return (head + ("+canvis" if dirty else "")) or None


def percent(part, whole):
    return f"{100 * part / whole:5.1f} %" if whole else "    — "


def summary(rows):
    """Suma els comptadors d'unes quantes imatges."""
    total = Counter()
    for row in rows:
        total.update({key: value for key, value in row.items()
                      if isinstance(value, int) and not isinstance(value, bool) and key != "level"})
    return total


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--n", type=int, default=60, help="quantes imatges")
    p.add_argument("--levels", default="0-3", help="nivells del Cangur, p. ex. 0-3 o 0,2,5")
    p.add_argument("--lang", default="cat", choices=["cat", "eng"])
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--degrade", nargs="?", const="mitja", choices=sorted(DEGRADE),
                   help="simula una foto de mòbil abans d'enviar (per defecte «mitja»); cal cv2 i numpy")
    p.add_argument("--url", default=ocr.OCR_URL, help="on escolta el servei")
    p.add_argument("--timeout", type=float, default=ocr.OCR_TIMEOUT)
    p.add_argument("--db", default=os.environ.get("MENTOR_DB", os.path.join(ROOT, "data", "mentor.db")))
    p.add_argument("--images", default=os.environ.get(
        "MENTOR_IMAGES", os.path.join(ROOT, "research", "qualcomm-repo", "data", "images")))
    p.add_argument("--detail", action="store_true", help="una línia per imatge (identificador i números, mai text)")
    p.add_argument("--no-save", action="store_true", help="no desis results/ocr-<hora>.json")
    args = p.parse_args()

    if args.degrade:
        try:
            import cv2  # noqa: F401
            import numpy  # noqa: F401
        except ImportError:
            sys.exit("--degrade NO ES POT FER: aquest Python no té cv2 i numpy.\n"
                     "Executa'l amb el virtualenv dels organitzadors:\n"
                     "  research/qualcomm-repo/.venv/bin/python scripts/eval_ocr.py --degrade ...")
    info = ocr.health(timeout=3, url=args.url)
    if not info or info.get("status") != "ok":
        sys.exit(f"El lector d'imatges no respon a {args.url}. Engega scripts/ocr_server.py o posa --url.")
    if not os.path.isfile(args.db):
        sys.exit(f"No trobo el banc {args.db} (scripts/build_bank.py el construeix).")

    levels = parse_levels(args.levels)
    chosen, available = sample(args.db, args.images, args.lang, levels, args.n, args.seed)
    fingerprint = hashlib.sha1(",".join(row[0] for row in chosen).encode()).hexdigest()[:10]
    params = DEGRADE[args.degrade] if args.degrade else None

    rows, failures = [], []
    for k, (pid, level, text_only, statement) in enumerate(chosen, 1):
        with open(os.path.join(args.images, f"{pid}_{args.lang}.png"), "rb") as f:
            image = f.read()
        if params:
            image = degrade(image, params, random.Random(f"{args.seed}:{pid}"))
        try:
            result = ocr.read_image(image, args.lang, url=args.url, timeout=args.timeout)
        except ocr.OcrUnavailable as error:
            failures.append({"id": pid, "status": error.status, "error": str(error)})
            if args.detail:
                print(f"[{k:3}/{len(chosen)}] {pid:16} ERROR {error.status} {error}")
            continue
        row = {"id": pid, "level": level, "text_only": bool(text_only), "seconds": result["seconds"],
               "bytes": len(image), "chars": len(result["text"]), "lines": result["lines"]}
        row.update(compare(statement, result["text"]))
        rows.append(row)
        if args.detail:
            print(f"[{k:3}/{len(chosen)}] {pid:16} {'text  ' if text_only else 'figura'} "
                  f"paraules {percent(row['words_exact'], row['words'])} exactes, "
                  f"{percent(row['words_plain'], row['words'])} sense accents, "
                  f"{percent(row['words_order'], row['words'])} en ordre · "
                  f"números {row['numbers_found']}/{row['numbers']} · {row['seconds']:.2f} s")
    if not rows:
        sys.exit(f"Cap imatge llegida ({len(failures)} errors; el primer: {failures[0]['error']}).")

    total = summary(rows)
    seconds = [row["seconds"] for row in rows]
    per_image = [row["words_plain"] / row["words"] for row in rows if row["words"]]
    with_numbers = [row for row in rows if row["numbers"]]
    all_numbers = sum(row["numbers_found"] == row["numbers"] for row in with_numbers)
    empty = sum(row["chars"] == 0 for row in rows)
    figure = sum(not row["text_only"] for row in rows)

    print(f"Lector: {args.url} · motor {info.get('engine')}"
          + (f" · idiomes {'+'.join(info['languages'])}" if info.get("languages") else ""))
    print(f"Mostra: {len(chosen)} imatges de {available} ({args.lang}, nivells {args.levels}, llavor {args.seed}, "
          f"empremta {fingerprint}); {figure} amb figura i {len(rows) - figure} només text")
    if params:
        print(f"Imatges: foto simulada «{args.degrade}»: escala {params['scale']}, gir fins a {params['angle']}°, "
              f"desenfocament σ {params['blur']} px, ombra fins a {params['shadow']}, "
              f"soroll σ {params['noise']}, JPEG {params['quality']}")
    else:
        print("Imatges: netes, tal com són al dataset")
    print()
    print("Paraules de l'enunciat que surten al text llegit")
    print(f"  exactes, amb accents          {percent(total['words_exact'], total['words'])}")
    print(f"  sense comptar accents         {percent(total['words_plain'], total['words'])}"
          f"   (per imatge: mitjana {100 * statistics.mean(per_image):.1f} %, pitjor {100 * min(per_image):.1f} %)")
    print(f"  en ordre, sense accents       {percent(total['words_order'], total['words'])}")
    print(f"  les {total['accented']} amb accent o ela geminada: {percent(total['accented_exact'], total['accented']).strip()} "
          f"exactes, {percent(total['accented_plain'], total['accented']).strip()} sense comptar l'accent")
    print(f"Números de l'enunciat           {percent(total['numbers_found'], total['numbers'])}"
          f"   ({total['numbers']} números en {len(with_numbers)} imatges; "
          f"imatges amb tots els números: {percent(all_numbers, len(with_numbers)).strip()})")
    print(f"Símbols ({' '.join(SYMBOLS)})   {total['symbols_found']} de {total['symbols']}")
    print(f"Segons per imatge               mitjana {statistics.mean(seconds):.2f} · "
          f"mediana {statistics.median(seconds):.2f} · pitjor {max(seconds):.2f}")
    print(f"Lectures fallides: {len(failures)} · text buit: {empty}")
    for label, flag in (("només text", True), ("amb figura", False)):
        part = [row for row in rows if row["text_only"] == flag]
        if part:
            t = summary(part)
            print(f"  {label} ({len(part)}): paraules {percent(t['words_plain'], t['words']).strip()} sense accents, "
                  f"{percent(t['words_order'], t['words']).strip()} en ordre, "
                  f"números {percent(t['numbers_found'], t['numbers']).strip()}")

    if not args.no_save:
        os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
        path = os.path.join(ROOT, "results", f"ocr-{time.strftime('%Y%m%d-%H%M%S')}.json")
        record = {
            "when": time.strftime("%Y-%m-%d %H:%M:%S"), "commit": commit(), "command": " ".join(sys.argv),
            "python": sys.version.split()[0], "service": info, "url": args.url, "lang": args.lang,
            "levels": levels, "seed": args.seed, "n": len(chosen), "fingerprint": fingerprint,
            "degrade": args.degrade, "degrade_params": params, "totals": dict(total),
            "seconds": {"mean": round(statistics.mean(seconds), 3), "median": round(statistics.median(seconds), 3),
                        "worst": round(max(seconds), 3)},
            "failures": failures, "empty": empty, "images": rows,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=1)
        print(f"\nDesat a {path}")


if __name__ == "__main__":
    main()
