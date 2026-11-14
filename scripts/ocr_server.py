#!/usr/bin/env python3
"""Servei de lectura d'imatges (OCR): la foto d'un problema -> el text que hi surt.

    python3 scripts/ocr_server.py                                   # tria el motor sol
    python3 scripts/ocr_server.py --engine tesseract --host 0.0.0.0  # a la placa
    research/qualcomm-repo/.venv/bin/python scripts/ocr_server.py --engine rapidocr   # al portàtil

És un servei a part del mentor perquè el mentor pot córrer dins del contenidor
d'App Lab, on no hi ha els programes del sistema. Aquest servei corre a
l'amfitrió, al costat dels llama-server, i el mentor el crida per HTTP
(mentor/ocr.py). Tot passa a la placa: cap imatge surt de l'aparell.

    GET  /health         -> {"status": "ok", "engine": "tesseract", ...}
    POST /ocr?lang=cat   cos: els bytes de la imatge (PNG o JPEG, 8 MB com a màxim)
                         -> {"text": "...", "engine": "tesseract", "seconds": 1.23, "lines": 4}
    Errors: {"error": "..."} amb 400, 404, 411, 413, 415, 500, 503 o 504.

Motors (--engine):
    tesseract  el programa `tesseract` (apt: tesseract-ocr tesseract-ocr-cat
               tesseract-ocr-spa tesseract-ocr-eng). És el de la placa.
    rapidocr   el paquet rapidocr_onnxruntime (al portàtil, amb el virtualenv dels
               organitzadors). El seu model és xinès i anglès: no coneix els
               accents catalans, i «àrea» surt «area».
    qwen       experimental: demana la transcripció a un llama-server que hi veu
               (--mmproj, port 8083). Molt lent a la placa.
    auto       tesseract si el programa hi és; si no, rapidocr si es pot importar;
               si no, qwen.

El text es neteja molt poc (espais, línies buides): no s'intenta «arreglar» les
matemàtiques. Si hi ha Pillow (python3-pil), abans de llegir es gira la foto
segons l'EXIF del mòbil i s'encongeix si és enorme; si no n'hi ha, la imatge
passa tal qual i és la web qui l'ha d'enviar dreta i petita.

Només biblioteca estàndard (els motors s'importen o es criden quan toquen).
"""
import argparse
import base64
import importlib.util
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

MAX_BYTES = 8 * 1024 * 1024  # cos màxim d'una petició
MAX_PIXELS = 64_000_000  # una foto de 64 MP; més que això no és una foto de mòbil
DRAIN_BYTES = 32 * 1024 * 1024  # fins aquí es llegeix i es llença un cos massa gran, per poder respondre 413
QUEUE_SECONDS = 30  # quant espera una petició que un altre alumne acabi

VISION_URL = "http://127.0.0.1:8083/v1/chat/completions"
VISION_PROMPT = (
    "Transcribe all the text in this image exactly as written, in its original language, "
    "line by line. Output only the text: no comments, no translation, and do not solve anything."
)


class EngineError(Exception):
    """Un error que es pot explicar al client: estat HTTP i missatge curt."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


# --- El text ---------------------------------------------------------------------

def clean(text):
    """Neteja lleugera: espais repetits i línies buides. Res més."""
    text = unicodedata.normalize("NFC", text or "").replace("\r", "\n").replace("\x0c", "\n")
    lines = []
    for line in text.split("\n"):
        line = "".join(ch for ch in line if ch == "\t" or unicodedata.category(ch) != "Cc")
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


# --- La imatge -------------------------------------------------------------------

def image_type(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    return ""


def image_size(data):
    """(amplada, alçada) llegides de la capçalera del PNG o del JPEG, o None."""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                return None
            marker = data[i + 1]
            if marker == 0xFF:  # farciment entre segments
                i += 1
                continue
            if marker in (0x01,) or 0xD0 <= marker <= 0xD9:  # sense longitud
                i += 2
                continue
            length = int.from_bytes(data[i + 2:i + 4], "big")
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):  # SOF: aquí hi ha la mida
                return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
            i += 2 + length
    return None


def prepare(data, max_side):
    """Deixa la foto dreta i d'una mida raonable. Torna (bytes, nota).

    Els mòbils desen la foto «de costat» i apunten el gir a l'EXIF; cap dels
    motors el llegeix. Amb Pillow es gira i, si el costat llarg passa de
    `max_side`, s'encongeix. Sense Pillow la imatge passa tal qual.
    """
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return data, "sense Pillow: la imatge passa tal qual"
    try:
        image = Image.open(io.BytesIO(data))
        orientation = image.getexif().get(0x0112, 1)
        too_big = bool(max_side) and max(image.size) > max_side
        if orientation in (None, 1) and not too_big:
            return data, ""
        image = ImageOps.exif_transpose(image)
        if image.mode in ("RGBA", "LA", "P"):  # la transparència, sobre blanc
            image = image.convert("RGBA")
            white = Image.new("RGBA", image.size, (255, 255, 255, 255))
            image = Image.alpha_composite(white, image).convert("RGB")
        elif image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        if too_big:
            image.thumbnail((max_side, max_side), getattr(Image, "Resampling", Image).LANCZOS)
        out = io.BytesIO()
        image.save(out, format="PNG", compress_level=1)
        note = f"girada segons l'EXIF ({orientation})" if orientation not in (None, 1) else ""
        if too_big:
            note = (note + ", " if note else "") + f"encongida a {image.size[0]}x{image.size[1]}"
        return out.getvalue(), note
    except Exception as error:  # Pillow no l'entén: que ho digui el motor
        return data, f"Pillow no l'ha pogut preparar ({type(error).__name__})"


# --- Motor 1: Tesseract (el de la placa) ------------------------------------------

class Tesseract:
    name = "tesseract"
    # Per a cada idioma de la petició, els models que es demanen, per ordre.
    # El primer mana; els altres ajuden amb paraules d'una altra llengua.
    PREFERRED = {
        "cat": ("cat", "spa", "eng"), "ca": ("cat", "spa", "eng"),
        "spa": ("spa", "cat", "eng"), "esp": ("spa", "cat", "eng"), "es": ("spa", "cat", "eng"),
        "eng": ("eng",), "en": ("eng",),
    }

    def __init__(self, args):
        self.binary = shutil.which("tesseract")
        if not self.binary:
            raise EngineError(503, "no trobo el programa tesseract "
                                   "(a la placa: ./board/06_install_ocr.sh)")
        self.psm = args.psm
        self.timeout = args.timeout or 45
        self.forced = [code for code in (args.tesseract_langs or "").replace(",", "+").split("+") if code]
        self.env = dict(os.environ)
        if args.threads:
            self.env["OMP_THREAD_LIMIT"] = str(args.threads)
        self.languages = self._installed()
        if not [code for code in self.languages if code not in ("osd", "equ")]:
            raise EngineError(503, "tesseract no té cap idioma instal·lat "
                                   "(apt install tesseract-ocr-cat tesseract-ocr-spa tesseract-ocr-eng)")

    def _installed(self):
        try:
            done = subprocess.run([self.binary, "--list-langs"], stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, timeout=15, env=self.env)
        except (OSError, subprocess.SubprocessError):
            return []
        lines = done.stdout.decode("utf-8", "replace").splitlines()
        # La primera línia és un títol amb espais; la resta, un codi per línia
        return sorted({line.strip() for line in lines if re.fullmatch(r"[A-Za-z0-9_/-]+", line.strip())})

    def languages_for(self, lang):
        usable = [code for code in self.languages if code not in ("osd", "equ")]
        wanted = self.forced or self.PREFERRED.get((lang or "cat").lower(), self.PREFERRED["cat"])
        chosen = [code for code in wanted if code in usable]
        if not chosen:  # el que hi hagi: millor sense accents que res
            chosen = ["eng"] if "eng" in usable else usable[:1]
        return "+".join(chosen)

    def _run(self, image, languages, psm):
        # `stdin` i `stdout` com a noms de fitxer: la imatge no toca mai el disc.
        # --oem 1: el reconeixedor LSTM, l'únic que porten els models de Debian.
        command = [self.binary, "stdin", "stdout", "-l", languages, "--oem", "1", "--psm", str(psm)]
        try:
            done = subprocess.run(command, input=image, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=self.timeout, env=self.env)
        except subprocess.TimeoutExpired:
            raise EngineError(504, f"tesseract ha trigat més de {self.timeout:g} s")
        except OSError as error:
            raise EngineError(503, f"no s'ha pogut executar tesseract ({type(error).__name__})")
        if done.returncode != 0:
            detail = [line.strip() for line in done.stderr.decode("utf-8", "replace").splitlines() if line.strip()]
            sys.stderr.write("tesseract: " + " | ".join(detail[-3:])[:400] + "\n")
            if any("pixRead" in line or "cannot be read" in line or "Unknown format" in line for line in detail):
                raise EngineError(415, "tesseract no ha pogut obrir la imatge")
            raise EngineError(500, f"tesseract ha fallat (codi {done.returncode})")
        return done.stdout.decode("utf-8", "replace")

    def read(self, image, lang):
        languages = self.languages_for(lang)
        text = self._run(image, languages, self.psm)
        if not text.strip() and self.psm != 6:
            # L'anàlisi de pàgina de vegades no veu text en imatges d'una o dues
            # línies («Empty page»): segon intent com un sol bloc de text.
            text = self._run(image, languages, 6)
        return text, languages

    def health(self):
        return {"languages": self.languages, "psm": self.psm}


# --- Motor 2: RapidOCR (el del portàtil) -------------------------------------------

def _distance(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def reading_order(boxes):
    """Caixes de l'OCR -> files de dalt a baix i, dins de cada fila, d'esquerra a dreta.

    És el criteri de laptop/prepare_m3kang.py dels organitzadors (una fila nova
    quan el centre baixa més de 0,6 alçades), amb un afegit per a les fotos
    tortes: es mesura la inclinació de les línies i es desfà abans d'agrupar.
    Cada caixa és (quatre cantonades començant per dalt a l'esquerra, text, confiança).
    """
    items = []
    for box, text, _score in boxes:
        top_left, top_right, bottom_right, bottom_left = [(float(p[0]), float(p[1])) for p in box[:4]]
        items.append({
            "cx": (top_left[0] + top_right[0] + bottom_right[0] + bottom_left[0]) / 4,
            "cy": (top_left[1] + top_right[1] + bottom_right[1] + bottom_left[1]) / 4,
            "left": top_left, "w": _distance(top_left, top_right), "h": _distance(top_left, bottom_left),
            "angle": math.atan2(top_right[1] - top_left[1], top_right[0] - top_left[0]),
            "text": str(text),
        })
    # Inclinació de la pàgina: la mediana dels angles de les caixes llargues
    long_ones = sorted(it["angle"] for it in items if it["w"] > 3 * it["h"] and abs(it["angle"]) < math.pi / 4)
    skew = long_ones[len(long_ones) // 2] if long_ones else 0.0
    cos, sin = math.cos(skew), math.sin(skew)
    for it in items:
        it["x"] = it["left"][0] * cos + it["left"][1] * sin
        it["y"] = -it["cx"] * sin + it["cy"] * cos
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


class RapidOcr:
    name = "rapidocr"

    def __init__(self, args):
        try:
            from rapidocr_onnxruntime import RapidOCR  # import tardà: només si es tria aquest motor
        except ImportError:
            raise EngineError(503, "no puc importar rapidocr_onnxruntime: engega'm amb "
                                   "research/qualcomm-repo/.venv/bin/python")
        self.engine = RapidOCR()  # una sola instància: carregar els models triga

    def read(self, image, lang):
        try:
            boxes, _elapsed = self.engine(image)
        except Exception as error:
            # Una imatge trencada surt com a LoadImageError o com l'OSError de Pillow
            if "LoadImage" in type(error).__name__ or isinstance(error, (OSError, SyntaxError)):
                raise EngineError(415, "rapidocr no ha pogut obrir la imatge")
            raise
        rows = reading_order(boxes or [])
        return "\n".join(" ".join(it["text"] for it in row) for row in rows), "ch+en"

    def health(self):
        return {"languages": ["ch", "en"], "note": "sense accents catalans"}


# --- Motor 3: Qwen amb visió (experimental) ----------------------------------------

class Qwen:
    name = "qwen"

    def __init__(self, args):
        self.url = args.vision_url
        self.timeout = args.timeout or 180

    def read(self, image, lang):
        mime = image_type(image) or "image/png"
        payload = {
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64," + base64.b64encode(image).decode()}},
                {"type": "text", "text": VISION_PROMPT},
            ]}],
            "max_tokens": 400, "temperature": 0, "seed": 42,
        }
        request = urllib.request.Request(self.url, data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read())
            text = body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as error:
            # Un llama-server sense --mmproj respon amb un error a les imatges
            raise EngineError(503, f"el model amb visió ha respost {error.code} (té --mmproj?)")
        except TimeoutError:
            raise EngineError(504, f"el model amb visió ha trigat més de {self.timeout:g} s")
        except OSError as error:
            if "timed out" in str(error):
                raise EngineError(504, f"el model amb visió ha trigat més de {self.timeout:g} s")
            raise EngineError(503, f"el model amb visió no respon a {self.url}")
        except (ValueError, KeyError, IndexError, TypeError):
            raise EngineError(500, "el model amb visió ha tornat una resposta que no entenc")
        if not isinstance(text, str):
            raise EngineError(500, "el model amb visió ha tornat una resposta que no entenc")
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).replace("</think>", "")
        return text, "qwen"

    def health(self):
        base = self.url.split("/v1/")[0]
        try:
            with urllib.request.urlopen(base + "/health", timeout=1) as response:
                up = json.loads(response.read()).get("status") == "ok"
        except (OSError, ValueError):
            up = False
        return {"vision_url": self.url, "vision_up": up}


ENGINES = {"tesseract": Tesseract, "rapidocr": RapidOcr, "qwen": Qwen}


def pick_engine(name):
    """`auto`: tesseract si el programa hi és; si no, rapidocr si es pot importar; si no, qwen."""
    if name != "auto":
        return name
    if shutil.which("tesseract"):
        return "tesseract"
    if importlib.util.find_spec("rapidocr_onnxruntime") is not None:
        return "rapidocr"
    return "qwen"


# --- El servidor -------------------------------------------------------------------

class Reader:
    """El motor triat i el pany: es llegeix una sola imatge alhora."""

    def __init__(self, args):
        self.engine = ENGINES[pick_engine(args.engine)](args)
        self.max_side = args.max_side
        self.lock = threading.Lock()

    def read(self, image, lang):
        if not self.lock.acquire(timeout=QUEUE_SECONDS):
            raise EngineError(503, "el lector està ocupat amb una altra imatge; torna-ho a provar")
        try:
            started = time.perf_counter()
            image, note = prepare(image, self.max_side)
            raw, used = self.engine.read(image, lang)
            text = clean(raw)
            seconds = round(time.perf_counter() - started, 3)
        finally:
            self.lock.release()
        result = {"text": text, "engine": self.engine.name, "seconds": seconds,
                  "lines": len(text.splitlines()), "lang": used}
        if note:
            result["note"] = note
        return result

    def health(self):
        info = {"status": "ok", "engine": self.engine.name}
        info.update(self.engine.health())
        return info


READER = None


class Handler(BaseHTTPRequestHandler):
    server_version = "MentorOCR/0.1"
    timeout = 30  # un client que no acaba d'enviar no reté un fil per sempre

    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_error(self, code, message=None, explain=None):
        # Els errors que genera http.server (petició mal formada, mètode desconegut) també en JSON
        self.close_connection = True
        try:
            self._json(code, {"error": message or "petició no vàlida"})
        except OSError:
            pass

    def _path(self):
        return urlparse(self.path).path.rstrip("/") or "/"

    def do_GET(self):
        if self._path() == "/health":
            return self._json(200, READER.health())
        self._json(404, {"error": f"ruta desconeguda: GET {self._path()} (hi ha GET /health i POST /ocr)"})

    def _body(self):
        """Llegeix el cos o llança EngineError. Mai més de MAX_BYTES a la memòria."""
        try:
            length = int(self.headers.get("Content-Length") or "")
        except ValueError:
            self.close_connection = True
            raise EngineError(411, "falta Content-Length: envia la imatge sencera al cos")
        if length > MAX_BYTES:
            # Es llegeix i es llença, perquè el client pugui rebre la resposta
            remaining = length if length <= DRAIN_BYTES else 0
            while remaining > 0:
                chunk = self.rfile.read(min(65536, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
            self.close_connection = True
            raise EngineError(413, f"la imatge és massa gran ({length / 1048576:.1f} MB; màxim 8 MB)")
        if length <= 0:
            raise EngineError(400, "falta la imatge: envia els bytes del PNG o del JPEG al cos")
        data = self.rfile.read(length)
        if len(data) != length:
            self.close_connection = True
            raise EngineError(400, "la imatge ha arribat tallada")
        return data

    def do_POST(self):
        url = urlparse(self.path)
        if self._path() != "/ocr":
            return self._json(404, {"error": f"ruta desconeguda: POST {self._path()} (hi ha GET /health i POST /ocr)"})
        size = 0
        try:
            try:
                image = self._body()
            except OSError as error:  # el client ha marxat a mig enviar
                sys.stderr.write(f"ocr: connexió tallada ({type(error).__name__})\n")
                self.close_connection = True
                return
            size = len(image)
            if not image_type(image):
                raise EngineError(415, "només es llegeixen imatges PNG o JPEG")
            dimensions = image_size(image)
            if dimensions and dimensions[0] * dimensions[1] > MAX_PIXELS:
                raise EngineError(413, f"la imatge té massa píxels ({dimensions[0]}x{dimensions[1]})")
            lang = (parse_qs(url.query).get("lang") or ["cat"])[-1]
            result = READER.read(image, lang)
        except EngineError as error:
            sys.stderr.write(f"ocr: {error.status} {error.message} ({size} bytes)\n")
            return self._json(error.status, {"error": error.message})
        except Exception as error:  # el servei no ha de caure ni ensenyar cap traça
            sys.stderr.write(f"ocr: 500 {type(error).__name__}: {error}\n")
            return self._json(500, {"error": f"el lector ha fallat ({type(error).__name__})"})
        # Al registre, només mides i temps: mai el text de l'alumne
        sys.stderr.write(f"ocr: 200 {result['engine']} {size} bytes, {result['lines']} línies, "
                         f"{result['seconds']} s\n")
        self._json(200, result)

    def log_message(self, fmt, *args):
        pass  # el registre útil ja el fa do_POST; /health no ha d'omplir el journal


def main():
    global READER
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="127.0.0.1",
                        help="0.0.0.0 a la placa, perquè hi arribi el contenidor de l'app")
    parser.add_argument("--port", type=int, default=8084)
    parser.add_argument("--engine", default="auto", choices=["auto", "tesseract", "rapidocr", "qwen"])
    parser.add_argument("--timeout", type=float, default=0,
                        help="segons màxims per imatge (per defecte 45 amb tesseract i 180 amb qwen)")
    parser.add_argument("--max-side", type=int, default=2000,
                        help="amb Pillow: costat llarg màxim en píxels abans de llegir (0 = no encongir)")
    parser.add_argument("--psm", type=int, default=3,
                        help="tesseract: mode de segmentació (3 = pàgina automàtica, 6 = un sol bloc, 11 = text escampat)")
    parser.add_argument("--tesseract-langs", default="",
                        help="tesseract: força els models, p. ex. «cat» (més ràpid que cat+spa+eng)")
    parser.add_argument("--threads", type=int, default=0,
                        help="tesseract: fils d'OpenMP (OMP_THREAD_LIMIT); 0 = els que vulgui")
    parser.add_argument("--vision-url", default=os.environ.get("OCR_VISION_URL", VISION_URL),
                        help="qwen: el llama-server que hi veu")
    args = parser.parse_args()
    try:
        READER = Reader(args)
    except EngineError as error:
        sys.exit(f"ERROR: {error.message}")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.daemon_threads = True
    extra = ", ".join(f"{key}: {value}" for key, value in READER.engine.health().items())
    print(f"Lector d'imatges a http://{args.host}:{args.port}  motor: {READER.engine.name} ({extra}). "
          "Ctrl+C per aturar.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
