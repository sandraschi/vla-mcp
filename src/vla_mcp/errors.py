"""Shared error + envelope helpers (TOOL_DESIGN_STANDARDS.md section 7.1, Pattern 3)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _error_response(
    message: str,
    *,
    error_type: str = "error",
    exc: BaseException | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a dialogic error dict and log it (traceback via logger.exception)."""
    if exc is not None:
        logger.exception("vla_error: %s", message)
    else:
        logger.warning("vla_error: %s", message)
    out: dict[str, Any] = {"success": False, "error": message, "error_type": error_type, "message": message}
    if extra:
        out.update(extra)
    return out


def _wrap(result: Any, message: str) -> dict[str, Any]:
    """Normalize an engine result into the dialogic envelope (never mutates input)."""
    if isinstance(result, dict):
        out = dict(result)
        out.setdefault("success", True)
        out.setdefault("message", message)
        return out
    return {"success": True, "result": result, "message": message}
