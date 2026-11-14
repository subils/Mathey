"""On viuen les dades i els models. Tot es pot canviar amb variables d'entorn.

Al portàtil, els valors per defecte apunten a les carpetes del projecte. A la
placa, l'app d'App Lab els fixa abans d'importar el mentor.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HOST = os.environ.get("MENTOR_HOST", "portàtil")
BANK_DB = os.environ.get("MENTOR_DB", os.path.join(ROOT, "data", "mentor.db"))
STATE_DB = os.environ.get("MENTOR_STATE_DB", os.path.join(ROOT, "data", "state.db"))
IMAGES = os.environ.get("MENTOR_IMAGES", os.path.join(ROOT, "research", "qualcomm-repo", "data", "images"))
LLM_URL = os.environ.get("MENTOR_LLM_URL", "http://127.0.0.1:8081").rstrip("/")
EMBED_URL = os.environ.get("MENTOR_EMBED_URL", "http://127.0.0.1:8082").rstrip("/")

# Temps màxim que l'alumne espera una resposta de la IA de la placa
LLM_TIMEOUT = float(os.environ.get("MENTOR_LLM_TIMEOUT", "40"))

# Nivells del Cangur on hi ha contingut preparat (5è de primària a 2n d'ESO)
MAX_LEVEL = int(os.environ.get("MENTOR_MAX_LEVEL", "3"))

# Curs de l'alumne -> nivell inicial del Cangur
GRADE_LEVEL = {"5è": 0, "6è": 1, "1r ESO": 2, "2n ESO": 3}

TOPICS = ["aritmètica", "àlgebra", "geometria", "combinatòria i probabilitat", "lògica"]
