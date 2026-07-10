"""
Telemetry and monitoring for Career OS robustness metrics.

Tracks:
- Completion rates
- Error recovery statistics
- Loop incidents
- LLM efficiency (memory hits vs LLM calls)
- Handoff frequency
"""
from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from .config import DB_PATH

_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@dataclass
class TelemetryEvent:
    """Single telemetry event."""
    session_id: str
    event_type: str  # completion, error, loop, llm_call, memory_hit, handoff
    timestamp: str
    details: dict
    
    def to_dict(self):
        return asdict(self)


class TelemetryTracker:
    """Centralized telemetry tracking."""
    
    def __init__(self):
        self._init_tables()
    
    def _init_tables(self):
        """Initialize telemetry tables."""
        with _lock:
            conn = _get_conn()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_session_events 
                ON telemetry_events(session_id, event_type);
                
                CREATE TABLE IF NOT EXISTS session_metrics (
                    session_id TEXT PRIMARY KEY,
                    total_steps INTEGER DEFAULT 0,
                    memory_hits INTEGER DEFAULT 0,
                    llm_calls INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    loops INTEGER DEFAULT 0,
                    handoffs INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT 0,
                    completion_time_seconds REAL DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );
            """)
            conn.commit()
            conn.close()
    
    def track_event(self, event: TelemetryEvent):
        """Record a telemetry event."""
        with _lock:
            conn = _get_conn()
            conn.execute(
                """
                INSERT INTO telemetry_events 
                (session_id, event_type, timestamp, details)
                VALUES (?, ?, ?, ?)
                """,
                (event.session_id, event.event_type, event.timestamp, 
                 json.dumps(event.details))
            )
            conn.commit()
            conn.close()
    
    def update_session_metric(self, session_id: str, metric: str, increment: int = 1):
        """Update a session-level metric."""
        with _lock:
            conn = _get_conn()
            conn.execute(
                f"""
                INSERT INTO session_metrics (session_id, {metric})
                VALUES (?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    {metric} = {metric} + excluded.{metric},
                    updated_at = datetime('now')
                """,
                (session_id, increment)
            )
            conn.commit()
            conn.close()
    
    def mark_completed(self, session_id: str, duration_seconds: float):
        """Mark a session as completed."""
        with _lock:
            conn = _get_conn()
            conn.execute(
                """
                UPDATE session_metrics
                SET completed = 1,
                    completion_time_seconds = ?,
                    updated_at = datetime('now')
                WHERE session_id = ?
                """,
                (duration_seconds, session_id)
            )
            conn.commit()
            conn.close()
    
    def get_session_metrics(self, session_id: str) -> Optional[dict]:
        """Get metrics for a specific session."""
        with _lock:
            conn = _get_conn()
            row = conn.execute(
                "SELECT * FROM session_metrics WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            conn.close()
            return dict(row) if row else None
    
    def get_aggregate_stats(self, days: int = 7) -> dict:
        """Get aggregate statistics for the last N days."""
        with _lock:
            conn = _get_conn()
            
            # Completion rate
            completion_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(completed) as completed_sessions,
                    AVG(completion_time_seconds) as avg_completion_time
                FROM session_metrics
                WHERE created_at >= datetime('now', ? || ' days')
            """, (f'-{days}',)).fetchone()
            
            # Error statistics
            error_stats = conn.execute("""
                SELECT 
                    SUM(errors) as total_errors,
                    AVG(errors) as avg_errors_per_session
                FROM session_metrics
                WHERE created_at >= datetime('now', ? || ' days')
            """, (f'-{days}',)).fetchone()
            
            # Loop incidents
            loop_stats = conn.execute("""
                SELECT 
                    SUM(loops) as total_loops,
                    AVG(loops) as avg_loops_per_session
                FROM session_metrics
                WHERE created_at >= datetime('now', ? || ' days')
            """, (f'-{days}',)).fetchone()
            
            # LLM efficiency
            llm_stats = conn.execute("""
                SELECT 
                    SUM(memory_hits) as total_memory_hits,
                    SUM(llm_calls) as total_llm_calls,
                    CAST(SUM(memory_hits) AS FLOAT) / 
                    NULLIF(SUM(memory_hits) + SUM(llm_calls), 0) as memory_hit_rate
                FROM session_metrics
                WHERE created_at >= datetime('now', ? || ' days')
            """, (f'-{days}',)).fetchone()
            
            # Handoff frequency
            handoff_stats = conn.execute("""
                SELECT 
                    AVG(handoffs) as avg_handoffs_per_session
                FROM session_metrics
                WHERE created_at >= datetime('now', ? || ' days')
                    AND completed = 1
            """, (f'-{days}',)).fetchone()
            
            conn.close()
            
            total = completion_stats['total_sessions'] or 0
            completed = completion_stats['completed_sessions'] or 0
            
            return {
                'period_days': days,
                'total_sessions': total,
                'completed_sessions': completed,
                'completion_rate': (completed / total * 100) if total > 0 else 0,
                'avg_completion_time_seconds': completion_stats['avg_completion_time'] or 0,
                'total_errors': error_stats['total_errors'] or 0,
                'avg_errors_per_session': error_stats['avg_errors_per_session'] or 0,
                'total_loops': loop_stats['total_loops'] or 0,
                'avg_loops_per_session': loop_stats['avg_loops_per_session'] or 0,
                'loop_incident_rate': (loop_stats['total_loops'] / total * 100) if total > 0 else 0,
                'total_memory_hits': llm_stats['total_memory_hits'] or 0,
                'total_llm_calls': llm_stats['total_llm_calls'] or 0,
                'memory_hit_rate': (llm_stats['memory_hit_rate'] or 0) * 100,
                'avg_handoffs_per_session': handoff_stats['avg_handoffs_per_session'] or 0,
            }


# Global tracker instance
tracker = TelemetryTracker()


# Convenience functions for common events
def track_completion(session_id: str, duration_seconds: float):
    """Track successful completion."""
    tracker.mark_completed(session_id, duration_seconds)
    tracker.track_event(TelemetryEvent(
        session_id=session_id,
        event_type='completion',
        timestamp=datetime.utcnow().isoformat(),
        details={'duration_seconds': duration_seconds}
    ))


def track_error(session_id: str, error_type: str, error_msg: str):
    """Track an error."""
    tracker.update_session_metric(session_id, 'errors')
    tracker.track_event(TelemetryEvent(
        session_id=session_id,
        event_type='error',
        timestamp=datetime.utcnow().isoformat(),
        details={'error_type': error_type, 'message': error_msg}
    ))


def track_loop(session_id: str, loop_type: str, pattern: str):
    """Track a loop detection incident."""
    tracker.update_session_metric(session_id, 'loops')
    tracker.track_event(TelemetryEvent(
        session_id=session_id,
        event_type='loop',
        timestamp=datetime.utcnow().isoformat(),
        details={'loop_type': loop_type, 'pattern': pattern}
    ))


def track_llm_call(session_id: str, fields_resolved: int, tokens_used: int):
    """Track an LLM API call."""
    tracker.update_session_metric(session_id, 'llm_calls')
    tracker.track_event(TelemetryEvent(
        session_id=session_id,
        event_type='llm_call',
        timestamp=datetime.utcnow().isoformat(),
        details={'fields_resolved': fields_resolved, 'tokens_used': tokens_used}
    ))


def track_memory_hit(session_id: str, field_label: str):
    """Track a memory bank hit (zero-token resolution)."""
    tracker.update_session_metric(session_id, 'memory_hits')
    tracker.track_event(TelemetryEvent(
        session_id=session_id,
        event_type='memory_hit',
        timestamp=datetime.utcnow().isoformat(),
        details={'field': field_label}
    ))


def track_handoff(session_id: str, reason: str):
    """Track a human handoff."""
    tracker.update_session_metric(session_id, 'handoffs')
    tracker.track_event(TelemetryEvent(
        session_id=session_id,
        event_type='handoff',
        timestamp=datetime.utcnow().isoformat(),
        details={'reason': reason}
    ))


def get_stats(days: int = 7) -> dict:
    """Get aggregate statistics."""
    return tracker.get_aggregate_stats(days)
