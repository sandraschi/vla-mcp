"""Persisted DMuon job registry under VLA_DATASET_ROOT/logs."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

_lock = threading.Lock()


def jobs_file(dataset_root: str) -> Path:
    p = Path(dataset_root).expanduser().resolve() / "logs" / "jobs.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_jobs(dataset_root: str) -> dict[str, dict[str, Any]]:
    path = jobs_file(dataset_root)
    if not path.is_file():
        return {}
    with _lock:
        data = json.loads(path.read_text(encoding="utf-8"))
    jobs = data.get("jobs", {})
    if isinstance(jobs, dict):
        return {str(k): v for k, v in jobs.items()}
    return {}


def save_jobs(dataset_root: str, jobs: dict[str, dict[str, Any]]) -> None:
    path = jobs_file(dataset_root)
    payload = json.dumps({"jobs": jobs}, indent=2)
    tmp = path.with_suffix(".json.tmp")
    with _lock:
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, path)


def upsert_job(dataset_root: str, jobs: dict[str, dict[str, Any]], job_id: str, record: dict[str, Any]) -> None:
    jobs[job_id] = record
    save_jobs(dataset_root, jobs)


def read_log_tail(log_path: str, *, offset: int = 0, max_bytes: int = 65536) -> dict[str, Any]:
    path = Path(log_path).expanduser()
    if not path.is_file():
        return {"success": False, "error": f"Log not found: {log_path}"}
    size = path.stat().st_size
    start = max(0, min(offset, size))
    with path.open("rb") as fh:
        fh.seek(start)
        chunk = fh.read(max_bytes)
    text = chunk.decode("utf-8", errors="replace")
    return {
        "success": True,
        "offset": start,
        "next_offset": start + len(chunk),
        "eof": start + len(chunk) >= size,
        "size": size,
        "text": text,
    }
