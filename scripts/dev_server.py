#!/usr/bin/env python3
"""Servidor de desenvolupament del mentor, per al portàtil.

    python3 scripts/dev_server.py            # API a http://127.0.0.1:7000
    python3 scripts/dev_server.py --port 7001

Fa el paper de la placa mentre no la tenim: exposa les rutes de mentor/api.py
al port 7000, el mateix que farà servir l'app d'App Lab. Si existeix web/out
(el resultat de `npm run build`), també serveix la web, com farà la placa.

Només biblioteca estàndard.
"""
import argparse
import json
import mimetypes
import os
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mentor.api import ROUTES, ApiError, Binary  # noqa: E402

WEB_OUT = os.path.join(ROOT, "web", "out")

# Pla B a la placa: el mentor corre aquí i l'app d'App Lab (mode «matriu») només
# pinta els LEDs. Si MENTOR_MATRIX_URL és definit (p. ex.
# http://127.0.0.1:7000/placa/matriu), cada dibuix s'hi envia en un fil a part.
MATRIX_URL = os.environ.get("MENTOR_MATRIX_URL", "")


def _push_matrix(frame):
    def send():
        try:
            request = urllib.request.Request(MATRIX_URL, data=json.dumps({"matrix": frame}).encode(),
                                             headers={"Content-Type": "application/json"})
            urllib.request.urlopen(request, timeout=3).read()
        except OSError as error:
            sys.stderr.write(f"matriu: no s'ha pogut enviar ({error})\n")
    threading.Thread(target=send, daemon=True).start()


class Handler(BaseHTTPRequestHandler):
    server_version = "MentorDev/0.1"

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        # `next dev` corre al 3000 i crida aquí: cal CORS. A la placa és el mateix origen.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, payload):
        self._send(status, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _api(self, method):
        url = urlparse(self.path)
        route = ROUTES.get((method, url.path.rstrip("/") or "/"))
        if route is None:
            return self._json(404, {"error": f"ruta desconeguda: {method} {url.path}"})
        params = {key: values[-1] for key, values in parse_qs(url.query).items()}
        if method == "POST":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                try:
                    params.update(json.loads(self.rfile.read(length)))
                except (ValueError, TypeError):
                    return self._json(400, {"error": "el cos ha de ser un objecte JSON"})
        try:
            result = route(params)
        except ApiError as error:
            return self._json(error.status, {"error": error.message})
        except Exception as error:  # el servidor no ha de caure per una ruta
            return self._json(500, {"error": f"{type(error).__name__}: {error}"})
        if isinstance(result, Binary):
            return self._send(200, result.data, result.content_type)
        self._json(200, result)

    def _static(self):
        path = urlparse(self.path).path
        target = os.path.normpath(os.path.join(WEB_OUT, path.lstrip("/")))
        if not target.startswith(WEB_OUT):
            return self._json(403, {"error": "fora de la carpeta de la web"})
        if os.path.isdir(target):
            target = os.path.join(target, "index.html")
        if not os.path.isfile(target):
            return self._json(404, {"error": "no trobat. Has fet `npm run build` a web/?"})
        with open(target, "rb") as f:
            body = f.read()
        self._send(200, body, mimetypes.guess_type(target)[0] or "application/octet-stream")

    def do_OPTIONS(self):
        self._send(204, b"", "text/plain")

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._api("GET")
        self._static()

    def do_POST(self):
        self._api("POST")

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))


def main():
    if MATRIX_URL:  # pla B: cada dibuix nou del mentor s'envia a l'app de la matriu
        from mentor import service
        service.on_matrix(_push_matrix)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7000)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    web = "també serveix web/out" if os.path.isdir(WEB_OUT) else "web/out no existeix: només API"
    print(f"Mentor (dev) a http://{args.host}:{args.port}  ({web}). Ctrl+C per aturar.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
