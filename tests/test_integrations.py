"""Fleet integration: aiwatcher ingest and pipeline liveness."""

from __future__ import annotations

import asyncio
import json
import time
from unittest.mock import AsyncMock, patch

import pytest

from vla_mcp.engine.fleet_bridge import FleetBridge
from vla_mcp.integrations.aiwatcher import push_fleet_event, push_pipeline_complete
from vla_mcp.pipeline_liveness import check_pipeline_liveness


@pytest.mark.asyncio
async def test_push_fleet_event_disabled(monkeypatch):
    monkeypatch.setenv("VLA_AIWATCHER_PUSH_ENABLED", "0")
    from vla_mcp.config import VLAConfig

    cfg = VLAConfig.from_env()
    ok = await push_fleet_event(title="t", summary="s", config=cfg)
    assert ok is False


@pytest.mark.asyncio
async def test_push_pipeline_complete_mocked(monkeypatch):
    monkeypatch.setenv("VLA_AIWATCHER_BASE_URL", "http://127.0.0.1:10946")
    monkeypatch.setenv("VLA_AIWATCHER_PUSH_ENABLED", "1")
    from vla_mcp.config import VLAConfig

    cfg = VLAConfig.from_env()
    with patch("vla_mcp.integrations.aiwatcher.httpx.AsyncClient") as mock_client:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)
        ok = await push_pipeline_complete(
            {"success": True, "run_id": "r1", "mode": "simulated", "episode_id": "e1"},
            config=cfg,
        )
    assert ok is True


@pytest.mark.asyncio
async def test_pipeline_liveness_with_provenance(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    prov_dir = tmp_path / "logs" / "pipeline"
    prov_dir.mkdir(parents=True)
    (prov_dir / "run_abc.json").write_text(
        json.dumps({"run_id": "abc", "success": True}),
        encoding="utf-8",
    )

    with patch("vla_mcp.pipeline_liveness.FleetBridge") as mock_bridge:
        mock_bridge.return_value.bridge_status = AsyncMock(
            return_value={
                "success": True,
                "peers": [
                    {"name": "yahboom-mcp", "reachable": True, "url": "http://127.0.0.1:10892"},
                ],
            }
        )
        out = await check_pipeline_liveness(stale_hours=168)

    assert out["success"] is True
    assert out["service"] == "vla-mcp"
    assert any(c.get("name") == "vla_last_pipeline" for c in out["checks"])


@pytest.mark.asyncio
async def test_bridge_status_bounds_hanging_probe():
    """A black-holed peer must not hang bridge_status: deadlines mark it unreachable."""
    from vla_mcp.config import VLAConfig

    async def hang_forever(_name: str, _url: str | None) -> dict:
        await asyncio.sleep(3600)
        raise AssertionError("should never return")

    bridge = FleetBridge(config=VLAConfig.from_env())
    with patch.object(FleetBridge, "probe_peer", side_effect=hang_forever):
        start = time.time()
        out = await bridge.bridge_status(peer_timeout=0.2, total_timeout=1.0)
        elapsed = time.time() - start

    assert elapsed < 10
    assert out["success"] is True
    assert len(out["peers"]) == 4
    assert all(p["reachable"] is False for p in out["peers"])
    assert all("deadline exceeded" in p["error"] for p in out["peers"])


@pytest.mark.asyncio
async def test_liveness_probe_phase_has_overall_budget():
    """check_pipeline_liveness resolves even when every probe hangs."""
    from vla_mcp.config import VLAConfig

    async def hang_forever(*args: object, **kwargs: object) -> dict:
        await asyncio.sleep(3600)
        raise AssertionError("should never return")

    cfg = VLAConfig.from_env()
    with (
        patch("vla_mcp.pipeline_liveness.FleetBridge") as mock_bridge,
        patch("vla_mcp.pipeline_liveness._PROBE_BUDGET_S", 1.0),
        patch(
            "vla_mcp.pipeline_liveness._LIVENESS_CACHE",
            {"ts": 0.0, "data": None},
        ),
    ):
        mock_bridge.return_value.bridge_status = AsyncMock(side_effect=hang_forever)
        start = time.time()
        out = await check_pipeline_liveness(stale_hours=168, config=cfg)
        elapsed = time.time() - start

    assert elapsed < 15
    assert out["success"] is True
    assert any(c.get("name") == "liveness_probe" for c in out["checks"])
