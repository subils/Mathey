"""Les dues bases de dades SQLite del mentor.

- El **banc** (MENTOR_DB): problemes, contingut preparat i problemes germans.
  Es construeix amb scripts/build_bank.py i a la placa només es llegeix.
- L'**estat** (MENTOR_STATE_DB): alumnes i intents. Es crea sol i no es
  reconstrueix mai, perquè no es perdi el progrés en actualitzar el banc.

Cap de les dues es puja a GitHub: el banc conté problemes de M3Kang.
"""
import json
import sqlite3
import threading

from . import config

BANK_SCHEMA = """
CREATE TABLE IF NOT EXISTS problems (
    id TEXT NOT NULL, lang TEXT NOT NULL, level INTEGER, year INTEGER,
    text_only INTEGER, text TEXT, options TEXT, label TEXT, split TEXT,
    PRIMARY KEY (id, lang));
CREATE TABLE IF NOT EXISTS content (
    id TEXT PRIMARY KEY, lang TEXT, topic TEXT, key_idea TEXT, hints TEXT,
    solution TEXT, traps TEXT, easy_text TEXT, options TEXT,
    agent_answer TEXT, agent_confidence TEXT, verified INTEGER, problems_found TEXT);
CREATE TABLE IF NOT EXISTS neighbors (
    id TEXT, rank INTEGER, neighbor_id TEXT, score REAL, PRIMARY KEY (id, rank));
CREATE TABLE IF NOT EXISTS topics (id TEXT PRIMARY KEY, topic TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""

STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT, alias TEXT NOT NULL, grade TEXT,
    level INTEGER NOT NULL, streak_ok INTEGER DEFAULT 0, streak_bad INTEGER DEFAULT 0,
    easy_mode INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, problem_id TEXT,
    letter TEXT, correct INTEGER, first_try INTEGER, hints_used INTEGER,
    seconds REAL, level INTEGER, topic TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS hints (
    student_id INTEGER, problem_id TEXT, rung INTEGER, ts TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS explanations (
    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, problem_id TEXT,
    letter TEXT, student_text TEXT, reply TEXT, source TEXT, seconds REAL,
    rejected TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS own_problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, text TEXT, topic TEXT,
    topic_confidence REAL, siblings TEXT, best_score REAL, found INTEGER,
    ts TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS own_helps (
    id INTEGER PRIMARY KEY AUTOINCREMENT, own_id INTEGER, doubt TEXT, reply TEXT,
    source TEXT, seconds REAL, rejected TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS problem_elo (
    id TEXT PRIMARY KEY, elo REAL NOT NULL, attempts INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS ocr_reads (
    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, engine TEXT, seconds REAL,
    chars INTEGER, ok INTEGER, ts TEXT DEFAULT CURRENT_TIMESTAMP);
"""

_lock = threading.Lock()


def _connect(path, schema):
    db = sqlite3.connect(path, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.executescript(schema)
    return db


_bank = None
_state = None


def bank():
    global _bank
    if _bank is None:
        _bank = _connect(config.BANK_DB, BANK_SCHEMA)
    return _bank


def _migrate_state(db):
    """Afegeix les columnes noves a una state.db creada amb una versió anterior."""
    have = {row["name"] for row in db.execute("PRAGMA table_info(students)")}
    for column, kind in (("elo", "REAL"), ("elo_attempts", "INTEGER DEFAULT 0")):
        if column not in have:
            db.execute(f"ALTER TABLE students ADD COLUMN {column} {kind}")
    have = {row["name"] for row in db.execute("PRAGMA table_info(attempts)")}
    # elo_score: el resultat de la resposta per a l'Elo (1, 0 o entremig amb ajudes)
    for column in ("elo_before", "elo_after", "problem_elo", "elo_score"):
        if column not in have:
            db.execute(f"ALTER TABLE attempts ADD COLUMN {column} REAL")
    db.commit()


def state():
    global _state
    if _state is None:
        _state = _connect(config.STATE_DB, STATE_SCHEMA)
        _migrate_state(_state)
    return _state


def query(db, sql, args=()):
    with _lock:
        return [dict(row) for row in db.execute(sql, args).fetchall()]


def one(db, sql, args=()):
    rows = query(db, sql, args)
    return rows[0] if rows else None


def execute(db, sql, args=()):
    with _lock:
        cursor = db.execute(sql, args)
        db.commit()
        return cursor.lastrowid


def loads(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except ValueError:
        return default
