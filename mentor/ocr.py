"""El lector d'imatges (OCR), vist des del mentor.

Per a «Porta el teu problema»: l'alumne envia al xat la foto d'un problema i el
mentor la llegeix amb `laptop/read_image.py --image` (RapidOCR, sense xarxa).
Aquell script torna en JSON l'enunciat i les opcions A–E; aquí es converteixen en
el text del problema, que és el prompt amb què la IA de la placa el resol.

Abans es llegia amb un servei HTTP a part (scripts/ocr_server.py, port 8084).
Ja no es fa servir per al xat.

- `read_image(bytes)`: el text del problema llegit de la imatge, en quant temps.
- `to_prompt(result)`: el JSON de read_image.py -> enunciat + opcions A) … E).
- `available()`: si hi ha l'script i l'intèrpret per executar-lo.
- `OcrUnavailable`: no s'ha pogut llegir (falta RapidOCR, triga massa, la imatge
  no és vàlida). És un OSError, com els errors de la IA de la placa: el mentor
  l'atrapa i ofereix a l'alumne d'escriure el problema a mà.

Configuració (variables d'entorn):
  MENTOR_READ_IMAGE         camí de read_image.py (per defecte el del repo,
                            laptop/read_image.py, o el que hi ha al costat del
                            paquet mentor/ a la placa)
  MENTOR_READ_IMAGE_PYTHON  intèrpret que té rapidocr_onnxruntime (per defecte el
                            mateix Python si el té; si no, el virtualenv dels
                            organitzadors, research/qualcomm-repo/.venv)
  MENTOR_OCR_TIMEOUT        segons que s'espera una lectura (per defecte 60)

El model de RapidOCR és xinès i anglès: no coneix els accents catalans («àrea»
surt «area»). Per a la IA no és un problema greu, però el text no és de fiar del tot.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))  # .../mentor
ROOT = os.path.dirname(HERE)  # el repo, o /app/python a la placa
LETTERS = "ABCDE"

try:
    OCR_TIMEOUT = float(os.environ.get("MENTOR_OCR_TIMEOUT", "60"))
except ValueError:
    OCR_TIMEOUT = 60.0

MAX_IMAGE_BYTES = 8 * 1024 * 1024


class OcrUnavailable(OSError):
    """No s'ha pogut llegir la imatge.

    `status` és com un estat HTTP: 4xx si el problema és la imatge (massa gran,
    no és PNG ni JPEG; no serveix de res tornar-ho a provar igual), 503 si falta
    el lector, 504 si ha trigat massa.
    """

    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status

    @property
    def rejected(self):
        return 400 <= self.status < 500


def script_path():
    """On és read_image.py: l'entorn, el repo o el costat de mentor/ (placa)."""
    candidates = [os.environ.get("MENTOR_READ_IMAGE"),
                  os.path.join(ROOT, "laptop", "read_image.py"),
                  os.path.join(ROOT, "read_image.py")]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def python_path():
    """L'intèrpret que executa read_image.py: el primer que tingui RapidOCR."""
    explicit = os.environ.get("MENTOR_READ_IMAGE_PYTHON")
    if explicit:
        return explicit
    if importlib.util.find_spec("rapidocr_onnxruntime") is not None:
        return sys.executable
    venv = os.path.join(ROOT, "research", "qualcomm-repo", ".venv", "bin", "python")
    return venv if os.path.isfile(venv) else sys.executable


def available():
    return script_path() is not None and os.path.exists(python_path())


def to_prompt(result):
    """{"question": ..., "options": {"A": ..., ...}} -> el text del problema.

    L'enunciat tal com l'ha llegit (una línia per fila) i, si s'han trobat les
    cinc opcions, una línia per opció: «A) 12».
    """
    question = str(result.get("question") or "").strip()
    options = result.get("options") or {}
    lines = [question] if question else []
    if isinstance(options, dict) and all(str(options.get(k) or "").strip() for k in LETTERS):
        lines.append("")
        lines += [f"{k}) {str(options[k]).strip()}" for k in LETTERS]
    return "\n".join(lines).strip()


def _image_suffix(image):
    if image.startswith(b"\x89PNG"):
        return ".png"
    if image.startswith(b"\xff\xd8"):
        return ".jpg"
    if image[:4] == b"RIFF" and image[8:12] == b"WEBP":
        return ".webp"
    return ".img"


def read_image(image_bytes, lang="cat", timeout=None):
    """Llegeix el problema d'una imatge PNG o JPEG amb read_image.py.

    Torna {"text", "question", "options", "engine", "seconds", "lines"}: `text`
    és el prompt (enunciat + opcions) i pot ser buit si a la imatge no hi ha text.
    `lang` no es fa servir (RapidOCR no en té); es manté per compatibilitat.
    Llança OcrUnavailable si no es pot llegir.
    """
    image = bytes(image_bytes or b"")
    if not image:
        raise OcrUnavailable("la imatge és buida", 400)
    if len(image) > MAX_IMAGE_BYTES:
        raise OcrUnavailable("la imatge és massa gran (màxim 8 MB)", 413)
    script = script_path()
    if not script:
        raise OcrUnavailable("no trobo read_image.py")
    python = python_path()
    wait = OCR_TIMEOUT if timeout is None else timeout
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="mathey-ocr-") as folder:
        path = os.path.join(folder, "problema" + _image_suffix(image))
        with open(path, "wb") as f:
            f.write(image)
        try:
            done = subprocess.run([python, script, "--image", path], capture_output=True,
                                  text=True, timeout=wait, cwd=folder)
        except subprocess.TimeoutExpired as error:
            raise OcrUnavailable(f"ha trigat més de {wait:g} s", 504) from error
        except OSError as error:  # l'intèrpret no hi és
            raise OcrUnavailable(f"no puc executar {python} ({error.strerror or error})") from error
    if done.returncode != 0:
        if "No module named" in done.stderr:
            raise OcrUnavailable(f"falta rapidocr_onnxruntime a {python} "
                                 "(MENTOR_READ_IMAGE_PYTHON)")
        last = (done.stderr.strip().splitlines() or [f"codi {done.returncode}"])[-1]
        raise OcrUnavailable(f"read_image.py ha fallat: {last[:200]}")
    try:
        result = json.loads(done.stdout)
    except ValueError as error:
        raise OcrUnavailable("read_image.py ha tornat una resposta que no entenc", 502) from error
    if not isinstance(result, dict):
        raise OcrUnavailable("read_image.py ha tornat una resposta que no entenc", 502)
    if result.get("error"):
        raise OcrUnavailable("no és una imatge PNG o JPEG", 415)
    text = to_prompt(result)
    return {
        "text": text,
        "question": str(result.get("question") or "").strip(),
        "options": result.get("options") or {},
        "engine": "read_image.py (RapidOCR)",
        "seconds": round(time.perf_counter() - started, 3),
        "lines": len(text.splitlines()),
    }
