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
import threading
import time
import zlib

import base64
import binascii
import json

from . import config, filters, llm, matrix, store, strategies

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
    level = min(config.GRADE_LEVEL[grade], config.MAX_LEVEL)
    easy = 1 if params.get("easy_mode") else 0
    sid = store.execute(store.state(),
                        "INSERT INTO students (alias, grade, level, easy_mode) VALUES (?, ?, ?, ?)",
                        (alias, grade, level, easy))
    return {"student": sid, "alias": alias, "grade": grade, "level": level,
            "easy_mode": bool(easy), "matrix": _set_matrix(matrix.level(level))}


def _topic_scores(sid):
    rows = store.query(store.state(), """
        SELECT topic, COUNT(*) AS n, SUM(correct) AS ok FROM attempts
        WHERE student_id = ? AND first_try = 1 GROUP BY topic""", (sid,))
    return {r["topic"]: ((r["ok"] or 0) + 1) / (r["n"] + 2) for r in rows}, {r["topic"]: r["n"] for r in rows}


def _pick(sid, level):
    seen = {r["problem_id"] for r in store.query(
        store.state(), "SELECT DISTINCT problem_id FROM attempts WHERE student_id = ?", (sid,))}
    rows = store.query(store.bank(), """
        SELECT c.id, c.topic FROM content c JOIN problems p ON p.id = c.id AND p.lang = 'cat'
        WHERE c.verified = 1 AND p.level = ? ORDER BY c.id""", (level,))
    pool = [r for r in rows if r["id"] not in seen]
    if not pool:
        return None
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
    else:
        pid = _pick(student["id"], student["level"])
        # Si el nivell s'ha esgotat, mira els nivells del costat
        for delta in (-1, 1, -2, 2, -3, 3):
            if pid:
                break
            level = student["level"] + delta
            if 0 <= level <= config.MAX_LEVEL:
                pid = _pick(student["id"], level)
    if not pid:
        return {"problem": None, "message": "Has fet tots els problemes! Parla amb el teu mestre."}
    return {"problem": _public(pid), "level": student["level"],
            "matrix": _set_matrix(matrix.level(student["level"], student["streak_ok"]))}


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
    level, ok, bad, change = student["level"], student["streak_ok"], student["streak_bad"], 0
    if first_try:
        if correct:
            bad = 0
            if hints_used == 0:
                ok += 1
                if ok >= 2 and level < config.MAX_LEVEL:
                    level, ok, change = level + 1, 0, 1
        else:
            ok, bad = 0, bad + 1
            if bad >= 2 and level > 0:
                level, bad, change = level - 1, 0, -1
    store.execute(db, "UPDATE students SET level = ?, streak_ok = ?, streak_bad = ? WHERE id = ?",
                  (level, ok, bad, student["id"]))
    try:
        seconds = float(params.get("seconds") or 0)
    except (TypeError, ValueError):
        seconds = 0.0
    store.execute(db, """INSERT INTO attempts (student_id, problem_id, letter, correct, first_try,
                         hints_used, seconds, level, topic) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (student["id"], pid, letter, int(correct), int(first_try), hints_used, seconds,
                   row["level"], content["topic"]))
    result = {"correct": correct, "first_try": first_try, "level": level, "level_change": change,
              "streak": ok, "matrix": _set_matrix(matrix.check() if correct else matrix.cross())}
    if correct:
        result.update({"answer": label, "answer_text": option,
                       "solution": content["solution"], "key_idea": content["key_idea"]})
    return result


def _germa(pid, content, student_id):
    """El problema germà: mateix tema, més fàcil (o igual de nivell), el més semblant."""
    row = _problem_row(pid)
    solved = {r["problem_id"] for r in store.query(
        store.state(), "SELECT problem_id FROM attempts WHERE student_id = ? AND correct = 1", (student_id,))}
    candidates = store.query(store.bank(), """
        SELECT n.neighbor_id AS id, n.score, p.level, c.topic FROM neighbors n
        JOIN content c ON c.id = n.neighbor_id AND c.verified = 1
        JOIN problems p ON p.id = n.neighbor_id AND p.lang = 'cat'
        WHERE n.id = ? ORDER BY n.rank""", (pid,))
    best = None
    for c in candidates:
        if c["id"] in solved or c["level"] > row["level"]:
            continue
        key = (c["topic"] == content["topic"], c["level"] < row["level"], c["score"])
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
                if sibling else content["key_idea"]}
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
    before = _current_matrix
    _set_matrix(matrix.thinking())
    try:
        text, timings = llm.socratic(row["text"], content["solution"], chosen, trap, said)
        rejected = filters.leaks(text, label, option, row["text"]) or (
            "" if filters.is_question(text) else "no és una pregunta curta")
        if not rejected:
            reply = text
    except OSError as error:
        rejected = f"la IA de la placa no respon ({type(error).__name__})"
    if reply is None:
        # Reserva: l'error típic d'aquesta opció (preparat i verificat), o la dada clau
        source = "preparat"
        if trap and not filters.leaks(trap, label, option, row["text"]):
            reply = f"Un error típic de qui tria la {letter}: {trap.rstrip('.')}. Pot ser el teu cas?"
        else:
            reply = (content["hints"][1] if len(content["hints"]) > 1 and content["hints"][1]
                     else content["key_idea"])
    _set_matrix(before)
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
    threading.Thread(target=llm.warm, args=(row["text"], content["solution"]), daemon=True).start()
    return {"started": True}


def profile(params):
    student = _student(params)
    sid = student["id"]
    rows = store.query(store.state(), """
        SELECT topic, COUNT(*) AS n, SUM(correct) AS ok, AVG(hints_used) AS hints FROM attempts
        WHERE student_id = ? AND first_try = 1 GROUP BY topic ORDER BY topic""", (sid,))
    total = sum(r["n"] for r in rows)
    ok = sum(r["ok"] or 0 for r in rows)
    recent = store.query(store.state(), """SELECT problem_id, letter, correct, hints_used, topic, level, ts
        FROM attempts WHERE student_id = ? AND first_try = 1 ORDER BY id DESC LIMIT 10""", (sid,))
    return {
        "alias": student["alias"], "grade": student["grade"], "level": student["level"],
        "streak": student["streak_ok"], "attempts": total, "correct": ok,
        "accuracy": round(ok / total, 3) if total else None,
        "by_topic": [{"topic": r["topic"], "attempts": r["n"], "correct": r["ok"] or 0,
                      "accuracy": round((r["ok"] or 0) / r["n"], 3), "avg_hints": round(r["hints"] or 0, 2)}
                     for r in rows],
        "recent": recent,
    }


def teacher(_params):
    db = store.state()
    cells = store.query(db, """
        SELECT topic, level, COUNT(*) AS n, SUM(correct) AS ok, AVG(hints_used) AS hints
        FROM attempts WHERE first_try = 1 GROUP BY topic, level ORDER BY topic, level""")
    wrong = store.query(db, """
        SELECT problem_id, letter, COUNT(*) AS n FROM attempts
        WHERE first_try = 1 AND correct = 0 GROUP BY problem_id, letter ORDER BY n DESC LIMIT 8""")
    traps = []
    for w in wrong:
        content = _content(w["problem_id"])
        row = _problem_row(w["problem_id"])
        if not content or not row:
            continue
        tried = store.one(db, "SELECT COUNT(*) AS n FROM attempts WHERE first_try = 1 AND problem_id = ?",
                          (w["problem_id"],))["n"]
        traps.append({"problem_id": w["problem_id"], "letter": w["letter"], "count": w["n"],
                      "share": round(w["n"] / tried, 3) if tried else None,
                      "trap": content["traps"].get(w["letter"], ""), "topic": content["topic"],
                      "level": row["level"], "image_url": f"/api/image?id={w['problem_id']}&lang=cat"})
    students = store.one(db, "SELECT COUNT(*) AS n FROM students")["n"]
    attempts = store.one(db, "SELECT COUNT(*) AS n FROM attempts WHERE first_try = 1")["n"]
    return {
        "students": students, "attempts": attempts,
        "cells": [{"topic": c["topic"], "level": c["level"], "attempts": c["n"], "correct": c["ok"] or 0,
                   "accuracy": round((c["ok"] or 0) / c["n"], 3), "avg_hints": round(c["hints"] or 0, 2)}
                  for c in cells],
        "traps": traps,
        "topics": config.TOPICS,
        "levels": list(range(config.MAX_LEVEL + 1)),
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
    meta = {r["key"]: r["value"] for r in store.query(store.bank(), "SELECT key, value FROM meta")}
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
            "fallback": len(explained) - len(live),
            "median_seconds": live[len(live) // 2] if live else None,
            "worst_seconds": live[-1] if live else None,
        },
        "internet": "no cal: tot passa en aquesta placa",
    }


# ------------------------------------------------------- «Porta el teu problema»
#
# L'alumne puja la foto d'un problema seu (deures, llibre, examen):
#   1. own_ocr    la placa llegeix el text de la imatge (servei OCR, port 8084)
#   2. own_match  es busquen problemes semblants del banc i es desa el problema
#   3. own_help   l'alumne diu on s'encalla i la IA de la placa, amb el problema
#                 semblant ja resolt com a exemple, li dona una pista per continuar
# El mentor no sap la resposta del problema de l'alumne: mai n'afirma cap.

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_OWN_WORDS = 45


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
    from . import ocr  # import tardà: el servei OCR és opcional
    before = _current_matrix
    _set_matrix(matrix.thinking())
    try:
        result = ocr.read_image(image, params.get("lang") or "cat")
        ok = True
    except OSError as error:
        ok = False
        failure = str(error) or type(error).__name__
    finally:
        _set_matrix(before)
    if not ok:
        store.execute(store.state(), "INSERT INTO ocr_reads (student_id, engine, seconds, chars, ok) VALUES (?, ?, ?, ?, 0)",
                      (student["id"], "", 0, 0))
        raise UserError(503, f"El lector d'imatges no està disponible ({failure}). Pots escriure el problema a mà.")
    text = (result.get("text") or "").strip()
    store.execute(store.state(), "INSERT INTO ocr_reads (student_id, engine, seconds, chars, ok) VALUES (?, ?, ?, ?, 1)",
                  (student["id"], result.get("engine", ""), result.get("seconds", 0), len(text)))
    return {"text": text, "engine": result.get("engine"), "seconds": result.get("seconds"),
            "empty": not text}


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
    # Primer, problemes del nivell de l'alumne o més fàcils; si no n'hi ha de prou semblants, tots
    hits = retrieval.find_similar(text, k=3, max_level=student["level"])
    low = getattr(retrieval, "LOW_SCORE", 0.0)
    if not hits or hits[0]["score"] < low:
        wider = retrieval.find_similar(text, k=3)
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
    # La IA llegeix ara el problema i l'exemple, mentre l'alumne escriu el seu dubte
    example = _example(siblings[0]["id"]) if found and siblings else None
    threading.Thread(target=llm.warm_own, args=(text, example), daemon=True).start()
    return {"own_id": own_id, "topic": topic, "topic_confidence": round(float(confidence), 2),
            "found": found, "siblings": siblings if found else [],
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
    example = _example(sibling_ids[0]) if own["found"] and sibling_ids else None
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
