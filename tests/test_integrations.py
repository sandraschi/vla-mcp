"""Fleet integration: aiwatcher ingest and pipeline liveness."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

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
