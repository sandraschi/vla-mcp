"""Smoke and Phase 2 tests for vla-mcp."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from vla_mcp import __version__
from vla_mcp.engine.event_segmenter import EventSegmenter
from vla_mcp.engine.hf_weights import HFWeightManager
from vla_mcp.server import app, mcp


def test_package_version():
    assert __version__ == "0.2.0"


def test_event_segmenter():
    seg = EventSegmenter().segment(
        [
            {"timestamp": 0, "velocity": 0.1, "distance_to_target": 1.0},
            {"timestamp": 1, "velocity": 0.5, "distance_to_target": 0.3},
            {"timestamp": 2, "velocity": 0.1, "contact_force": 0.9},
        ]
    )
    assert seg["success"] is True
    assert "approaching" in seg["events"] or "making_contact" in seg["events"]


def test_hf_list_models():
    out = HFWeightManager.default().list_models()
    assert out["success"] is True
    assert len(out["models"]) >= 2


@pytest.mark.asyncio
async def test_mcp_tools_registered():
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    for expected in (
        "vla_status",
        "vla_weights",
        "vla_wall",
        "vla_world_model",
        "vla_dataset",
        "vla_events",
        "vla_training",
        "vla_fleet",
        "vla_agentic_workflow",
    ):
        assert expected in names, f"Missing tool: {expected}"


@pytest.mark.asyncio
async def test_training_dry_run():
    result = await mcp.call_tool(
        "vla_training",
        {"operation": "launch_co_train", "dry_run": True},
    )
    assert result is not None


@pytest.mark.asyncio
async def test_dataset_segment_telemetry(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    result = await mcp.call_tool(
        "vla_dataset",
        {
            "operation": "segment_telemetry",
            "source": "unit_test",
            "telemetry": [
                {"velocity": 0.2, "distance_to_target": 0.4},
                {"contact_force": 0.8, "velocity": 0.05},
            ],
        },
    )
    assert result is not None


@pytest.mark.asyncio
async def test_api_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["server"] == "vla-mcp"


@pytest.mark.asyncio
async def test_api_capabilities():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/capabilities")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["features"]["hf_weights"] is True


@pytest.mark.asyncio
async def test_api_tools_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tools")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 9
