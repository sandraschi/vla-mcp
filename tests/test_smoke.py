"""Smoke tests for vla-mcp."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from vla_mcp import __version__
from vla_mcp.engine.dataset_store import DatasetStore
from vla_mcp.engine.wall_runner import WallRunner
from vla_mcp.server import app, mcp


def test_package_version():
    assert __version__ == "0.1.0"


def test_wall_runner_health():
    h = WallRunner.default().health()
    assert h["model"] == "Wall-OSS-0.5"
    assert "reference_repo" in h


@pytest.mark.asyncio
async def test_mcp_tools_registered():
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    for expected in (
        "vla_status",
        "vla_wall",
        "vla_world_model",
        "vla_dataset",
        "vla_training",
        "vla_fleet",
        "vla_agentic_workflow",
    ):
        assert expected in names, f"Missing tool: {expected}"


@pytest.mark.asyncio
async def test_vla_wall_list_tasks():
    result = await mcp.call_tool("vla_wall", {"operation": "list_tasks"})
    assert result is not None


@pytest.mark.asyncio
async def test_dataset_ingest_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    store = DatasetStore.default()
    ing = store.ingest_episode(
        source="test_sim",
        events=["approaching", "making_contact"],
        video_paths=[],
    )
    assert ing["success"] is True
    listed = store.list_episodes()
    assert listed["total"] >= 1


@pytest.mark.asyncio
async def test_api_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["server"] == "vla-mcp"
