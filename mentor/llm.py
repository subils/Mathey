"""La IA de la placa (llama-server amb Qwen3.5 0.8B), vista des del mentor.

Dos usos en directe:
- `socratic()`: una sola pregunta que encamina l'alumne, a partir de com diu
  que ho ha pensat. La IA té la solució correcta com a context: no ha de
  resoldre res, només fer la pregunta.
- `warm()`: llegeix el problema per endavant mentre l'alumne el mira, perquè
  després només hagi de llegir la frase de l'alumne (`cache_prompt`).

Si la IA no hi és o triga massa, el mentor fa servir el contingut preparat.
"""
import hashlib
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


_was_available = False


def available(timeout=1.0):
    global _was_available
    try:
        with urllib.request.urlopen(config.LLM_URL + "/health", timeout=timeout) as response:
            up = json.loads(response.read()).get("status") == "ok"
    except (OSError, ValueError):
        up = False
    if up and not _was_available:  # la IA acaba d'arrencar o torna: deixa el system a punt
        prepare_system_later()
    _was_available = up
    return up


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
            _prepare_slot(messages)
            # Ningú no espera aquesta lectura, però si es talla abans d'hora, llama-server
            # l'anul·la i la pregunta que ve darrere l'ha de tornar a fer sencera: un
            # problema llarg pot trigar més de 40 s a llegir-se.
            _post("/v1/chat/completions", {
                "messages": messages, "max_tokens": 1, "temperature": 0, "cache_prompt": True,
                "chat_template_kwargs": {"enable_thinking": False},  # el mateix prompt que el xat
            }, timeout=config.LLM_STREAM_TIMEOUT)
        except Exception:  # és només una preparació: si falla, la pregunta real anirà en fred
            pass


# ------------------------------------------- el prompt de sistema, llegit un sol cop
#
# El model és híbrid (capes recurrents): llama-server no pot reaprofitar qualsevol
# inici de prompt, només els punts que ha desat. A la placa, llegir el prompt de
# sistema del xat costa 0,089 s per token; si s'ha de rellegir a cada problema, el
# xat no pot portar exemples. Per això:
# - quan la IA arrenca, el mentor llegeix [SYSTEM_SOLVE, "."] un cop i en desa l'estat
#   a disc (`POST /slots/0?action=save`; cal `--slot-save-path` al servei);
# - abans d'un problema nou, restaura aquest estat (menys d'un segon al Mac) i la IA només
#   llegeix l'enunciat. Una petició d'un altre mode pel mig ja no obliga a rellegir res;
# - el fitxer porta l'empremta del text: si SYSTEM_SOLVE canvia, se'n fa un de nou.
# Sense `--slot-save-path` tot funciona igual que abans, només que més lent.

_slot_lock = threading.Lock()
_slot_key = None  # la conversa que l'slot té llegida; None si no se sap
_long_ready = False  # SYSTEM_SOLVE és desat a la placa (si no, el xat fa servir el curt)
_long_building = False
_long_last_try = 0.0
_RETRY_SECONDS = 120


def long_prompt_ready():
    return _long_ready


def _ensure_long_prompt():
    """Si el prompt llarg no és a punt, torna-ho a provar de tant en tant (no bloqueja)."""
    if not _long_ready and not _long_building and time.monotonic() - _long_last_try > _RETRY_SECONDS:
        prepare_system_later()


def _prefix_file(system):
    return "mathey-" + hashlib.sha1(system.encode()).hexdigest()[:12] + ".bin"


_slots_supported = None  # None: no se sap; False: el servei no té --slot-save-path (HTTP 501)


def _slot_action(action, filename, timeout):
    global _slots_supported
    try:
        _post(f"/slots/0?action={action}", {"filename": filename}, timeout=timeout)
        _slots_supported = True
        return True
    except urllib.error.HTTPError as error:  # 501: sense --slot-save-path; 400: el fitxer no hi és
        _slots_supported = error.code != 501  # 400 vol dir que sí que pot desar
        return False
    except (OSError, ValueError):
        return False


def _conversation_key(messages):
    return hashlib.sha1(json.dumps(messages[:2], ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _forget_slot():
    """Una petició amb un altre prompt de sistema ha passat per l'slot."""
    global _slot_key
    with _slot_lock:
        _slot_key = None


def _prepare_slot(messages):
    """Abans d'una petició: si l'slot no té llegida aquesta conversa, restaura el system desat."""
    global _slot_key, _long_ready
    if not messages or messages[0].get("role") != "system" or messages[0]["content"] != SYSTEM_SOLVE:
        _forget_slot()
        return
    key = _conversation_key(messages)
    with _slot_lock:
        if _slot_key == key:
            return  # mateix problema (seguiment, o resolució després de la lectura per endavant)
        _slot_key = key
    if not _slot_action("restore", _prefix_file(SYSTEM_SOLVE), timeout=30):
        _long_ready = False  # el servei ha canviat o ha perdut el fitxer: torna al curt
        _forget_slot()
        _ensure_long_prompt()


def _build_prefix():
    global _slot_key, _long_ready, _long_building, _long_last_try
    name = _prefix_file(SYSTEM_SOLVE)
    try:
        with _slot_lock:
            _slot_key = None
        if _slot_action("restore", name, timeout=30):
            _long_ready = True  # ja estava desat (el fitxer sobreviu als reinicis)
            return
        if _slots_supported is False:
            return  # sense --slot-save-path no es pot desar: el xat continua amb el prompt curt
        _post("/v1/chat/completions", {
            "messages": [{"role": "system", "content": SYSTEM_SOLVE}, {"role": "user", "content": "."}],
            "max_tokens": 1, "temperature": 0, "cache_prompt": True,
            "chat_template_kwargs": {"enable_thinking": False},
        }, timeout=900)  # el primer cop triga uns 3 minuts a la placa; després el fitxer hi queda
        _long_ready = _slot_action("save", name, timeout=120)
    except Exception:
        _long_ready = False
    finally:
        _long_building = False
        _long_last_try = time.monotonic()


def prepare_system_later():
    """Deixa SYSTEM_SOLVE llegit i desat a disc (no bloqueja). Es crida quan la IA arrenca."""
    global _long_building
    if _long_building:
        return
    _long_building = True
    threading.Thread(target=_build_prefix, name="system-ia", daemon=True).start()


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
        _forget_slot()
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
    _forget_slot()
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
        _forget_slot()
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
    _forget_slot()
    started = time.perf_counter()
    response = _post("/v1/chat/completions", {
        "messages": _own_messages(own_text, example, tail),
        "max_tokens": 72, "temperature": 0.2, "seed": 42, "cache_prompt": True,
    }, timeout=config.LLM_TIMEOUT)
    text = _reply_text(response)
    timings = response.get("timings", {})
    timings["wall_seconds"] = round(time.perf_counter() - started, 2)
    return text, timings


# ------------------------------------------------------ problema propi: xat
#
# Ordre del fundador (14/11/2026): al mode 2 (xat «Porta el teu problema») la IA
# de la placa SÍ que intenta resoldre el problema de l'alumne, pas a pas, i
# l'acosta a una solució final. És una excepció a la regla 4 limitada a aquest
# mode: la web ho mostra com a «proposta de la IA, pot equivocar-se».
#
# A 5-6 tok/s una resolució triga desenes de segons: es fa en streaming perquè
# l'alumne vegi els passos a mesura que surten.

# Ordre del fundador (15/11/2026): al xat la IA no s'enrotlla. Sense salutacions
# ni voltes, directa i precisa; ha de tardar la meitat. Aquest prompt no surt al xat.
SYSTEM_SOLVE_CURT = (
    "Ets un mentor de matemàtiques per a alumnes de 10 a 14 anys. Català, directe i precís. "
    "Mai saludes, no repeteixes l'enunciat ni cap càlcul i no fas voltes.\n"
    "Si et demanen resoldre: màxim 4 passos numerats, un per línia, un càlcul per pas; "
    "després una línia «Resultat: ...» (amb la lletra si hi ha opcions A–E) i res més. Format:\n"
    "1. Caramels: $4 \\cdot 6 = 24$.\n"
    "2. Em queden: $24 - 5 = 19$.\n"
    "Resultat: 19 caramels\n"
    "Si l'alumne pregunta: 1 o 2 frases, sense numerar. Si no n'estàs segur, ho dius."
)
# 15/11/2026: prompt del xat amb regles i exemples resolts. Es llegeix un sol cop i es
# desa a disc (vegeu «el prompt de sistema, llegit un sol cop»): la seva llargada no costa
# temps a l'alumne. Mesurat al Mac amb el codi de la placa, 31 problemes inventats que no
# es van fer servir per dissenyar-lo, 3 llavors (results/chat_quality/): encerta 9-11 de
# 31 (el curt, 3-4), arriba a «Resultat» el 74-87 % dels cops (el curt, 48-61 %) i escriu
# menys tokens. Mentre no és desat a la placa, el xat fa servir SYSTEM_SOLVE_CURT.
SYSTEM_SOLVE = "Ets un mentor de matemàtiques per a alumnes de 10 a 14 anys. Reps un problema i el resols.\nRegles:\n- Escrius sempre en català, encara que el problema estigui en castellà.\n- Com a màxim 4 passos numerats, un per línia. Cada pas: una etiqueta curta, dos punts i un càlcul entre $ $.\n- Sense negreta, sense guions i sense subapartats.\n- Després, una sola línia «Resultat: …» amb la resposta i la unitat. Si el problema té opcions A–E, hi poses la lletra i el valor; si no en té, cap lletra.\n- No saludes, no copies l'enunciat i no escrius res després del resultat.\n- Si després l'alumne fa una pregunta, li respons amb 1 o 2 frases curtes en català, sense numerar i sense «Resultat».\n\nExemples:\n\nProblema: Un llibre costa 12 € i un bolígraf 3 €. Compro 2 llibres i 4 bolígrafs. Quant pago en total?\nA) 15 €   B) 30 €   C) 36 €   D) 40 €   E) 48 €\nResolució en català:\n1. Llibres: $2 \\cdot 12 = 24$ €.\n2. Bolígrafs: $4 \\cdot 3 = 12$ €.\n3. Total: $24 + 12 = 36$ €.\nResultat: C) 36 €\n\nProblema: Resol l'equació 4x + 5 = 29.\nResolució en català:\n1. Resto 5 als dos costats: $4x = 29 - 5 = 24$.\n2. Divideixo entre 4: $x = 24 : 4 = 6$.\nResultat: x = 6\n\nPregunta de l'alumne: No entenc el pas 2.\nResposta curta en català: Al pas 2 tenim $4x = 24$, que vol dir 4 vegades x: per trobar x sola dividim 24 entre 4.\n\nProblema: En una caja hay 48 lápices. Se reparten a partes iguales entre 6 niños y cada niño pierde 2. ¿Cuántos lápices le quedan a cada niño?\nResolució en català:\n1. Reparteixo: $48 : 6 = 8$ llapis.\n2. En perd 2: $8 - 2 = 6$ llapis.\nResultat: 6 llapis\n\nProblema: Penso un nombre, el multiplico per 2 i hi sumo 6. Obtinc 30. Quin nombre he pensat?\nA) 7   B) 9   C) 12   D) 18   E) 21\nResolució en català:\n1. Equació: $2x + 6 = 30$.\n2. Resto 6: $2x = 30 - 6 = 24$.\n3. Divideixo entre 2: $x = 24 : 2 = 12$.\nResultat: C) 12\n\nProblema: Uns pantalons de 40 € tenen un 15 % de descompte. Quants euros ens estalviem? Quant costen ara?\nResolució en català:\n1. Descompte: $0,15 \\cdot 40 = 6$ €.\n2. Preu nou: $40 - 6 = 34$ €.\nResultat: ens estalviem 6 € i ara costen 34 €\n\nPregunta de l'alumne: He restat 40 − 15 i em surt 25. Està bé?\nResposta curta en català: El 15 % no són 15 €: primer cal trobar el 15 % de 40, que són 6 €, i després restar-los.\n\nProblema: Una ruleta té 8 sectors iguals: 3 verds i 5 grocs. Quina és la probabilitat que surti verd?\nA) 3/5   B) 5/8   C) 1/3   D) 3/8   E) 1/8\nResolució en català:\n1. Casos favorables: 3.\n2. Casos possibles: 8.\nResultat: D) 3/8\n\nProblema: Un menú té 3 primers, 4 segons i 2 postres. Quants menús diferents es poden triar?\nResolució en català:\n1. Multiplico les opcions: $3 \\cdot 4 \\cdot 2 = 24$.\nResultat: 24 menús\n\nPregunta de l'alumne: I si hi hagués 3 postres?\nResposta curta en català: Llavors serien $3 \\cdot 4 \\cdot 3 = 36$ menús, perquè només canvia l'últim nombre.\n\nProblema: Rosa es más alta que Quim. Quim es más alto que Sara. Tina es más alta que Rosa. Ordénalos de más alto a más bajo.\nResolució en català:\n1. La Tina és més alta que la Rosa, la Rosa més que en Quim i en Quim més que la Sara.\nResultat: Tina, Rosa, Quim, Sara\n\nProblema: Una classe té 30 alumnes. 2/5 hi van a peu, 1/2 en autobús i la resta en cotxe. Quants hi van en cotxe?\nResolució en català:\n1. A peu: $30 : 5 \\cdot 2 = 12$.\n2. En autobús: $30 : 2 = 15$.\n3. En cotxe: $30 - 12 - 15 = 3$.\nResultat: 3 alumnes\n\nPregunta de l'alumne: He fet 30 − 2/5 − 1/2 i em surt 29,1. Què he fet malament?\nResposta curta en català: Les fraccions són parts dels 30 alumnes: primer cal saber quants alumnes són 2/5 i 1/2 de 30, i després restar-los.\n\nProblema: Un coche recorre 150 km en 2 horas. ¿Cuántos kilómetros recorre en 5 horas a la misma velocidad?\nResolució en català:\n1. En una hora: $150 : 2 = 75$ km.\n2. En 5 hores: $75 \\cdot 5 = 375$ km.\nResultat: 375 km\n\nProblema: Problema 4.\nLa Mireia fa una festa d'aniversari un dissabte a la tarda. Hi convida\n11 amics, i comptant-la a ella seran 12 persones. Vol que cada persona\ntingui 3 entrepans petits. A la fleca cada entrepà costa 2 €.\nQuant costen tots els entrepans?\n(A) 24 € (B) 36 € (C) 66 € (D) 72 € (E) 78 €\nResolució en català:\n1. Entrepans: $12 \\cdot 3 = 36$.\n2. Cost: $36 \\cdot 2 = 72$ €.\nResultat: D) 72 €"
SOLVE_PREFILL = "1."  # la resposta comença pel primer pas: res de salutacions ni «No.»

# Límits de llargada (tokens): la resolució i la resposta a una pregunta
SOLVE_TOKENS = 130
ANSWER_TOKENS = 70


def _solve_messages(own_text, example, history=(), message="", long=None):
    """Els missatges del xat: el format llarg si el seu prompt de sistema és desat a la placa."""
    if long is None:
        long = long_prompt_ready()
    if not long:
        return _solve_messages_curt(own_text, example, history, message)
    turns = []
    for turn in list(history)[-4:]:  # els últims 2 torns (alumne + IA)
        role = "assistant" if turn.get("role") == "assistant" else "user"
        text = str(turn.get("text") or "").strip()[:600]
        if text:
            turns.append({"role": role, "content": text})
    problem = "Problema: " + own_text.strip()[:900]
    if example and example.get("key_idea"):
        problem += "\nPista: " + example["key_idea"]
    first = [{"role": "system", "content": SYSTEM_SOLVE},
             {"role": "user", "content": problem + "\nResolució en català:"}]
    if not message:
        return first + [{"role": "assistant", "content": SOLVE_PREFILL}]
    ask = "Pregunta de l'alumne: " + message.strip()[:300] + "\nResposta curta en català:"
    return first + turns + [{"role": "user", "content": ask}]


def _solve_messages_curt(own_text, example, history=(), message=""):
    """El format d'abans del 15/11 (prompt curt): la reserva mentre el llarg no és a punt."""
    context = _own_context(own_text, example)
    turns = []
    for turn in list(history)[-4:]:  # els últims 2 torns (alumne + IA)
        role = "assistant" if turn.get("role") == "assistant" else "user"
        text = str(turn.get("text") or "").strip()[:600]
        if text:
            turns.append({"role": role, "content": text})
    solve = ("Resol el problema de l'alumne pas a pas"
             + (", fent servir la mateixa idea que l'exemple" if example else "") + ".")
    # El primer missatge és sempre el mateix que el de la resolució: així una
    # pregunta de seguiment comença igual que el prompt que la placa ja ha llegit,
    # llama-server en reaprofita la lectura i només llegeix el que és nou.
    first = [{"role": "system", "content": SYSTEM_SOLVE_CURT},
             {"role": "user", "content": context + "\n" + solve}]
    if not message:
        return first
    ask = (f"L'ALUMNE PREGUNTA: «{message.strip()[:300]}»\n"
           "Respon en 1 o 2 frases, sobre el seu problema.")
    return first + turns + [{"role": "user", "content": ask}]


def warm_solve_later(own_text, example):
    """Llegeix per endavant el problema propi amb el prompt del xat (no bloqueja)."""
    _schedule_warm(_solve_messages(own_text, example)[:2])
    _ensure_long_prompt()


_RESULT_LINE = re.compile(r"Resultat\**\s*:[^\n]*\S[^\n]*\n", re.I)


def _finished(text):
    """Cert quan ja hi ha una línia «Resultat: ...» acabada."""
    return bool(_RESULT_LINE.search(text))


class _ThinkFilter:
    """Treu els blocs <think>…</think> d'un text que arriba a trossos."""

    TAG = "<think>"

    def __init__(self):
        self.raw = ""
        self.sent = 0

    def _visible(self):
        visible = re.sub(r"<think>.*?</think>", "", self.raw, flags=re.S)
        if self.TAG in visible:  # pensament encara obert: no s'ensenya res més
            visible = visible[:visible.index(self.TAG)]
        return visible.replace("</think>", "")

    def feed(self, chunk):
        self.raw += chunk
        visible = self._visible()
        # Un tros final com «<thi» pot ser l'inici de <think>: s'espera el següent
        hold = max((k for k in range(1, len(self.TAG)) if visible.endswith(self.TAG[:k])), default=0)
        safe = len(visible) - hold
        if self.sent == 0:  # sense espais ni salts de línia al principi
            self.sent = min(len(visible) - len(visible.lstrip()), safe)
        out = visible[self.sent:safe]
        self.sent = max(self.sent, safe)
        return out

    def text(self):
        return self._visible().strip()


def solve_own_stream(own_text, example, history=(), message="", max_tokens=None):
    """Generador: dona trossos de text a mesura que la IA els escriu.

    Al final dona un dict amb els temps (`timings`). Llança OSError si la IA no
    respon abans de començar; si es talla a mig camí, també. Para quan acaba la
    línia «Resultat: ...»: el que vingui després només són voltes.
    """
    _cancel_pending_warm()  # la pregunta de l'alumne passa davant
    if max_tokens is None:
        max_tokens = ANSWER_TOKENS if message else SOLVE_TOKENS
    _ensure_long_prompt()
    messages = _solve_messages(own_text, example, history, message)
    prefill = messages[-1]["content"] if messages[-1]["role"] == "assistant" else ""
    one_line = bool(message) and messages[0]["content"] == SYSTEM_SOLVE  # seguiment del format llarg
    _prepare_slot(messages)
    payload = {
        "messages": messages,
        "max_tokens": max_tokens, "temperature": 0.2, "seed": 42,
        "cache_prompt": True, "stream": True,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    request = urllib.request.Request(
        config.LLM_URL + "/v1/chat/completions", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"})
    started = time.perf_counter()
    first = None
    timings = {}
    think = _ThinkFilter()
    if prefill:  # el model continua el que ja hi ha: l'alumne ho veu sencer
        yield think.feed(prefill)
        first = round(time.perf_counter() - started, 2)
    with urllib.request.urlopen(request, timeout=config.LLM_STREAM_TIMEOUT) as response:
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                event = json.loads(data)
            except ValueError:
                continue
            if event.get("timings"):
                timings = event["timings"]
            choices = event.get("choices") or [{}]
            chunk = (choices[0].get("delta") or {}).get("content") or ""
            if chunk:
                stop = False
                if one_line and "\n" in chunk and think.text():
                    chunk, stop = chunk.split("\n")[0], True  # una resposta = una línia
                out = think.feed(chunk)
                if out:
                    if first is None:
                        first = round(time.perf_counter() - started, 2)
                    yield out
                if stop or _finished(think.text() + chunk[-1:]):
                    break  # tancar la connexió atura la generació a llama-server
    timings = dict(timings)
    timings["wall_seconds"] = round(time.perf_counter() - started, 2)
    timings["first_token_seconds"] = first
    yield {"timings": timings, "text": think.text()}
