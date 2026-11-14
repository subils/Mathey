"""La lògica del mentor. Cada funció pública és una ruta de l'API (vegeu api.py).

Principis:
- La resposta correcta no surt cap a la web fins que l'alumne demana la solució
  (o l'encerta).
- Només es fan servir problemes amb contingut **verificat**: la solució de
  l'agent coincideix amb la resposta oficial.
- Tot el text que arriba a l'alumne passa pel filtre de filtracions.
"""
import os
import re
import time
import zlib

import base64
import binascii
import json

from . import config, elo, filters, llm, matrix, router, store, strategies

_current_matrix = matrix.idle()
_ID = re.compile(r"^lvl-\d_\d{4}_\d+$")


class UserError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------- dades

def _content(pid):
    row = store.one(store.bank(), "SELECT * FROM content WHERE id = ? AND verified = 1", (pid,))
    if not row:
        return None
    for key, default in (("hints", []), ("solution", []), ("traps", {}), ("options", {})):
        row[key] = store.loads(row[key], default)
    return row


def _problem_row(pid, lang="cat"):
    return store.one(store.bank(), "SELECT * FROM problems WHERE id = ? AND lang = ?", (pid, lang))


def _public(pid, lang="cat"):
    """El que la web pot saber d'un problema: mai la resposta."""
    content = _content(pid)
    row = _problem_row(pid, lang) or _problem_row(pid, "cat")
    if not content or not row:
        return None
    return {
        "id": pid,
        "level": row["level"],
        "elo": _problem_elo(pid),
        "year": row["year"],
        "topic": content["topic"],
        "has_figure": not row["text_only"],
        "text": row["text"],
        "easy_text": content["easy_text"],
        "options": content["options"],
        "image_url": f"/api/image?id={pid}&lang={row['lang']}",
    }


def _student(params):
    try:
        sid = int(params.get("student"))
    except (TypeError, ValueError):
        raise UserError(400, "falta l'alumne")
    row = store.one(store.state(), "SELECT * FROM students WHERE id = ?", (sid,))
    if not row:
        raise UserError(404, "alumne desconegut")
    return row


# ---------------------------------------------------------------- Elo (vegeu elo.py)

def _initial_problem_elo(pid):
    """Elo inicial a partir de l'id: lvl-<nivell>_<any>_<número de pregunta>."""
    level, number = int(pid[4]), int(pid.rsplit("_", 1)[1])
    return elo.problem_elo(level, number)


def _problem_elos():
    """Elo actual dels problemes que ja han rebut respostes (la resta: l'inicial)."""
    return {r["id"]: r["elo"] for r in store.query(store.state(), "SELECT id, elo FROM problem_elo")}


def _problem_elo(pid):
    row = store.one(store.state(), "SELECT elo FROM problem_elo WHERE id = ?", (pid,))
    return round(row["elo"]) if row else _initial_problem_elo(pid)


def _student_elo(student):
    if student.get("elo") is not None:
        return round(student["elo"])
    return elo.initial_student_elo(student["level"])  # alumnes d'abans de l'Elo


def _start_elo(student):
    """Elo de partida de l'alumne (el del seu curs): el punt de partida d'elo.estimate()."""
    if student.get("grade") in config.GRADE_LEVEL:
        return elo.initial_elo_for_grade(student["grade"], config.MAX_LEVEL)
    return elo.initial_student_elo(student["level"])


def _elo_answers(sid):
    """Les respostes que compten per a l'Elo (el primer intent de cada problema), de la
    més antiga a la més recent: [(Elo del problema quan el va fer, resultat), ...]."""
    rows = store.query(store.state(), """SELECT problem_id, correct, hints_used, problem_elo, elo_score
        FROM attempts WHERE student_id = ? AND first_try = 1 ORDER BY id DESC LIMIT ?""",
                       (sid, elo.MAX_ANSWERS))
    answers = []
    for r in reversed(rows):
        rating = r["problem_elo"] if r["problem_elo"] is not None else _initial_problem_elo(r["problem_id"])
        # Intents d'abans de desar elo_score: el resultat es refà amb encert i ajudes
        result = r["elo_score"] if r["elo_score"] is not None else elo.score(r["correct"], r["hints_used"] or 0)
        answers.append((rating, result))
    return answers


def _target_elo(params, student):
    """L'Elo que l'alumne vol practicar (paràmetre `elo`) o, si no en tria cap, el seu."""
    raw = params.get("elo")
    if raw in (None, ""):
        return _student_elo(student)
    try:
        return min(max(int(float(raw)), 400), 2800)
    except (TypeError, ValueError):
        raise UserError(400, "l'Elo ha de ser un número")


_matrix_listeners = []


def on_matrix(listener):
    """Registra una funció que rep cada dibuix nou (la placa: pintar els LEDs)."""
    _matrix_listeners.append(listener)


def _set_matrix(frame):
    global _current_matrix
    _current_matrix = frame
    for listener in _matrix_listeners:
        try:
            listener(frame)
        except Exception:  # la matriu no pot fer caure una resposta a l'alumne
            pass
    return frame


def _correct(pid):
    row = _problem_row(pid, "cat")
    content = _content(pid)
    if not row or not content:
        raise UserError(404, "problema desconegut")
    label = row["label"]
    return label, content["options"].get(label, ""), content, row


def _safe_key_idea(content, label, option, row):
    """La idea clau, si no revela la resposta (filters.leaks); si la revela, None.

    Les pistes ja es filtren en construir el banc; la idea clau no, i per això es
    filtra aquí cada cop que arriba a l'alumne abans de resoldre el problema.
    """
    idea = content.get("key_idea") or ""
    return idea if idea and not filters.leaks(idea, label, option, row["text"]) else None


# ---------------------------------------------------------------- rutes

def health(_params):
    verified = store.one(store.bank(), "SELECT COUNT(*) AS n FROM content WHERE verified = 1")
    total = store.one(store.bank(), "SELECT COUNT(DISTINCT id) AS n FROM problems")
    return {
        "ok": True,
        "mock": False,
        "host": config.HOST,
        "problems": verified["n"] if verified else 0,
        "bank_problems": total["n"] if total else 0,
        "llm": "up" if llm.available() else "down",
        "embeddings": "tf-idf",
        "matrix": "placa" if config.HOST == "placa" else "simulada",
        "server_time": time.strftime("%H:%M:%S"),
    }


def create_session(params):
    alias = (params.get("alias") or "").strip()[:30]
    grade = params.get("grade") or ""
    if not alias:
        raise UserError(400, "cal un àlies")
    if grade not in config.GRADE_LEVEL:
        raise UserError(400, f"curs desconegut: tria'n un de {', '.join(config.GRADE_LEVEL)}")
    easy = 1 if params.get("easy_mode") else 0
    # El curs només serveix per triar l'Elo inicial; a partir d'aquí tot va per Elo
    rating = elo.initial_elo_for_grade(grade, config.MAX_LEVEL)
    # La columna `level` és el número de la matriu de LEDs (derivat de l'Elo)
    sid = store.execute(store.state(),
                        "INSERT INTO students (alias, grade, level, easy_mode, elo, elo_attempts) "
                        "VALUES (?, ?, ?, ?, ?, 0)", (alias, grade, _led_level(rating), easy, rating))
    return {"student": sid, "alias": alias, "grade": grade, "elo": rating, "streak": 0,
            "easy_mode": bool(easy), "matrix": _set_matrix(_led_frame(rating))}


def _led_level(rating):
    """El número que surt a la matriu de LEDs: el nivell del Cangur que correspon a l'Elo."""
    return elo.led_level(rating, config.MAX_LEVEL)


def _led_frame(rating, streak=0):
    return matrix.level(_led_level(rating), streak)


def _elo_range():
    """[mínim, màxim] de l'Elo dels problemes amb contingut verificat (on es pot practicar)."""
    rows = store.query(store.bank(), """
        SELECT c.id FROM content c JOIN problems p ON p.id = c.id AND p.lang = 'cat'
        WHERE c.verified = 1 AND p.level <= ?""", (config.MAX_LEVEL,))
    current = _problem_elos()
    values = [current.get(r["id"], _initial_problem_elo(r["id"])) for r in rows]
    return [round(min(values)), round(max(values))] if values else None


def _topic_scores(sid):
    rows = store.query(store.state(), """
        SELECT topic, COUNT(*) AS n, SUM(correct) AS ok FROM attempts
        WHERE student_id = ? AND first_try = 1 GROUP BY topic""", (sid,))
    return {r["topic"]: ((r["ok"] or 0) + 1) / (r["n"] + 2) for r in rows}, {r["topic"]: r["n"] for r in rows}


ELO_WINDOWS = (100, 200, 400)  # es busca a ±100 de l'Elo objectiu; si no n'hi ha, s'amplia


def _pick(sid, target):
    """Un problema no fet amb l'Elo més a prop de `target`; dins la finestra, el tema més fluix."""
    seen = {r["problem_id"] for r in store.query(
        store.state(), "SELECT DISTINCT problem_id FROM attempts WHERE student_id = ?", (sid,))}
    rows = store.query(store.bank(), """
        SELECT c.id, c.topic FROM content c JOIN problems p ON p.id = c.id AND p.lang = 'cat'
        WHERE c.verified = 1 AND p.level <= ? ORDER BY c.id""", (config.MAX_LEVEL,))
    rows = [r for r in rows if r["id"] not in seen]
    if not rows:
        return None
    current = _problem_elos()
    for r in rows:
        r["distance"] = abs(current.get(r["id"], _initial_problem_elo(r["id"])) - target)
    pool = []
    for window in ELO_WINDOWS:
        pool = [r for r in rows if r["distance"] <= window]
        if pool:
            break
    if not pool:  # cap prou a prop: els 5 més propers
        pool = sorted(rows, key=lambda r: (r["distance"], r["id"]))[:5]
    scores, counts = _topic_scores(sid)
    by_topic = {}
    for r in pool:
        by_topic.setdefault(r["topic"], []).append(r["id"])
    # El tema més fluix primer; a igualtat, el menys practicat
    topic = min(by_topic, key=lambda t: (scores.get(t, 0.5), counts.get(t, 0), t))
    ids = by_topic[topic]
    return ids[zlib.crc32(f"{sid}:{len(seen)}".encode()) % len(ids)]


def next_problem(params):
    student = _student(params)
    pid = params.get("id")
    if pid:
        if not _content(pid):
            raise UserError(404, "problema sense contingut verificat")
    target = _target_elo(params, student)
    if not pid:
        pid = _pick(student["id"], target)
    if not pid:
        return {"problem": None, "message": "Has fet tots els problemes! Parla amb el teu mestre."}
    rating = _student_elo(student)
    return {"problem": _public(pid), "elo": rating, "target_elo": target, "elo_range": _elo_range(),
            "streak": student["streak_ok"],
            "matrix": _set_matrix(_led_frame(rating, student["streak_ok"]))}


def get_problem(params):
    problem = _public(params.get("id", ""), params.get("lang", "cat"))
    if not problem:
        raise UserError(404, "problema desconegut")
    return {"problem": problem}


def image_path(pid, lang):
    if not _ID.match(pid or "") or lang not in ("cat", "eng"):
        return None, None
    path = os.path.join(config.IMAGES, f"{pid}_{lang}.png")
    return (path, "image/png") if os.path.isfile(path) else (None, None)


def answer(params):
    student = _student(params)
    pid = params.get("problem_id", "")
    letter = (params.get("letter") or "").upper()
    if letter not in ("A", "B", "C", "D", "E"):
        raise UserError(400, "la resposta ha de ser A, B, C, D o E")
    label, option, content, row = _correct(pid)
    correct = letter == label
    db = store.state()
    first_try = store.one(db, "SELECT COUNT(*) AS n FROM attempts WHERE student_id = ? AND problem_id = ?",
                          (student["id"], pid))["n"] == 0
    hints_used = store.one(db, "SELECT COUNT(DISTINCT rung) AS n FROM hints WHERE student_id = ? AND problem_id = ?",
                           (student["id"], pid))["n"]
    # Ratxa (per a la web i la barra de la matriu): encerts seguits al primer intent i
    # sense ajudes. Ja no fa pujar ni baixar res: l'únic que mana és l'Elo.
    streak = student["streak_ok"]

    # Elo, com als escacs: una partida per problema, la primera resposta. Qui ha
    # vist la solució abans de respondre la perd; cada ajuda resta (elo.score).
    rating_before = _student_elo(student)
    problem_before = _problem_elo(pid)
    rating_after, problem_after, result_score = rating_before, problem_before, None
    if first_try:
        if correct and hints_used == 0:
            streak += 1
        elif not correct:
            streak = 0
        saw_solution = store.one(db, "SELECT COUNT(*) AS n FROM hints WHERE student_id = ? AND problem_id = ? "
                                     "AND rung = 5", (student["id"], pid))["n"] > 0
        result_score = 0.0 if saw_solution else elo.score(correct, hints_used)
        # El problema: Elo clàssic (K petita). L'alumne: estimació amb totes les respostes.
        _, problem_after = elo.update(rating_before, problem_before, result_score)
        rating_after = elo.estimate(_start_elo(student),
                                    _elo_answers(student["id"]) + [(problem_before, result_score)])
        # `level` només és el número de la matriu de LEDs, derivat del nou Elo
        store.execute(db, "UPDATE students SET elo = ?, elo_attempts = COALESCE(elo_attempts, 0) + 1, "
                          "level = ?, streak_ok = ?, streak_bad = 0 WHERE id = ?",
                      (rating_after, _led_level(rating_after), streak, student["id"]))
        store.execute(db, """INSERT INTO problem_elo (id, elo, attempts) VALUES (?, ?, 1)
                             ON CONFLICT(id) DO UPDATE SET elo = excluded.elo, attempts = attempts + 1""",
                      (pid, problem_after))

    try:
        seconds = float(params.get("seconds") or 0)
    except (TypeError, ValueError):
        seconds = 0.0
    store.execute(db, """INSERT INTO attempts (student_id, problem_id, letter, correct, first_try,
                         hints_used, seconds, level, topic, elo_before, elo_after, problem_elo, elo_score)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (student["id"], pid, letter, int(correct), int(first_try), hints_used, seconds,
                   row["level"], content["topic"], rating_before, rating_after, problem_before, result_score))
    result = {"correct": correct, "first_try": first_try,
              "streak": streak, "elo": rating_after, "elo_change": rating_after - rating_before,
              "problem_elo": problem_before,
              "matrix": _set_matrix(matrix.check() if correct else matrix.cross())}
    if correct:
        result.update({"answer": label, "answer_text": option,
                       "solution": content["solution"], "key_idea": content["key_idea"]})
    return result


def _germa(pid, content, student_id):
    """El problema germà: mateix tema, Elo més baix (o igual), el més semblant."""
    here = _problem_elo(pid)
    current = _problem_elos()
    solved = {r["problem_id"] for r in store.query(
        store.state(), "SELECT problem_id FROM attempts WHERE student_id = ? AND correct = 1", (student_id,))}
    candidates = store.query(store.bank(), """
        SELECT n.neighbor_id AS id, n.score, c.topic FROM neighbors n
        JOIN content c ON c.id = n.neighbor_id AND c.verified = 1
        JOIN problems p ON p.id = n.neighbor_id AND p.lang = 'cat'
        WHERE n.id = ? ORDER BY n.rank""", (pid,))
    best = None
    for c in candidates:
        rating = current.get(c["id"], _initial_problem_elo(c["id"]))
        if c["id"] in solved or rating > here:
            continue
        key = (c["topic"] == content["topic"], rating < here, c["score"])
        if best is None or key > best[0]:
            best = (key, c["id"])
    return _public(best[1]) if best else None


def hint(params):
    student = _student(params)
    pid = params.get("problem_id", "")
    try:
        rung = int(params.get("rung"))
    except (TypeError, ValueError):
        raise UserError(400, "graó no vàlid")
    if not 1 <= rung <= 5:
        raise UserError(400, "el graó va de 1 a 5")
    label, option, content, row = _correct(pid)
    if rung == 5 and not params.get("confirm"):
        raise UserError(400, "per veure la solució cal confirmar-ho")
    store.execute(store.state(), "INSERT INTO hints (student_id, problem_id, rung) VALUES (?, ?, ?)",
                  (student["id"], pid, rung))
    hints = content["hints"] + [None] * 3
    if rung == 3:
        sibling = _germa(pid, content, student["id"])
        return {"rung": 3, "type": "germa", "problem": sibling,
                "text": "Prova primer aquest problema: és més fàcil i fa servir una idea semblant."
                if sibling else (_safe_key_idea(content, label, option, row)
                                 or "Per a aquest problema no tinc cap germà més fàcil. Prova el graó següent.")}
    if rung == 5:
        return {"rung": 5, "type": "solucio", "steps": content["solution"],
                "answer": label, "answer_text": option}
    text = hints[{1: 0, 2: 1, 4: 2}[rung]]
    if text and filters.leaks(text, label, option, row["text"]):
        text = None
    return {"rung": rung, "type": {1: "estrategia", 2: "dada_clau", 4: "primer_pas"}[rung],
            "text": text, "blocked": text is None}


def explain(params):
    student = _student(params)
    pid = params.get("problem_id", "")
    letter = (params.get("letter") or "").upper()
    said = (params.get("text") or "").strip()
    if not said:
        raise UserError(400, "explica en una frase com ho has pensat")
    label, option, content, row = _correct(pid)
    trap = content["traps"].get(letter, "") if letter != label else ""
    chosen = f"{letter}) {content['options'].get(letter, '')}" if letter else "cap"
    reply, source, rejected, timings = None, "placa", None, {}
    started = time.perf_counter()
    # Router sense IA (mentor/router.py): si la frase descriu la trampa de l'opció triada,
    # la resposta preparada arriba a l'instant i el model de la placa queda lliure.
    instant, _decision = router.instant_reply(said, letter, label, option, content, row["text"])
    if instant:
        reply, source = instant, "instant"
    else:
        before = _current_matrix
        _set_matrix(matrix.thinking())
        try:
            text, timings = llm.socratic(row["text"], content["solution"], chosen, trap, said)
            rejected = filters.leaks(text, label, option, row["text"], strict = True) or (
                "" if filters.is_question(text) else "no és una pregunta curta")
            if not rejected:
                reply = text
        except OSError as error:
            rejected = f"la IA de la placa no respon ({type(error).__name__})"
        except Exception as error:  # resposta inesperada: l'alumne rep igualment la reserva
            rejected = f"resposta inesperada de la IA ({type(error).__name__})"
        finally:
            _set_matrix(before)
    if reply is None:
        # Reserva: l'error típic d'aquesta opció (preparat i verificat), o la dada clau
        source = "preparat"
        if trap and not filters.leaks(trap, label, option, row["text"]):
            reply = f"Un error típic de qui tria la {letter}: {trap.rstrip('.')}. Pot ser el teu cas?"
        else:
            reply = (content["hints"][1] if len(content["hints"]) > 1 and content["hints"][1]
                     else _safe_key_idea(content, label, option, row)
                     or "Torna a llegir l'enunciat amb calma: quina dada encara no has fet servir?")
    seconds = round(time.perf_counter() - started, 2)
    store.execute(store.state(), """INSERT INTO explanations (student_id, problem_id, letter, student_text,
                  reply, source, seconds, rejected) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (student["id"], pid, letter, said, reply, source, seconds, rejected))
    return {"reply": reply, "source": source, "seconds": seconds, "rejected": rejected or None,
            "timings": {k: timings.get(k) for k in ("prompt_n", "prompt_per_second", "predicted_n",
                                                    "predicted_per_second", "wall_seconds") if k in timings}}


def warm(params):
    pid = params.get("problem_id", "")
    _label, _option, content, row = _correct(pid)
    llm.warm_later(row["text"], content["solution"])  # no bloqueja i no fa cua
    return {"started": True}


def profile(params):
    student = _student(params)
    sid = student["id"]
    rows = store.query(store.state(), """
        SELECT topic, COUNT(*) AS n, SUM(correct) AS ok, AVG(hints_used) AS hints FROM attempts
        WHERE student_id = ? AND first_try = 1 GROUP BY topic ORDER BY topic""", (sid,))
    total = sum(r["n"] for r in rows)
    ok = sum(r["ok"] or 0 for r in rows)
    recent = store.query(store.state(), """SELECT problem_id, letter, correct, hints_used, topic,
        problem_elo, elo_before, elo_after, ts
        FROM attempts WHERE student_id = ? AND first_try = 1 ORDER BY id DESC LIMIT 10""", (sid,))
    rating = _student_elo(student)
    history = store.query(store.state(), """SELECT elo_before, elo_after FROM attempts
        WHERE student_id = ? AND first_try = 1 AND elo_after IS NOT NULL ORDER BY id""", (sid,))
    return {
        "alias": student["alias"], "grade": student["grade"],
        "elo": rating,
        # Elo amb què va començar i el més alt que ha tingut
        "elo_start": round(history[0]["elo_before"]) if history else rating,
        "elo_peak": round(max([rating] + [h["elo_after"] for h in history])),
        "streak": student["streak_ok"], "attempts": total, "correct": ok,
        "accuracy": round(ok / total, 3) if total else None,
        "by_topic": [{"topic": r["topic"], "attempts": r["n"], "correct": r["ok"] or 0,
                      "accuracy": round((r["ok"] or 0) / r["n"], 3), "avg_hints": round(r["hints"] or 0, 2)}
                     for r in rows],
        "recent": recent,
    }


def current_matrix(_params):
    return {"matrix": _current_matrix}


def _memory():
    """Memòria del sistema en MB (Linux: /proc/meminfo). Al Mac no n'hi ha: None."""
    try:
        with open("/proc/meminfo") as f:
            info = {line.split(":")[0]: int(line.split()[1]) for line in f if ":" in line}
        return {"total_mb": info["MemTotal"] // 1024, "available_mb": info["MemAvailable"] // 1024}
    except (OSError, KeyError, ValueError, IndexError):
        return None


def stats(_params):
    """Sala de màquines: què fa la placa, amb números mesurats en aquesta sessió."""
    db = store.state()
    explained = store.query(db, "SELECT source, seconds FROM explanations ORDER BY id DESC LIMIT 200")
    live = sorted(e["seconds"] for e in explained if e["source"] == "placa")
    instant = sum(1 for e in explained if e["source"] == "instant")
    meta ={r["key"]: r["value"] for r in store.query(store.bank(), "SELECT key, value FROM meta")}
    verified = store.one(store.bank(), "SELECT COUNT(*) AS n FROM content WHERE verified = 1")["n"]
    prepared = store.one(store.bank(), "SELECT COUNT(*) AS n FROM content")["n"]
    return {
        "host": config.HOST,
        "llm": "up" if llm.available() else "down",
        "memory": _memory(),
        "bank": {"verified": verified, "prepared": prepared, "built_at": meta.get("built_at")},
        "students": store.one(db, "SELECT COUNT(*) AS n FROM students")["n"],
        "attempts": store.one(db, "SELECT COUNT(*) AS n FROM attempts")["n"],
        "hints": store.one(db, "SELECT COUNT(*) AS n FROM hints")["n"],
        "questions": {
            "total": len(explained),
            "from_board": len(live),
            "instant": instant,  # router sense IA: la frase descrivia la trampa
            "fallback": len(explained) - len(live) - instant,
            "median_seconds": live[len(live) // 2] if live else None,
            "worst_seconds": live[-1] if live else None,
        },
        "internet": "no cal: tot passa en aquesta placa",
    }


# ------------------------------------------------------- «Porta el teu problema»
#
# L'alumne puja la foto d'un problema seu (deures, llibre, examen):
#   1. own_ocr    la placa llegeix la imatge amb laptop/read_image.py (mentor/ocr.py):
#                 l'enunciat i les opcions A–E són el prompt del problema
#   2. own_match  es busquen problemes semblants del banc i es desa el problema
#   3. own_help   l'alumne diu on s'encalla i la IA de la placa, amb el problema
#                 semblant ja resolt com a exemple, li dona una pista per continuar
# El mentor no sap la resposta del problema de l'alumne: mai n'afirma cap.

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_OWN_WORDS = 45
# Problemes semblants: se'n busquen uns quants i es prefereixen els que no passen
# de l'Elo de l'alumne més aquest marge (un pèl més difícils encara serveixen)
OWN_CANDIDATES = 20
OWN_ELO_MARGIN = 100


def own_ocr(params):
    student = _student(params)
    raw = params.get("image") or ""
    if "," in raw[:80]:  # data:image/jpeg;base64,....
        raw = raw.split(",", 1)[1]
    try:
        image = base64.b64decode(raw, validate=False)
    except (binascii.Error, ValueError):
        raise UserError(400, "la imatge no s'ha pogut llegir")
    if not image:
        raise UserError(400, "falta la imatge")
    if len(image) > MAX_IMAGE_BYTES:
        raise UserError(413, "la imatge és massa gran (màxim 8 MB)")
    from . import ocr  # import tardà: el lector d'imatges és opcional
    before = _current_matrix
    _set_matrix(matrix.thinking())
    try:
        result = ocr.read_image(image, params.get("lang") or "cat")
        ok = True
    except OSError as error:
        ok = False
        failure = str(error) or type(error).__name__
        rejected = getattr(error, "rejected", False)  # la imatge no val: no és cosa del lector
    finally:
        _set_matrix(before)
    if not ok:
        store.execute(store.state(), "INSERT INTO ocr_reads (student_id, engine, seconds, chars, ok) VALUES (?, ?, ?, ?, 0)",
                      (student["id"], "", 0, 0))
        if rejected:
            raise UserError(400, f"No he pogut llegir aquesta imatge: {failure}. Prova amb una altra foto.")
        raise UserError(503, f"El lector d'imatges no està disponible ({failure}). Pots escriure el problema a mà.")
    text = (result.get("text") or "").strip()
    store.execute(store.state(), "INSERT INTO ocr_reads (student_id, engine, seconds, chars, ok) VALUES (?, ?, ?, ?, 1)",
                  (student["id"], result.get("engine", ""), result.get("seconds", 0), len(text)))
    return {"text": text, "question": result.get("question", text), "options": result.get("options") or {},
            "engine": result.get("engine"), "seconds": result.get("seconds"), "empty": not text}


def _example(pid):
    """El problema semblant, com a exemple per a la IA: idea clau i primers passos."""
    content = _content(pid) if pid else None
    if not content:
        return None
    return {"id": pid, "key_idea": content["key_idea"], "solution": content["solution"]}


def own_match(params):
    student = _student(params)
    text = (params.get("text") or "").strip()
    if len(text.split()) < 4:
        raise UserError(400, "escriu l'enunciat del problema (com a mínim una frase)")
    text = text[:2000]
    from . import retrieval  # import tardà: construeix l'índex el primer cop
    topic, confidence = retrieval.guess_topic(text)
    # Primer, problemes fins a l'Elo de l'alumne (+ un marge); si no n'hi ha de prou semblants, tots
    candidates = retrieval.find_similar(text, k=OWN_CANDIDATES)
    ceiling = _student_elo(student) + OWN_ELO_MARGIN
    hits = [h for h in candidates if _problem_elo(h["id"]) <= ceiling][:3]
    low = getattr(retrieval, "LOW_SCORE", 0.0)
    if not hits or hits[0]["score"] < low:
        wider = candidates[:3]
        if wider and (not hits or wider[0]["score"] > hits[0]["score"]):
            hits = wider
    found = bool(hits) and hits[0]["score"] >= low
    siblings = []
    for hit in hits:
        public = _public(hit["id"])
        if public:
            siblings.append({**public, "score": round(float(hit["score"]), 4)})
    own_id = store.execute(store.state(), """INSERT INTO own_problems (student_id, text, topic,
        topic_confidence, siblings, best_score, found) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (student["id"], text, topic, float(confidence), json.dumps([s["id"] for s in siblings]),
         float(hits[0]["score"]) if hits else 0.0, int(found)))
    # Només un problema molt semblant guia la pista; els altres serveixen per practicar el tema
    guides = found and bool(siblings) and hits[0]["score"] >= retrieval.HIGH_SCORE
    # La IA llegeix ara el problema i l'exemple, mentre l'alumne escriu el seu dubte
    example = _example(siblings[0]["id"]) if guides else None
    # El xat (mode 2) fa servir el prompt de resolució: és el que es llegeix per endavant
    llm.warm_solve_later(text, example)  # no bloqueja i no fa cua
    return {"own_id": own_id, "topic": topic, "topic_confidence": round(float(confidence), 2),
            "found": found, "same_idea": guides, "siblings": siblings if found else [],
            "strategy": strategies.for_topic(topic),
            "message": None if found else "No he trobat cap problema prou semblant al banc, "
                                          "però et puc ajudar igualment si m'expliques on t'encalles."}


def own_help(params):
    student = _student(params)
    try:
        own_id = int(params.get("own_id"))
    except (TypeError, ValueError):
        raise UserError(400, "falta el problema")
    own = store.one(store.state(), "SELECT * FROM own_problems WHERE id = ? AND student_id = ?",
                    (own_id, student["id"]))
    if not own:
        raise UserError(404, "problema desconegut")
    doubt = (params.get("doubt") or "").strip()
    if len(doubt.split()) < 2:
        raise UserError(400, "explica on t'encalles, encara que sigui amb poques paraules")
    sibling_ids = store.loads(own["siblings"], [])
    from . import retrieval
    guides = own["found"] and sibling_ids and (own["best_score"] or 0) >= retrieval.HIGH_SCORE
    example = _example(sibling_ids[0]) if guides else None
    asked = store.one(store.state(), "SELECT COUNT(*) AS n FROM own_helps WHERE own_id = ?", (own_id,))["n"]
    strategy = strategies.for_topic(own["topic"], asked)
    reply, source, rejected, timings = None, "placa", None, {}
    started = time.perf_counter()
    before = _current_matrix
    _set_matrix(matrix.thinking())
    try:
        text, timings = llm.own_hint(own["text"], example, doubt, strategy)
        invented = filters.new_numbers(text, own["text"], doubt)
        if invented:
            rejected = f"escriu números que no són al problema ({', '.join(sorted(invented))})"
        elif not text or len(text.split()) > MAX_OWN_WORDS:
            rejected = "massa llarga o buida"
        else:
            reply = text
    except OSError as error:
        rejected = f"la IA de la placa no respon ({type(error).__name__})"
    except Exception as error:  # resposta inesperada: l'alumne rep igualment la reserva
        rejected = f"resposta inesperada de la IA ({type(error).__name__})"
    finally:
        _set_matrix(before)
    if reply is None:
        # Reserva sense IA: la idea del problema semblant, dita com el que és, o l'estratègia del tema
        source = "preparat"
        if example and example["key_idea"]:
            reply = (f"En un problema semblant del Cangur, la clau era: «{example['key_idea'].rstrip('.')}». "
                     "Mira si al teu problema pots fer servir la mateixa idea.")
        else:
            reply = strategy
    seconds = round(time.perf_counter() - started, 2)
    store.execute(store.state(), """INSERT INTO own_helps (own_id, doubt, reply, source, seconds, rejected)
                  VALUES (?, ?, ?, ?, ?, ?)""", (own_id, doubt, reply, source, seconds, rejected))
    return {"reply": reply, "source": source, "seconds": seconds, "rejected": rejected or None,
            "strategy": strategy,
            "sibling": _public(sibling_ids[0]) if example else None,
            "timings": {k: timings.get(k) for k in ("prompt_n", "prompt_per_second", "predicted_n",
                                                    "predicted_per_second", "wall_seconds") if k in timings}}


# ------------------------------------------------------------- xat del mode 2
#
# Ordre del fundador (14/11/2026): al xat la IA intenta resoldre el problema
# propi pas a pas (excepció a la regla 4 limitada a aquest mode). La resposta
# arriba en streaming: own_chat() valida ara i torna un generador d'esdeveniments
# (mentor/api.py l'embolica en un Stream i l'adaptador l'envia com a NDJSON):
#   {"type": "meta", "own_id", "sibling", "strategy"}
#   {"type": "delta", "text": "..."}            (un o més)
#   {"type": "done", "reply", "source", "seconds", "rejected", "timings"}

MAX_CHAT_CHARS = 1600


def _chat_fallback(example, strategy):
    """Sense IA: el problema semblant resolt, presentat com el que és, o l'estratègia."""
    if example and example.get("key_idea"):
        steps = "\n".join(f"{i}. {step}" for i, step in enumerate((example.get("solution") or [])[:4], 1))
        return ("Ara mateix la IA de la placa no pot respondre. Mentrestant, mira com es resol "
                f"un problema semblant del Cangur.\n\n**La idea clau:** {example['key_idea']}"
                + (f"\n\n{steps}" if steps else "")
                + "\n\nProva de fer el mateix amb el teu problema.")
    return f"Ara mateix la IA de la placa no pot respondre. Una manera de començar: {strategy}"


def own_chat(params):
    student = _student(params)
    try:
        own_id = int(params.get("own_id"))
    except (TypeError, ValueError):
        raise UserError(400, "falta el problema")
    own = store.one(store.state(), "SELECT * FROM own_problems WHERE id = ? AND student_id = ?",
                    (own_id, student["id"]))
    if not own:
        raise UserError(404, "problema desconegut")
    message = (params.get("message") or "").strip()[:300]
    history = params.get("history") or []
    if not isinstance(history, list):
        history = []
    sibling_ids = store.loads(own["siblings"], [])
    from . import retrieval
    guides = own["found"] and sibling_ids and (own["best_score"] or 0) >= retrieval.HIGH_SCORE
    example = _example(sibling_ids[0]) if guides else None
    strategy = strategies.for_topic(own["topic"])
    return _own_chat_events(own, example, strategy, history, message,
                            _public(sibling_ids[0]) if (own["found"] and sibling_ids) else None)


def _own_chat_events(own, example, strategy, history, message, sibling):
    yield {"type": "meta", "own_id": own["id"], "sibling": sibling, "strategy": strategy}
    parts, source, rejected, timings = [], "placa", None, {}
    started = time.perf_counter()
    before = _current_matrix
    _set_matrix(matrix.thinking())
    try:
        for piece in llm.solve_own_stream(own["text"], example, history, message):
            if isinstance(piece, dict):
                timings = piece.get("timings", {})
                continue
            parts.append(piece)
            yield {"type": "delta", "text": piece}
            if sum(map(len, parts)) > MAX_CHAT_CHARS:
                rejected = "massa llarga: s'ha tallat"
                break
    except OSError as error:
        rejected = f"la IA de la placa no respon ({type(error).__name__})"
    except Exception as error:  # resposta inesperada: l'alumne rep igualment la reserva
        rejected = f"resposta inesperada de la IA ({type(error).__name__})"
    finally:
        _set_matrix(before)
    reply = "".join(parts).strip()
    if not reply:
        source = "preparat"
        reply = _chat_fallback(example, strategy)
        yield {"type": "delta", "text": reply}
    seconds = round(time.perf_counter() - started, 2)
    store.execute(store.state(), """INSERT INTO own_helps (own_id, doubt, reply, source, seconds, rejected)
                  VALUES (?, ?, ?, ?, ?, ?)""", (own["id"], message or "(resol-lo)", reply, source, seconds, rejected))
    yield {"type": "done", "reply": reply, "source": source, "seconds": seconds,
           "rejected": rejected, "timings": {k: timings.get(k) for k in (
               "prompt_n", "prompt_per_second", "predicted_n", "predicted_per_second",
               "wall_seconds", "first_token_seconds") if k in timings}}
