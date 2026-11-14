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
import threading
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


def _reply_text(response):
    """El text de la resposta del model, sense el <think>. Buit si no n'hi ha."""
    text = response["choices"][0]["message"].get("content") or ""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).replace("</think>", "").strip()


# ------------------------------------------------------- lectures per endavant
#
# El model atén una petició cada cop (--parallel 1). Si cada problema obert
# llancés la seva lectura, es farien cua i la pregunta real de l'alumne hauria
# d'esperar-les totes. Per això, des del mentor:
# - com a màxim hi ha una lectura en marxa i una de pendent;
# - una lectura nova substitueix la pendent (la més recent és la que servirà);
# - una pregunta real de l'alumne anul·la la pendent (té prioritat).
# warm() i warm_own() continuen sent síncrones per als scripts de mesura.

_warm_cond = threading.Condition()
_warm_pending = None  # missatges de l'última lectura demanada i no començada
_warm_running = False


def _schedule_warm(messages):
    global _warm_pending, _warm_running
    with _warm_cond:
        _warm_pending = messages
        if _warm_running:
            return
        _warm_running = True
    threading.Thread(target=_warm_loop, name="lectura-ia", daemon=True).start()


def _cancel_pending_warm():
    global _warm_pending
    with _warm_cond:
        _warm_pending = None


def _warm_loop():
    global _warm_pending, _warm_running
    while True:
        with _warm_cond:
            messages, _warm_pending = _warm_pending, None
            if messages is None:
                _warm_running = False
                return
        try:
            _post("/v1/chat/completions", {
                "messages": messages, "max_tokens": 1, "temperature": 0, "cache_prompt": True,
            }, timeout=config.LLM_TIMEOUT)
        except Exception:  # és només una preparació: si falla, la pregunta real anirà en fred
            pass


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


def warm_later(problem_text, solution_steps):
    """Com warm(), però no bloqueja i no fa cua (és el que fa servir el mentor)."""
    _schedule_warm(_messages(problem_text, solution_steps))


def socratic(problem_text, solution_steps, chosen_option, trap, student_text):
    """Torna (text, timings) o llança OSError si la IA no respon."""
    tail = (
        f"\nL'ALUMNE HA TRIAT: {chosen_option}\n"
        + (f"ERROR PROBABLE: {trap}\n" if trap else "")
        + f"L'ALUMNE DIU: «{student_text.strip()[:300]}»\n\n"
        "Escriu UNA sola pregunta curta (màxim 20 paraules) que l'ajudi a veure el seu error. "
        "No diguis la resposta ni el resultat."
    )
    _cancel_pending_warm()  # la pregunta de l'alumne passa davant
    started = time.perf_counter()
    response = _post("/v1/chat/completions", {
        "messages": _messages(problem_text, solution_steps, tail),
        "max_tokens": 48, "temperature": 0.2, "seed": 42, "cache_prompt": True,
    }, timeout=config.LLM_TIMEOUT)
    text = _reply_text(response)
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


def warm_own_later(own_text, example):
    """Com warm_own(), però no bloqueja i no fa cua (és el que fa servir el mentor)."""
    _schedule_warm(_own_messages(own_text, example))


def own_hint(own_text, example, doubt, strategy=""):
    """Torna (text, timings) o llança OSError si la IA no respon."""
    tail = (
        f"\nL'ALUMNE DIU: «{doubt.strip()[:300]}»\n\n"
        + (f"ESTRATÈGIA ÚTIL: {strategy}\n\n" if strategy and not example else "")
        + "Escriu una pista curta (una o dues frases) perquè continuï EL SEU problema"
        + (" fent servir la mateixa idea de l'exemple" if example else "")
        + ". No calculis res, no diguis el resultat i no escriguis cap número que no sigui al seu problema."
    )
    _cancel_pending_warm()  # el dubte de l'alumne passa davant
    started = time.perf_counter()
    response = _post("/v1/chat/completions", {
        "messages": _own_messages(own_text, example, tail),
        "max_tokens": 72, "temperature": 0.2, "seed": 42, "cache_prompt": True,
    }, timeout=config.LLM_TIMEOUT)
    text = _reply_text(response)
    timings = response.get("timings", {})
    timings["wall_seconds"] = round(time.perf_counter() - started, 2)
    return text, timings
