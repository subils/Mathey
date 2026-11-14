"""La IA de la placa (llama-server amb Qwen3.5 0.8B), vista des del mentor.

Dos usos en directe:
- `socratic()`: una sola pregunta que encamina l'alumne, a partir de com diu
  que ho ha pensat. La IA té la solució correcta com a context: no ha de
  resoldre res, només fer la pregunta.
- `warm()`: llegeix el problema per endavant mentre l'alumne el mira, perquè
  després només hagi de llegir la frase de l'alumne (`cache_prompt`).

Si la IA no hi és o triga massa, el mentor fa servir el contingut preparat.
"""
import json
import re
import time
import urllib.error
import urllib.request

from . import config

SYSTEM = (
    "Ets un mentor de matemàtiques per a nens i nenes de 10 a 14 anys. "
    "Mai dius la resposta ni el resultat. Respons sempre en català, amb una "
    "sola pregunta curta que ajudi l'alumne a trobar el seu error."
)


def _post(path, payload, timeout):
    request = urllib.request.Request(
        config.LLM_URL + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def available(timeout=1.0):
    try:
        with urllib.request.urlopen(config.LLM_URL + "/health", timeout=timeout) as response:
            return json.loads(response.read()).get("status") == "ok"
    except (OSError, ValueError):
        return False


def _context(problem_text, solution_steps):
    """La part fixa del prompt: és la que es pot llegir per endavant."""
    steps = "\n".join(f"- {s}" for s in solution_steps)
    return f"PROBLEMA:\n{problem_text.strip()}\n\nSOLUCIÓ CORRECTA (no la diguis):\n{steps}\n"


def _messages(problem_text, solution_steps, tail=""):
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": _context(problem_text, solution_steps) + tail},
    ]


def warm(problem_text, solution_steps):
    """Fa que el servidor llegeixi el context ara. No espera resposta útil."""
    try:
        _post("/v1/chat/completions", {
            "messages": _messages(problem_text, solution_steps),
            "max_tokens": 1, "temperature": 0, "cache_prompt": True,
        }, timeout=config.LLM_TIMEOUT)
        return True
    except (OSError, ValueError, urllib.error.URLError):
        return False


def socratic(problem_text, solution_steps, chosen_option, trap, student_text):
    """Torna (text, timings) o llança OSError si la IA no respon."""
    tail = (
        f"\nL'ALUMNE HA TRIAT: {chosen_option}\n"
        + (f"ERROR PROBABLE: {trap}\n" if trap else "")
        + f"L'ALUMNE DIU: «{student_text.strip()[:300]}»\n\n"
        "Escriu UNA sola pregunta curta (màxim 20 paraules) que l'ajudi a veure el seu error. "
        "No diguis la resposta ni el resultat."
    )
    started = time.perf_counter()
    response = _post("/v1/chat/completions", {
        "messages": _messages(problem_text, solution_steps, tail),
        "max_tokens": 48, "temperature": 0.2, "seed": 42, "cache_prompt": True,
    }, timeout=config.LLM_TIMEOUT)
    text = response["choices"][0]["message"]["content"]
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).replace("</think>", "").strip()
    timings = response.get("timings", {})
    timings["wall_seconds"] = round(time.perf_counter() - started, 2)
    return text, timings


# ------------------------------------------------------------------ problema propi
#
# L'alumne porta un problema que no és al banc. La IA no en sap la solució (i no
# la sabria trobar), però té com a exemple un problema semblant JA RESOLT i
# verificat. La seva feina: una pista curta per continuar, amb la mateixa idea.

SYSTEM_OWN = (
    "Ets un mentor de matemàtiques per a nens i nenes de 10 a 14 anys. "
    "Mai resols el problema ni dius el resultat. Respons sempre en català, "
    "amb una o dues frases curtes que ajudin l'alumne a continuar ell sol."
)


def _own_context(own_text, example):
    """La part fixa del prompt (es pot llegir mentre l'alumne escriu el seu dubte)."""
    parts = [f"PROBLEMA DE L'ALUMNE:\n{own_text.strip()[:900]}\n"]
    if example:
        steps = "\n".join(f"- {s}" for s in (example.get("solution") or [])[:3])
        parts.append(
            "UN PROBLEMA SEMBLANT JA RESOLT (serveix d'exemple, no és el de l'alumne):\n"
            f"Idea clau: {example.get('key_idea', '')}\n"
            + (f"Primers passos:\n{steps}\n" if steps else ""))
    elif own_text:
        parts.append("(No hi ha cap exemple semblant.)\n")
    return "\n".join(parts)


def _own_messages(own_text, example, tail=""):
    return [
        {"role": "system", "content": SYSTEM_OWN},
        {"role": "user", "content": _own_context(own_text, example) + tail},
    ]


def warm_own(own_text, example):
    try:
        _post("/v1/chat/completions", {
            "messages": _own_messages(own_text, example),
            "max_tokens": 1, "temperature": 0, "cache_prompt": True,
        }, timeout=config.LLM_TIMEOUT)
        return True
    except (OSError, ValueError, urllib.error.URLError):
        return False


def own_hint(own_text, example, doubt, strategy=""):
    """Torna (text, timings) o llança OSError si la IA no respon."""
    tail = (
        f"\nL'ALUMNE DIU: «{doubt.strip()[:300]}»\n\n"
        + (f"ESTRATÈGIA ÚTIL: {strategy}\n\n" if strategy and not example else "")
        + "Escriu una pista curta (una o dues frases) perquè continuï EL SEU problema"
        + (" fent servir la mateixa idea de l'exemple" if example else "")
        + ". No calculis res, no diguis el resultat i no escriguis cap número que no sigui al seu problema."
    )
    started = time.perf_counter()
    response = _post("/v1/chat/completions", {
        "messages": _own_messages(own_text, example, tail),
        "max_tokens": 72, "temperature": 0.2, "seed": 42, "cache_prompt": True,
    }, timeout=config.LLM_TIMEOUT)
    text = response["choices"][0]["message"]["content"]
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).replace("</think>", "").strip()
    timings = response.get("timings", {})
    timings["wall_seconds"] = round(time.perf_counter() - started, 2)
    return text, timings
