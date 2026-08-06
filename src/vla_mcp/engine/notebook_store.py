"""SQLite-backed notebooks: personal diary, dev diary, news diary."""

from __future__ import annotations

import sqlite3
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..config import VLAConfig, get_config

NOTEBOOKS = ("personal", "dev", "news")
CATEGORIES = ("repo_fix", "tool_install", "blooper", "decision", "note", "digest")
MAX_ENTRIES_PER_NOTEBOOK = 500

_SCHEMA = """
CREATE TABLE IF NOT EXISTS notebook_entries (
  id         TEXT PRIMARY KEY,
  notebook   TEXT NOT NULL CHECK (notebook IN ('personal','dev','news')),
  category   TEXT NOT NULL DEFAULT 'note',
  title      TEXT NOT NULL,
  body       TEXT NOT NULL,
  author     TEXT NOT NULL DEFAULT 'sandra',
  tags       TEXT NOT NULL DEFAULT '[]',
  metrics    TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_nb_created ON notebook_entries(notebook, created_at DESC);
"""

_lock = threading.Lock()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _row_to_entry(row: sqlite3.Row) -> dict[str, Any]:
    import json

    entry = dict(row)
    try:
        entry["tags"] = json.loads(entry.get("tags") or "[]")
    except Exception:
        entry["tags"] = []
    try:
        entry["metrics"] = json.loads(entry.get("metrics") or "{}")
    except Exception:
        entry["metrics"] = {}
    return entry


class NotebookStore:
    """One notebook_entries table, WAL mode, connection per operation."""

    def __init__(self, config: VLAConfig | None = None) -> None:
        self.config = config or get_config()

    @classmethod
    def default(cls) -> NotebookStore:
        return cls()

    @property
    def db_path(self) -> Path:
        root = Path(self.config.dataset_root).expanduser().resolve()
        notebooks_dir = root / "notebooks"
        notebooks_dir.mkdir(parents=True, exist_ok=True)
        return notebooks_dir / "notebooks.sqlite3"

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=15000")
        conn.executescript(_SCHEMA)
        try:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(notebook_entries)")}
            if "metrics" not in cols:
                conn.execute("ALTER TABLE notebook_entries ADD COLUMN metrics TEXT NOT NULL DEFAULT '{}'")
                conn.commit()
        except sqlite3.Error:
            pass
        return conn

    def add_entry(
        self,
        notebook: str,
        *,
        title: str,
        body: str,
        category: str = "note",
        author: str = "sandra",
        tags: list[str] | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if notebook not in NOTEBOOKS:
            return {"success": False, "error": f"notebook must be one of {NOTEBOOKS}", "error_type": "validation"}
        title = (title or "").strip()
        body = (body or "").strip()
        if not title or len(title) > 200:
            return {"success": False, "error": "title required, max 200 chars", "error_type": "validation"}
        if not body or len(body) > 20000:
            return {"success": False, "error": "body required, max 20000 chars", "error_type": "validation"}
        if category not in CATEGORIES:
            category = "note"
        entry_id = f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"
        now = _now()
        tags_json = __import__("json").dumps(list(tags or []))
        metrics_json = __import__("json").dumps(metrics or {})
        with _lock:
            conn = self._connect()
            try:
                conn.execute(
                    "INSERT INTO notebook_entries"
                    " (id, notebook, category, title, body, author, tags, metrics, created_at)"
                    " VALUES (?,?,?,?,?,?,?,?,?)",
                    (entry_id, notebook, category, title, body, author, tags_json, metrics_json, now),
                )
                conn.execute(
                    "DELETE FROM notebook_entries WHERE notebook=? AND id NOT IN ("
                    " SELECT id FROM notebook_entries WHERE notebook=? ORDER BY created_at DESC, rowid DESC LIMIT ?"
                    ")",
                    (notebook, notebook, MAX_ENTRIES_PER_NOTEBOOK),
                )
                conn.commit()
            finally:
                conn.close()
        entry = self.get_entry(notebook, entry_id)
        return {"success": True, "entry": entry, "message": f"Logged to {notebook} diary."}

    def list_entries(
        self,
        notebook: str,
        *,
        limit: int = 50,
        offset: int = 0,
        category: str | None = None,
    ) -> dict[str, Any]:
        if notebook not in NOTEBOOKS:
            return {"success": False, "error": f"notebook must be one of {NOTEBOOKS}", "error_type": "validation"}
        limit = max(1, min(int(limit), 200))
        offset = max(0, int(offset))
        with _lock:
            conn = self._connect()
            try:
                if category:
                    total = conn.execute(
                        "SELECT COUNT(*) FROM notebook_entries WHERE notebook=? AND category=?",
                        (notebook, category),
                    ).fetchone()[0]
                    rows = conn.execute(
                        "SELECT * FROM notebook_entries WHERE notebook=? AND category=?"
                        " ORDER BY created_at DESC, rowid DESC LIMIT ? OFFSET ?",
                        (notebook, category, limit, offset),
                    ).fetchall()
                else:
                    total = conn.execute(
                        "SELECT COUNT(*) FROM notebook_entries WHERE notebook=?", (notebook,)
                    ).fetchone()[0]
                    rows = conn.execute(
                        "SELECT * FROM notebook_entries WHERE notebook=?"
                        " ORDER BY created_at DESC, rowid DESC LIMIT ? OFFSET ?",
                        (notebook, limit, offset),
                    ).fetchall()
            finally:
                conn.close()
        entries = [_row_to_entry(r) for r in rows]
        return {
            "success": True,
            "notebook": notebook,
            "entries": entries,
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": offset + len(entries) < total,
        }

    def get_entry(self, notebook: str, entry_id: str) -> dict[str, Any] | None:
        with _lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT * FROM notebook_entries WHERE notebook=? AND id=?", (notebook, entry_id)
                ).fetchone()
            finally:
                conn.close()
        return _row_to_entry(row) if row else None

    def delete_entry(self, notebook: str, entry_id: str) -> bool:
        with _lock:
            conn = self._connect()
            try:
                cur = conn.execute("DELETE FROM notebook_entries WHERE notebook=? AND id=?", (notebook, entry_id))
                conn.commit()
                return cur.rowcount > 0
            finally:
                conn.close()

    def latest(self, notebook: str) -> dict[str, Any] | None:
        with _lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT * FROM notebook_entries WHERE notebook=? ORDER BY created_at DESC, rowid DESC LIMIT 1",
                    (notebook,),
                ).fetchone()
            finally:
                conn.close()
        return _row_to_entry(row) if row else None

    def counts(self) -> dict[str, int]:
        with _lock:
            conn = self._connect()
            try:
                rows = conn.execute("SELECT notebook, COUNT(*) AS n FROM notebook_entries GROUP BY notebook").fetchall()
            finally:
                conn.close()
        counts = {n: 0 for n in NOTEBOOKS}
        for row in rows:
            counts[row["notebook"]] = row["n"]
        return counts

    def summaries(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        counts = self.counts()
        for name in NOTEBOOKS:
            latest = self.latest(name)
            out[name] = {"name": name, "count": counts[name], "latest": latest}
        return out
