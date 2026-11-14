"""Mentor Cangur: l'adaptador de la placa (app d'App Lab).

Exposa les rutes de mentor/api.py (ROUTES) amb el brick web_ui (FastAPI, port
7000), serveix la web exportada (assets/) i pinta a la matriu de LEDs el dibuix
"matrix" que tornen les rutes. És el bessó de scripts/dev_server.py, que fa el
mateix al portàtil.

Regles d'aquest fitxer:
- Cap crida lenta bloqueja el servidor: les rutes del mentor corren en el
  threadpool de FastAPI i la matriu té el seu propi fil.
- Un error del Bridge (el sketch encara compila, o no hi és) no tomba mai la web.
- App.run() és l'última línia.

Configuració (variables d'entorn; ordre: entorn real > data/mentor.env > per defecte):
  MENTOR_LLM_HOST   on escolten els llama-server (per defecte msgpack-rpc-router,
                    que App Lab apunta a l'amfitrió). Ex.: 172.17.0.1
  MENTOR_LLM_URL    http://<MENTOR_LLM_HOST>:8081
  MENTOR_EMBED_URL  http://<MENTOR_LLM_HOST>:8082
  MENTOR_OCR_URL    http://<MENTOR_LLM_HOST>:8084 (lectura d'imatges, opcional)
  MENTOR_DB, MENTOR_STATE_DB, MENTOR_IMAGES   dins de /app/data
  MENTOR_MODE       "complet" (per defecte) o "matriu" (pla B: només la matriu)
"""
import json
import os
import sys
import threading
import time
import traceback
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))  # /app/python
APP_DIR = os.path.dirname(HERE)  # /app = /home/arduino/ArduinoApps/mentor-cangur
DATA_DIR = os.path.join(APP_DIR, "data")
ASSETS_DIR = os.path.join(APP_DIR, "assets")
NO_WEB_DIR = os.path.join(HERE, "sense_web")


def log(message):
    print(f"[mentor-cangur] {message}", flush=True)


def load_env_file(path):
    """Llegeix KEY=VALUE de data/mentor.env sense trepitjar l'entorn real."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    log(f"configuració llegida de {path}")


# --- Configuració: abans d'importar el mentor, que la llegeix en importar-se ---
load_env_file(os.path.join(DATA_DIR, "mentor.env"))
LLM_HOST = os.environ.setdefault("MENTOR_LLM_HOST", "msgpack-rpc-router")
os.environ.setdefault("MENTOR_HOST", "placa")
os.environ.setdefault("MENTOR_DB", os.path.join(DATA_DIR, "mentor.db"))
os.environ.setdefault("MENTOR_STATE_DB", os.path.join(DATA_DIR, "state.db"))
os.environ.setdefault("MENTOR_IMAGES", os.path.join(DATA_DIR, "images"))
LLM_URL = os.environ.setdefault("MENTOR_LLM_URL", f"http://{LLM_HOST}:8081").rstrip("/")
EMBED_URL = os.environ.setdefault("MENTOR_EMBED_URL", f"http://{LLM_HOST}:8082").rstrip("/")
# Servei de lectura d'imatges (scripts/ocr_server.py), al mateix amfitrió que els models
OCR_URL = os.environ.setdefault("MENTOR_OCR_URL", f"http://{LLM_HOST}:8084").rstrip("/")
MODE = os.environ.get("MENTOR_MODE", "complet").strip().lower()

if HERE not in sys.path:
    sys.path.insert(0, HERE)  # python/mentor/ és el paquet del mentor

import numpy as np  # noqa: E402
from fastapi import Request  # noqa: E402
from fastapi.responses import JSONResponse, Response  # noqa: E402
from starlette.concurrency import run_in_threadpool  # noqa: E402

from arduino.app_bricks.web_ui import WebUI  # noqa: E402
from arduino.app_utils import App, Bridge, Frame  # noqa: E402


class _Never(Exception):
    """Substitut de Binary/ApiError si el mentor no s'ha pogut importar."""


ROUTES, Binary, ApiError = {}, _Never, _Never
MENTOR_ERROR = None
if MODE == "matriu":
    log("mode matriu (pla B): no es carrega el mentor; només es pinta la matriu")
else:
    try:
        from mentor.api import ROUTES, Binary, ApiError  # noqa: E402,F811
    except Exception as error:  # la web ha d'arrencar igualment i dir què passa
        MENTOR_ERROR = f"{type(error).__name__}: {error}"
        log(f"ERROR: no s'ha pogut importar el mentor: {MENTOR_ERROR}")
        traceback.print_exc()


# --- Matriu de LEDs ------------------------------------------------------------

ROWS, COLS, MAX_BRIGHTNESS = 8, 13, 7

STARTUP = [  # una K de Cangur, la mateixa que el mentor fa servir en repòs
    ".............",
    "....#...#....",
    "....#..#.....",
    "....#.#......",
    "....##.......",
    "....#.#......",
    "....#..#.....",
    "....#...#....",
]
BROKEN = [  # un "!": el mentor no s'ha carregat (mireu els registres)
    "......#......",
    "......#......",
    "......#......",
    "......#......",
    "......#......",
    ".............",
    "......#......",
    ".............",
]


def pattern_to_grid(pattern):
    return [[MAX_BRIGHTNESS if ch == "#" else 0 for ch in row] for row in pattern]


def frame_bytes(grid):
    """8 llistes de 13 enters 0-7 -> bytes per al sketch, com l'exemple oficial."""
    arr = np.array(grid, dtype=np.int64)
    if arr.shape != (ROWS, COLS):
        raise ValueError(f"la matriu ha de ser {ROWS}x{COLS}, no {arr.shape}")
    arr = np.clip(arr, 0, MAX_BRIGHTNESS).astype(np.uint8)
    # Frame per defecte té 256 nivells: els valors 0-7 passen tal qual, i el
    # sketch (setGrayscaleBits(3)) els entén com a brillantor 0-7.
    return Frame(arr).to_board_bytes()


class Matrix:
    """Pinta a la matriu des d'un fil propi.

    - L'últim dibuix guanya: si n'arriben molts, els intermedis es descarten.
    - Com a màxim un dibuix cada 0,34 s (regla: res no parpelleja més de 3 cops/s).
    - Si el Bridge falla (el sketch encara compila), torna a provar cada 3 s.
    """

    MIN_INTERVAL = 0.34
    RETRY = 3.0
    TIMEOUT = 5

    def __init__(self):
        self._cond = threading.Condition()
        self._pending = None
        self._shown = None
        self.last_error = None
        self.draws = 0
        threading.Thread(target=self._run, name="matriu", daemon=True).start()

    def show(self, grid):
        """No bloqueja mai i no llança mai: torna True si el dibuix és vàlid."""
        try:
            data = frame_bytes(grid)
        except Exception as error:
            log(f"dibuix de matriu invàlid, l'ignoro: {error}")
            return False
        with self._cond:
            self._pending = data
            self._cond.notify()
        return True

    def _take(self):
        with self._cond:
            data, self._pending = self._pending, None
            return data

    def _run(self):
        last_draw = 0.0
        failing_since = None
        while True:
            with self._cond:
                while self._pending is None:
                    self._cond.wait()
            wait = self.MIN_INTERVAL - (time.monotonic() - last_draw)
            if wait > 0:
                time.sleep(wait)
            data = self._take()  # el més recent, encara que n'hagi arribat un altre
            if data is None or data == self._shown:
                continue
            try:
                Bridge.call("draw", data, timeout=self.TIMEOUT)
                self._shown = data
                self.draws += 1
                self.last_error = None
                if failing_since is not None:
                    log("matriu: el Bridge ja respon")
                failing_since = None
            except Exception as error:  # el sketch no hi és o encara arrenca
                self.last_error = f"{type(error).__name__}: {error}"
                now = time.monotonic()
                if failing_since is None or now - failing_since > 60:
                    log(f"matriu: el Bridge no respon ({self.last_error}); ho reintento")
                    failing_since = now
                with self._cond:
                    if self._pending is None:
                        self._pending = data
                    self._cond.wait(timeout=self.RETRY)
            last_draw = time.monotonic()


matrix = Matrix()

# El mentor avisa de cada dibuix nou a l'instant (p. ex. «pensant» mentre la IA
# respon), no només quan acaba la petició. matrix.show no bloqueja mai.
if ROUTES:
    try:
        from mentor import service as _mentor_service  # noqa: E402
        _mentor_service.on_matrix(matrix.show)
    except Exception as error:
        log(f"no s'ha pogut escoltar la matriu del mentor: {error}")


# --- Adaptador HTTP ------------------------------------------------------------

def json_response(payload, status=200):
    return JSONResponse(payload, status_code=status, headers={"Cache-Control": "no-store"})


def error_response(status, message):
    return json_response({"error": message}, status)


def to_response(result):
    if isinstance(result, Binary):
        return Response(content=result.data, media_type=result.content_type,
                        headers={"Cache-Control": "max-age=3600"})
    if isinstance(result, dict) and result.get("matrix") is not None:
        matrix.show(result["matrix"])  # no bloqueja: el fil de la matriu el pinta
    return json_response(result)


async def read_params(request, method):
    """Query + cos JSON (POST) fusionats en un sol dict, com scripts/dev_server.py."""
    params = {key: value for key, value in request.query_params.multi_items()}
    if method != "GET":
        raw = await request.body()
        if raw.strip():
            try:
                body = json.loads(raw)
            except ValueError:
                return None
            if not isinstance(body, dict):
                return None
            params.update(body)
    return params


HANDLERS = {}  # (mètode, ruta) -> handler, també per a les rutes amb "/" final


def make_handler(method, path, fn):
    async def handler(request: Request):
        params = await read_params(request, method)
        if params is None:
            return error_response(400, "el cos ha de ser un objecte JSON")
        try:
            # Al threadpool: una crida al model (5-20 s) no bloqueja el servidor
            result = await run_in_threadpool(fn, params)
            return to_response(result)
        except ApiError as error:
            return error_response(getattr(error, "status", 400), getattr(error, "message", str(error)))
        except Exception as error:  # el servidor no cau per una ruta
            traceback.print_exc()
            return error_response(500, f"{type(error).__name__}: {error}")

    handler.__name__ = "api_" + method.lower() + path.replace("/", "_").replace("-", "_")
    return handler


def model_status(url, timeout=3.0):
    try:
        with urllib.request.urlopen(url + "/health", timeout=timeout) as response:
            return {"url": url, "respon": True, "health": json.loads(response.read() or b"{}")}
    except Exception as error:
        return {"url": url, "respon": False, "error": f"{type(error).__name__}: {error}"}


def board_status():
    """GET /placa/estat: diagnòstic de la placa (el model respon? la matriu?)."""
    return {
        "mode": MODE,
        "mentor_carregat": bool(ROUTES),
        "mentor_error": MENTOR_ERROR,
        "rutes": sorted(f"{m} {p}" for m, p in ROUTES),
        "model": model_status(LLM_URL),
        "embeddings": model_status(EMBED_URL),
        "matriu": {"dibuixos": matrix.draws, "error": matrix.last_error},
        "dades": {
            name: {"cami": os.environ[name], "existeix": os.path.exists(os.environ[name])}
            for name in ("MENTOR_DB", "MENTOR_STATE_DB", "MENTOR_IMAGES")
        },
        "web": os.path.isfile(os.path.join(ASSETS_DIR, "index.html")),
    }


async def draw_matrix(request: Request):
    """POST /placa/matriu {"matrix": [[...13]...8]}: per provar la matriu i per al pla B."""
    params = await read_params(request, "POST")
    if not params or "matrix" not in params:
        return error_response(400, 'cal {"matrix": 8 llistes de 13 enters 0-7}')
    if not matrix.show(params["matrix"]):
        return error_response(400, "la matriu ha de ser 8x13 amb enters 0-7")
    return json_response({"ok": True})


async def api_fallback(request: Request, rest: str):
    """Ruta /api/... desconeguda: accepta la "/" final (com el servidor de dev) o 404."""
    handler = HANDLERS.get((request.method, "/api/" + rest.rstrip("/")))
    if handler is not None:
        return await handler(request)
    if MENTOR_ERROR:
        return error_response(503, f"el mentor no s'ha carregat: {MENTOR_ERROR}")
    return error_response(404, f"ruta desconeguda: {request.method} /api/{rest}")


def check_models_later():
    """Escriu als registres si el model respon, perquè es vegi amb `app logs`."""
    time.sleep(3)
    for name, url in (("model de llenguatge", LLM_URL), ("embeddings", EMBED_URL)):
        status = model_status(url)
        if status["respon"]:
            log(f"{name}: respon a {url}")
        else:
            log(f"AVÍS {name}: NO respon a {url} ({status['error']}). Vegeu app/README.md, pla A i pla B.")


# --- Muntatge ----------------------------------------------------------------

if os.path.isfile(os.path.join(ASSETS_DIR, "index.html")):
    ui = WebUI()  # serveix /app/assets, port 7000
else:
    log(f"no hi ha {ASSETS_DIR}/index.html: serveixo la pàgina d'avís. Desplegueu la web.")
    ui = WebUI(assets_dir_path=NO_WEB_DIR)

for (method, path), fn in ROUTES.items():
    handler = make_handler(method, path, fn)
    HANDLERS[(method, path)] = handler
    ui.expose_api(method, path, handler)

ui.expose_api("GET", "/placa/estat", board_status)
ui.expose_api("POST", "/placa/matriu", draw_matrix)
ui.expose_api("GET", "/api/{rest:path}", api_fallback)
ui.expose_api("POST", "/api/{rest:path}", api_fallback)

log(f"mode={MODE} model={LLM_URL} embeddings={EMBED_URL} rutes={len(ROUTES)}")
matrix.show(pattern_to_grid(BROKEN if MENTOR_ERROR else STARTUP))
if MODE != "matriu":
    threading.Thread(target=check_models_later, name="comprova-model", daemon=True).start()

App.run()
