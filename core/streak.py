"""Streak engine — persistent streak data via SQLite cache."""
from __future__ import annotations

import logging
import sqlite3
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)
DB_PATH = Path("lifeos_cache.db")


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS streaks (
                task        TEXT PRIMARY KEY,
                current     INTEGER DEFAULT 0,
                longest     INTEGER DEFAULT 0,
                last_date   TEXT
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS snooze (
                chat_id     INTEGER,
                task        TEXT,
                fire_at     TEXT,
                PRIMARY KEY (chat_id, task)
            )
        """)
        con.commit()


def update_streak(task: str, done: bool, for_date: date) -> int:
    """Update and return current streak count for task."""
    with _conn() as con:
        row = con.execute("SELECT * FROM streaks WHERE task=?", (task,)).fetchone()
        today_str = for_date.isoformat()
        if row is None:
            current = 1 if done else 0
            longest = current
            con.execute(
                "INSERT INTO streaks VALUES (?,?,?,?)",
                (task, current, longest, today_str if done else None),
            )
        else:
            current = row["current"]
            longest = row["longest"]
            last = row["last_date"]

            if done:
                if last is None:
                    current = 1
                else:
                    from datetime import timedelta
                    last_date = date.fromisoformat(last)
                    diff = (for_date - last_date).days
                    if diff == 1:
                        current += 1
                    elif diff == 0:
                        pass  # already counted today
                    else:
                        current = 1
                longest = max(longest, current)
                con.execute(
                    "UPDATE streaks SET current=?, longest=?, last_date=? WHERE task=?",
                    (current, longest, today_str, task),
                )
            else:
                # missed today — streak resets
                current = 0
                con.execute(
                    "UPDATE streaks SET current=0 WHERE task=?", (task,)
                )
        con.commit()
    return current


def get_all_streaks() -> dict[str, dict[str, int]]:
    """Return {task: {current, longest}} for all tracked tasks."""
    with _conn() as con:
        rows = con.execute("SELECT task, current, longest FROM streaks").fetchall()
    return {r["task"]: {"current": r["current"], "longest": r["longest"]} for r in rows}


def save_snooze(chat_id: int, task: str, fire_at: str) -> None:
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO snooze VALUES (?,?,?)",
            (chat_id, task, fire_at),
        )
        con.commit()


def pop_due_snoozes(now_str: str) -> list[dict]:
    """Return and delete snoozes due at or before now_str (ISO format)."""
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM snooze WHERE fire_at <= ?", (now_str,)
        ).fetchall()
        for r in rows:
            con.execute(
                "DELETE FROM snooze WHERE chat_id=? AND task=?",
                (r["chat_id"], r["task"]),
            )
        con.commit()
    return [dict(r) for r in rows]
