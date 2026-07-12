"""SQLite persistence: field memory / answer bank, application log, idempotency.

Everything the agent "learns" lives here so it improves over time at zero token cost.
Deliberately dependency-free (stdlib sqlite3) and safe to import from anywhere.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
from collections import deque
from typing import Any, Optional

from .config import DB_PATH

_lock = threading.Lock()

# Enhanced loop detection: track state transitions to detect cycles
_state_history: dict[str, deque] = {}  # session_id -> deque of last N state hashes
MAX_HISTORY_LENGTH = 10


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


_conn = _connect()


def init_db() -> None:
    with _lock:
        _conn.executescript(
            """
            -- The Answer Bank: normalized question -> the answer we gave.
            CREATE TABLE IF NOT EXISTS field_memory (
                q_norm     TEXT PRIMARY KEY,   -- normalized question/label
                q_raw      TEXT NOT NULL,       -- original text (last seen)
                answer     TEXT NOT NULL,
                source     TEXT NOT NULL,       -- 'user' | 'profile' | 'llm'
                confidence REAL DEFAULT 1.0,
                uses       INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT (datetime('now'))
            );

            -- One row per application attempt; also the dedupe + idempotency source.
            CREATE TABLE IF NOT EXISTS applications (
                session_id TEXT PRIMARY KEY,
                url        TEXT,
                company    TEXT,
                title      TEXT,
                status     TEXT DEFAULT 'in_progress', -- in_progress|submitted|uncertain|aborted
                submitted  INTEGER DEFAULT 0,          -- idempotency guard
                answers    TEXT DEFAULT '{}',          -- JSON snapshot of answers given
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            -- Anti-loop: count how many times a (session, stage_hash) recurs.
            CREATE TABLE IF NOT EXISTS stage_counts (
                session_id TEXT,
                stage_hash TEXT,
                count      INTEGER DEFAULT 0,
                PRIMARY KEY (session_id, stage_hash)
            );
            
            -- Enhanced loop detection: track state transitions
            CREATE TABLE IF NOT EXISTS state_transitions (
                session_id TEXT,
                from_hash  TEXT,
                to_hash    TEXT,
                count      INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (session_id, from_hash, to_hash)
            );

            -- Freemium: usage tracking per billing month
            CREATE TABLE IF NOT EXISTS usage (
                month       TEXT PRIMARY KEY,
                count       INTEGER DEFAULT 0,
                limit_val   INTEGER DEFAULT 3,
                tier        TEXT DEFAULT 'free',
                license_key TEXT DEFAULT '',
                activated_at TEXT DEFAULT (datetime('now'))
            );
            """
        )
        _conn.commit()


# --- normalization -------------------------------------------------------------

_STOP = re.compile(r"[^a-z0-9 ]+")


def normalize_question(text: str) -> str:
    """Collapse a label/question to a stable key so paraphrases match."""
    t = text.lower().strip()
    t = _STOP.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    # Drop trailing filler that varies ("(required)", "optional", punctuation).
    for junk in ("required", "optional"):
        t = t.replace(junk, "")
    return re.sub(r"\s+", " ", t).strip()


# --- field memory / answer bank ------------------------------------------------

def remember_answer(q_raw: str, answer: str, source: str, confidence: float = 1.0) -> None:
    q = normalize_question(q_raw)
    if not q:
        return
    with _lock:
        _conn.execute(
            """
            INSERT INTO field_memory (q_norm, q_raw, answer, source, confidence, uses)
            VALUES (?, ?, ?, ?, ?, 0)
            ON CONFLICT(q_norm) DO UPDATE SET
                answer=excluded.answer, q_raw=excluded.q_raw,
                source=excluded.source, confidence=excluded.confidence,
                updated_at=datetime('now')
            """,
            (q, q_raw, answer, source, confidence),
        )
        _conn.commit()


def recall_answer(q_raw: str) -> Optional[dict[str, Any]]:
    q = normalize_question(q_raw)
    if not q:
        return None
    with _lock:
        row = _conn.execute(
            "SELECT * FROM field_memory WHERE q_norm = ?", (q,)
        ).fetchone()
        if row:
            _conn.execute(
                "UPDATE field_memory SET uses = uses + 1 WHERE q_norm = ?", (q,)
            )
            _conn.commit()
            return dict(row)
    return None


# --- applications / idempotency ------------------------------------------------

def get_application(session_id: str) -> Optional[dict[str, Any]]:
    with _lock:
        row = _conn.execute(
            "SELECT * FROM applications WHERE session_id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None


def upsert_application(session_id: str, **fields: Any) -> None:
    existing = get_application(session_id)
    with _lock:
        if existing is None:
            _conn.execute(
                "INSERT INTO applications (session_id) VALUES (?)", (session_id,)
            )
        if fields:
            cols = ", ".join(f"{k} = ?" for k in fields)
            vals = list(fields.values()) + [session_id]
            _conn.execute(
                f"UPDATE applications SET {cols}, updated_at=datetime('now') "
                f"WHERE session_id = ?",
                vals,
            )
        _conn.commit()


def is_already_submitted(session_id: str) -> bool:
    app = get_application(session_id)
    return bool(app and app["submitted"])


def already_applied_to(url: str) -> bool:
    """Cross-session dedupe by job URL (loose match on the path)."""
    key = url.split("?")[0]
    with _lock:
        row = _conn.execute(
            "SELECT 1 FROM applications WHERE submitted = 1 AND url LIKE ? LIMIT 1",
            (f"{key}%",),
        ).fetchone()
        return row is not None


# --- anti-loop -----------------------------------------------------------------

def detect_cycle_pattern(session_id: str, current_hash: str) -> Optional[str]:
    """
    Detect cyclic patterns in state transitions (e.g., A→B→A→B or A→B→C→A).
    Returns a description of the detected pattern if found, else None.
    """
    if session_id not in _state_history:
        _state_history[session_id] = deque(maxlen=MAX_HISTORY_LENGTH)
    
    history = _state_history[session_id]
    history.append(current_hash)
    
    if len(history) < 4:
        return None  # Need at least 4 states to detect a cycle
    
    # Check for oscillation (A→B→A→B)
    recent = list(history)[-4:]
    if recent[0] == recent[2] and recent[1] == recent[3] and recent[0] != recent[1]:
        return f"oscillation: {recent[0][:8]}↔{recent[1][:8]}"
    
    # Check for 3-state cycle (A→B→C→A)
    if len(history) >= 6:
        recent_6 = list(history)[-6:]
        if (recent_6[0] == recent_6[3] and 
            recent_6[1] == recent_6[4] and 
            recent_6[2] == recent_6[5]):
            return f"3-cycle: {recent_6[0][:8]}→{recent_6[1][:8]}→{recent_6[2][:8]}"
    
    return None


def record_state_transition(session_id: str, from_hash: str, to_hash: str) -> None:
    """Track state transitions for advanced loop detection."""
    if not from_hash or not to_hash or from_hash == to_hash:
        return
    
    with _lock:
        _conn.execute(
            """
            INSERT INTO state_transitions (session_id, from_hash, to_hash, count)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(session_id, from_hash, to_hash) 
            DO UPDATE SET count = count + 1, created_at = datetime('now')
            """,
            (session_id, from_hash, to_hash),
        )
        _conn.commit()


def bump_stage(session_id: str, stage_hash: str) -> int:
    if not stage_hash:
        return 0
    with _lock:
        _conn.execute(
            """
            INSERT INTO stage_counts (session_id, stage_hash, count)
            VALUES (?, ?, 1)
            ON CONFLICT(session_id, stage_hash) DO UPDATE SET count = count + 1
            """,
            (session_id, stage_hash),
        )
        _conn.commit()
        row = _conn.execute(
            "SELECT count FROM stage_counts WHERE session_id = ? AND stage_hash = ?",
            (session_id, stage_hash),
        ).fetchone()
        return row["count"] if row else 0


def reset_stage(session_id: str, stage_hash: str) -> None:
    with _lock:
        _conn.execute(
            "DELETE FROM stage_counts WHERE session_id = ? AND stage_hash = ?",
            (session_id, stage_hash),
        )
        _conn.commit()


# --- freemium usage tracking ---------------------------------------------------

def get_usage() -> dict[str, Any]:
    """Get current month's usage and quota info."""
    from datetime import datetime
    month = datetime.now().strftime('%Y-%m')
    with _lock:
        row = _conn.execute(
            "SELECT * FROM usage WHERE month = ?", (month,)
        ).fetchone()
        if not row:
            _conn.execute(
                "INSERT INTO usage (month, count, limit_val, tier) "
                "VALUES (?, 0, 3, 'free')",
                (month,),
            )
            _conn.commit()
            row = _conn.execute(
                "SELECT * FROM usage WHERE month = ?", (month,)
            ).fetchone()
        return dict(row)


def increment_usage() -> dict[str, Any]:
    """Increment this month's usage count. Returns updated usage."""
    from datetime import datetime
    month = datetime.now().strftime('%Y-%m')
    get_usage()  # ensure row exists
    with _lock:
        _conn.execute(
            "UPDATE usage SET count = count + 1 WHERE month = ?", (month,)
        )
        _conn.commit()
    return get_usage()


def has_quota() -> bool:
    """Check if the user has remaining applications this month."""
    u = get_usage()
    return u['count'] < u['limit_val']


def activate_license(key: str, tier: str = 'pro', limit: int = 50) -> dict[str, Any]:
    """Activate a license key and upgrade the current month's tier."""
    from datetime import datetime
    month = datetime.now().strftime('%Y-%m')
    get_usage()  # ensure row exists
    with _lock:
        _conn.execute(
            "UPDATE usage SET tier = ?, limit_val = ?, license_key = ?, "
            "activated_at = datetime('now') WHERE month = ?",
            (tier, limit, key, month),
        )
        _conn.commit()
    return get_usage()


init_db()
