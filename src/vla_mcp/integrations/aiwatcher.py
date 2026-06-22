"""Push VLA pipeline and training events to aiwatcher-mcp fleet ingest."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..config import VLAConfig, get_config

log = logging.getLogger(__name__)


async def push_fleet_event(
    *,
    title: str,
    summary: str,
    source: str = "vla-mcp",
    url: str | None = None,
    urgency_hint: float = 7.5,
    config: VLAConfig | None = None,
) -> bool:
    """POST to aiwatcher ``/api/fleet/ingest`` when configured."""
    cfg = config or get_config()
    if not cfg.aiwatcher_push_enabled:
        return False
    base = (cfg.aiwatcher_base_url or "").strip().rstrip("/")
    if not base:
        return False
    headers = {"Content-Type": "application/json"}
    if cfg.aiwatcher_api_key:
        headers["X-AIWatcher-Key"] = cfg.aiwatcher_api_key
    payload: dict[str, Any] = {
        "title": title,
        "summary": summary,
        "source": source,
        "urgency_hint": float(urgency_hint),
    }
    if url:
        payload["url"] = url
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{base}/api/fleet/ingest", json=payload, headers=headers)
        if resp.status_code >= 400:
            log.warning("aiwatcher ingest failed HTTP %s: %s", resp.status_code, resp.text[:200])
            return False
        return True
    except httpx.HTTPError as exc:
        log.warning("aiwatcher ingest unreachable: %s", exc)
        return False


async def push_pipeline_complete(run: dict[str, Any], *, config: VLAConfig | None = None) -> bool:
    """Notify aiwatcher when an end-to-end VLA pipeline run finishes."""
    if not run.get("success"):
        return False
    mode = run.get("mode", "unknown")
    run_id = run.get("run_id", "?")
    episode = run.get("episode_id") or "n/a"
    shard = run.get("shard_name") or "n/a"
    summary = (
        f"VLA pipeline ({mode}) run {run_id}: episode={episode}, shard={shard}, "
        f"arrays={run.get('arrays_written', 0)}, boomy={run.get('boomy_demo') or 'none'}. "
        f"{run.get('message') or ''}"
    ).strip()
    return await push_fleet_event(
        title=f"[vla-pipeline] {mode} loop completed ({run_id})",
        summary=summary,
        source="vla-mcp-pipeline",
        urgency_hint=7.0 if mode == "simulated" else 8.0,
        config=config,
    )
