"""In-memory log ring buffer for the dashboard Logger modal."""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any

_CAPACITY = 500
_buffer: deque[dict[str, Any]] = deque(maxlen=_CAPACITY)
_attached = False


class _RingBufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # A logging Handler must never raise (stdlib contract) - drop
        # unformattable records instead of breaking the logging call chain.
        try:
            _buffer.append(
                {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created)),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
            )
        except Exception:  # noqa: S110 - see contract note above
            pass


def ensure_attached() -> None:
    """Attach the ring buffer to the root logger (idempotent, store-only)."""
    global _attached
    if _attached:
        return
    root = logging.getLogger()
    if not any(isinstance(h, _RingBufferHandler) for h in root.handlers):
        root.addHandler(_RingBufferHandler(level=logging.DEBUG))
    _attached = True


def query(level: str = "", q: str = "", limit: int = 200) -> list[dict[str, Any]]:
    """Newest-first slice of buffered records, filtered by level substring + text."""
    rows = list(reversed(_buffer))
    if level:
        rows = [r for r in rows if r["level"] == level.upper()]
    if q:
        needle = q.lower()
        rows = [r for r in rows if needle in str(r["message"]).lower() or needle in r["logger"].lower()]
    return rows[: max(1, min(limit, _CAPACITY))]
