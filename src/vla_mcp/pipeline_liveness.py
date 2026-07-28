"""Robotics stack liveness for supervisors (meta-mcp, fleet-agent, aiwatcher)."""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from .config import VLAConfig, get_config
from .engine.fleet_bridge import FleetBridge

log = logging.getLogger(__name__)


def _latest_pipeline_age_hours(dataset_root: str) -> tuple[float | None, str | None]:
    folder = Path(dataset_root).expanduser().resolve() / "logs" / "pipeline"
    if not folder.is_dir():
        return None, None
    files = sorted(folder.glob("run_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return None, None
    latest = files[0]
    age_h = round((time.time() - latest.stat().st_mtime) / 3600, 1)
    run_id: str | None = None
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
        run_id = data.get("run_id")
    except (OSError, json.JSONDecodeError):
        pass
    return age_h, run_id or latest.name


async def check_pipeline_liveness(
    *,
    stale_hours: int = 168,
    config: VLAConfig | None = None,
) -> dict[str, Any]:
    """Surface stale VLA loops and unreachable robotics fleet peers."""
    cfg = config or get_config()
    stale_hours = max(1, int(stale_hours))
    stale_seconds = stale_hours * 3600
    alerts: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    age_h, run_id = _latest_pipeline_age_hours(cfg.dataset_root)
    if age_h is None:
        alerts.append(
            {
                "severity": "warning",
                "code": "VLA_PIPELINE_NEVER_RUN",
                "message": (
                    "No VLA pipeline provenance on disk — run vla_pipeline(operation='run') "
                    "or use the webapp Pipeline tab"
                ),
                "detail": {"dataset_root": cfg.dataset_root},
            }
        )
        checks.append({"name": "vla_last_pipeline", "ok": False, "age_hours": None})
    else:
        ok = (age_h * 3600) <= stale_seconds
        checks.append(
            {
                "name": "vla_last_pipeline",
                "ok": ok,
                "age_hours": age_h,
                "run_id": run_id,
            }
        )
        if not ok:
            alerts.append(
                {
                    "severity": "warning",
                    "code": "VLA_PIPELINE_STALE",
                    "message": (f"Last VLA pipeline run is {age_h}h old (threshold {stale_hours}h)"),
                    "detail": {"run_id": run_id, "age_hours": age_h},
                }
            )

    bridge = FleetBridge(config=cfg)
    peer_status = await bridge.bridge_status()
    for peer in peer_status.get("peers") or []:
        name = peer.get("name", "?")
        reachable = bool(peer.get("reachable"))
        checks.append(
            {
                "name": f"peer_{name}",
                "ok": reachable,
                "url": peer.get("url"),
                "probe_path": peer.get("probe_path"),
            }
        )
        if not reachable and peer.get("url"):
            alerts.append(
                {
                    "severity": "warning",
                    "code": "VLA_PEER_UNREACHABLE",
                    "message": f"Robotics peer {name} unreachable at {peer.get('url')}",
                    "detail": {"peer": name, "error": peer.get("error")},
                }
            )

    base = (cfg.aiwatcher_base_url or "").strip()
    if base:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{base.rstrip('/')}/api/health")
            ok = resp.status_code == 200
            checks.append(
                {
                    "name": "aiwatcher_health",
                    "ok": ok,
                    "url": base,
                    "status_code": resp.status_code,
                }
            )
            if not ok:
                alerts.append(
                    {
                        "severity": "warning",
                        "code": "AIWATCHER_UNHEALTHY",
                        "message": f"aiwatcher health check failed ({resp.status_code})",
                        "detail": {"url": base},
                    }
                )
        except httpx.HTTPError as exc:
            checks.append({"name": "aiwatcher_health", "ok": False, "url": base})
            alerts.append(
                {
                    "severity": "warning",
                    "code": "AIWATCHER_UNREACHABLE",
                    "message": f"Cannot reach aiwatcher at {base}: {exc}",
                    "detail": {"url": base},
                }
            )

    critical = [a for a in alerts if a.get("severity") == "critical"]
    healthy = len(critical) == 0
    if alerts:
        for a in alerts:
            if a.get("severity") in ("critical", "warning"):
                log.warning("VLA pipeline liveness [%s]: %s", a.get("code"), a.get("message"))

    return {
        "success": True,
        "healthy": healthy,
        "critical_count": len(critical),
        "warning_count": len([a for a in alerts if a.get("severity") == "warning"]),
        "checked_at": datetime.now(UTC).isoformat(),
        "service": "vla-mcp",
        "stale_hours": stale_hours,
        "api_port": cfg.api_port,
        "frontend_port": cfg.frontend_port,
        "aiwatcher_base_url": base or None,
        "checks": checks,
        "alerts": alerts,
    }
