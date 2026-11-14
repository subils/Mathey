"""El lector d'imatges (OCR), vist des del mentor.

Per a «Porta el teu problema»: l'alumne puja la foto d'un problema i la placa en
treu el text. El mentor no llegeix imatges ell mateix: les envia a un servei
petit (scripts/ocr_server.py) que corre a l'amfitrió de la placa, al costat dels
llama-server, perquè dins del contenidor d'App Lab no hi ha Tesseract.

- `read_image(bytes)`: el text de la imatge, quin motor l'ha llegit i en quant temps.
- `available()`: si el servei respon.
- `OcrUnavailable`: el servei no hi és, triga massa o no ha pogut llegir la imatge.
  És un OSError, com els errors de la IA de la placa: el mentor l'atrapa i
  ofereix a l'alumne d'escriure el problema a mà.

Configuració (variables d'entorn):
  MENTOR_OCR_URL      on escolta el servei (per defecte http://127.0.0.1:8084)
  MENTOR_OCR_TIMEOUT  segons que s'espera una lectura (per defecte 60)

El text que torna l'OCR no és de fiar del tot (accents, símbols, ordre de les
línies quan hi ha una figura): cal ensenyar-lo a l'alumne perquè el corregeixi
abans de fer-lo servir.
"""
import json
import os
import time
import urllib.error
import urllib.request
from urllib.parse import quote

OCR_URL = os.environ.get("MENTOR_OCR_URL", "http://127.0.0.1:8084").rstrip("/")
try:
    OCR_TIMEOUT = float(os.environ.get("MENTOR_OCR_TIMEOUT", "60"))
except ValueError:
    OCR_TIMEOUT = 60.0

# El mateix límit que el servei: una foto més gran s'ha d'encongir abans d'enviar-la
MAX_IMAGE_BYTES = 8 * 1024 * 1024


class OcrUnavailable(OSError):
    """El servei de lectura d'imatges no hi és o no ha pogut llegir la imatge.

    `status` és l'estat HTTP que ha tornat el servei, o 0 si no s'hi ha arribat.
    `rejected` diu si el problema és la imatge (massa gran, no és PNG ni JPEG) i
    no el servei: en aquest cas no serveix de res tornar-ho a provar igual.
    """

    def __init__(self, message, status=0):
        super().__init__(message)
        self.status = status

    @property
    def rejected(self):
        return 400 <= self.status < 500


def _error_message(error):
    """El missatge que el servei posa a {"error": ...}, o l'estat si no n'hi ha."""
    try:
        return str(json.loads(error.read())["error"])
    except (OSError, ValueError, KeyError, TypeError):
        return f"error {error.code}"


def health(timeout=1.0, url=None):
    """El que diu GET /health (estat, motor, idiomes), o None si el servei no respon."""
    try:
        with urllib.request.urlopen((url or OCR_URL).rstrip("/") + "/health", timeout=timeout) as response:
            info = json.loads(response.read())
    except (OSError, ValueError):
        return None
    return info if isinstance(info, dict) else None


def available(timeout=1.0, url=None):
    info = health(timeout, url)
    return bool(info) and info.get("status") == "ok"


def read_image(image_bytes, lang="cat", url=None, timeout=None):
    """Llegeix el text d'una imatge PNG o JPEG.

    Torna {"text", "engine", "seconds", "lines", "engine_seconds"}: `seconds` és
    el que ha esperat el mentor (cua i transport inclosos) i `engine_seconds` el
    que ha trigat el motor. `text` pot ser buit si a la imatge no hi ha text.
    Llança OcrUnavailable si el servei no respon, triga massa o rebutja la imatge.
    """
    image = bytes(image_bytes or b"")
    if not image:
        raise OcrUnavailable("la imatge és buida", 400)
    if len(image) > MAX_IMAGE_BYTES:
        raise OcrUnavailable("la imatge és massa gran (màxim 8 MB)", 413)
    base = (url or OCR_URL).rstrip("/")
    wait = OCR_TIMEOUT if timeout is None else timeout
    request = urllib.request.Request(
        f"{base}/ocr?lang={quote(str(lang or 'cat'))}", data=image,
        headers={"Content-Type": "application/octet-stream"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=wait) as response:
            result = json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise OcrUnavailable(_error_message(error), error.code) from error
    except TimeoutError as error:
        raise OcrUnavailable(f"ha trigat més de {wait:g} s") from error
    except OSError as error:  # connexió rebutjada, nom que no resol, temps esgotat en connectar
        if "timed out" in str(error):
            raise OcrUnavailable(f"ha trigat més de {wait:g} s") from error
        raise OcrUnavailable(f"no respon a {base}") from error
    except ValueError as error:
        raise OcrUnavailable("ha tornat una resposta que no entenc", 502) from error
    if not isinstance(result, dict) or not isinstance(result.get("text"), str):
        raise OcrUnavailable("ha tornat una resposta que no entenc", 502)
    return {
        "text": result["text"],
        "engine": str(result.get("engine") or ""),
        "seconds": round(time.perf_counter() - started, 3),
        "lines": int(result.get("lines") or len(result["text"].splitlines())),
        "engine_seconds": result.get("seconds"),
    }
