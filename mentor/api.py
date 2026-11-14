"""Les rutes de l'API del mentor, independents de qui les serveix.

Contracte per als adaptadors (scripts/dev_server.py al portàtil, app/python/main.py
a la placa):

- ROUTES és un diccionari {(mètode, ruta): funció}. Les rutes no tenen
  paràmetres de camí: tot va per la query (GET) o pel cos JSON (POST).
- Cada funció rep un sol argument, `params` (dict amb la query i el cos JSON
  fusionats) i torna un dict serialitzable a JSON, o un `Binary` per a fitxers.
- Si el dict té la clau "matrix" (8 llistes de 13 enters 0–7), l'adaptador de la
  placa la pinta a la matriu de LEDs. Al portàtil, la web la simula.
- Errors de l'usuari: llançar ApiError(status, missatge).

Detall de cada ruta: docs/ARQUITECTURA.md, secció 5.
"""
from dataclasses import dataclass

from . import service


@dataclass
class Binary:
    content_type: str
    data: bytes


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def _image(params):
    path, content_type = service.image_path(params.get("id", ""), params.get("lang", "cat"))
    if not path:
        raise ApiError(404, "imatge no trobada")
    with open(path, "rb") as f:
        return Binary(content_type, f.read())


def _wrap(fn):
    def handler(params):
        try:
            return fn(params or {})
        except service.UserError as error:
            raise ApiError(error.status, str(error)) from error
    handler.__name__ = getattr(fn, "__name__", "handler")
    return handler


ROUTES = {
    ("GET", "/api/health"): _wrap(service.health),
    ("POST", "/api/session"): _wrap(service.create_session),
    ("GET", "/api/next"): _wrap(service.next_problem),
    ("GET", "/api/problem"): _wrap(service.get_problem),
    ("GET", "/api/image"): _wrap(_image),
    ("POST", "/api/answer"): _wrap(service.answer),
    ("POST", "/api/hint"): _wrap(service.hint),
    ("POST", "/api/explain"): _wrap(service.explain),
    ("POST", "/api/warm"): _wrap(service.warm),
    ("GET", "/api/profile"): _wrap(service.profile),
    ("GET", "/api/teacher"): _wrap(service.teacher),
    ("GET", "/api/matrix"): _wrap(service.current_matrix),
    ("GET", "/api/stats"): _wrap(service.stats),
    # «Porta el teu problema»: foto -> text -> problemes semblants -> pista de la IA
    ("POST", "/api/own/ocr"): _wrap(service.own_ocr),
    ("POST", "/api/own/match"): _wrap(service.own_match),
    ("POST", "/api/own/help"): _wrap(service.own_help),
}
