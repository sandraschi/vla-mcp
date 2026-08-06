"""Smoke and Phase 2 tests for vla-mcp."""

from __future__ import annotations

import json

import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

from vla_mcp import __version__
from vla_mcp.engine.dataset_store import DatasetStore
from vla_mcp.engine.dmuon_runner import DMuonRunner, _jobs
from vla_mcp.engine.event_segmenter import EventSegmenter
from vla_mcp.engine.hf_weights import HFWeightManager, _slug
from vla_mcp.engine.xvla_adapter import XVLAAdapter
from vla_mcp.rest_policy import rest_control_allowed
from vla_mcp.server import app, mcp


def test_package_version():
    assert __version__ == "0.3.1b1"


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


def test_hf_slug_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_HF_CACHE_DIR", str(tmp_path))
    mgr = HFWeightManager.default()
    key = "wall-oss-0.5"
    local = mgr.local_dir_for(key)
    local.mkdir(parents=True)
    (local / "config.json").write_text("{}", encoding="utf-8")
    out = mgr.list_models()
    row = next(m for m in out["models"] if m["key"] == key)
    assert row["downloaded"] is True
    assert _slug(key) == "wall_oss_0_5"


def test_hf_list_models_includes_xvla():
    out = HFWeightManager.default().list_models()
    assert out["success"] is True
    keys = {m["key"] for m in out["models"]}
    assert "x-vla" in keys
    assert len(out["models"]) >= 3


def test_job_status_json_serializable():
    _jobs.clear()
    _jobs["testjob"] = {
        "id": "testjob",
        "status": "running",
        "pid": 4242,
        "command": ["python", "-c", "print(1)"],
    }
    out = DMuonRunner.default().job_status()
    payload = json.dumps(out)
    assert "testjob" in payload
    _jobs.clear()


def test_numpy_export_copies_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    store = DatasetStore.default()
    src = tmp_path / "src_actions.npy"
    np.save(src, np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32))
    ing = store.ingest_episode(
        source="unit",
        events=["approaching"],
        action_path=str(src),
    )
    assert ing["success"] is True
    out = store.export_numpy_shard(shard_name="train_a")
    assert out["success"] is True
    assert out["arrays_written"] == 1
    arrays_dir = tmp_path / "exports" / "numpy" / "train_a"
    assert (arrays_dir / f"{ing['episode_id']}_actions.npy").is_file()


def test_numpy_export_inline_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    store = DatasetStore.default()
    store.ingest_episode(
        source="unit",
        events=["contact"],
        actions=[[0.1, 0.2], [0.3, 0.4]],
    )
    out = store.export_numpy_shard(shard_name="inline")
    assert out["success"] is True
    assert out["arrays_written"] == 1


def test_xvla_edge_prepare():
    out = XVLAAdapter.default().edge_prepare(target="raspbot")
    assert out["success"] is True
    assert out["target"] == "raspbot"
    assert "vla_xvla" in out["steps"][1]


def test_rest_policy_blocks_agentic():
    ok, _ = rest_control_allowed("vla_agentic_workflow", {"goal": "x"}, confirm_header=None)
    assert ok is False


def test_rest_policy_mutating_requires_confirm():
    ok, reason = rest_control_allowed(
        "vla_training",
        {"operation": "launch_co_train", "confirm": True},
        confirm_header=None,
    )
    assert ok is False
    assert reason is not None
    ok2, _ = rest_control_allowed(
        "vla_training",
        {"operation": "launch_co_train", "confirm": True},
        confirm_header="1",
    )
    assert ok2 is True


@pytest.mark.asyncio
async def test_mcp_tools_registered():
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    for expected in (
        "vla_status",
        "vla_weights",
        "vla_wall",
        "vla_xvla",
        "vla_world_model",
        "vla_dataset",
        "vla_events",
        "vla_training",
        "vla_fleet",
        "vla_pipeline",
        "vla_agentic_workflow",
    ):
        assert expected in names, f"Missing tool: {expected}"


@pytest.mark.asyncio
async def test_pipeline_liveness_tool():
    result = await mcp.call_tool("vla_pipeline_liveness", {"stale_hours": 168})
    assert result is not None


@pytest.mark.asyncio
async def test_prefab_tool_registered(monkeypatch):
    monkeypatch.setenv("VLA_PREFAB_APPS", "1")
    from vla_mcp.server import build_mcp

    test_mcp = build_mcp()
    tools = await test_mcp.list_tools()
    names = {t.name for t in tools}
    if "show_vla_status_card" not in names:
        pytest.skip("prefab-ui not installed or Prefab registration unavailable")
    assert "show_vla_status_card" in names
    assert "show_pipeline_run_card" in names


@pytest.mark.asyncio
async def test_training_dry_run():
    result = await mcp.call_tool(
        "vla_training",
        {"operation": "launch_co_train", "dry_run": True},
    )
    assert result is not None


@pytest.mark.asyncio
async def test_vla_xvla_health():
    result = await mcp.call_tool("vla_xvla", {"operation": "health"})
    assert result is not None


@pytest.mark.asyncio
async def test_wall_edge_prepare():
    result = await mcp.call_tool("vla_wall", {"operation": "edge_prepare", "target": "raspbot"})
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
        assert "xvla" in body


@pytest.mark.asyncio
async def test_api_capabilities():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/capabilities")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["features"]["xvla_peft"] is True


@pytest.mark.asyncio
async def test_api_tools_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tools")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 12


def test_rest_policy_world_requires_confirm():
    ok, _ = rest_control_allowed("vla_world", {"operation": "generate"}, confirm_header=None)
    assert ok is False
    ok2, _ = rest_control_allowed("vla_world", {"operation": "generate"}, confirm_header="1")
    assert ok2 is True


@pytest.mark.asyncio
async def test_vla_world_describe():
    result = await mcp.call_tool("vla_world", {"operation": "describe"})
    assert result is not None


@pytest.mark.asyncio
async def test_api_agentic_blocked():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/control/vla_agentic_workflow", json={"goal": "test"})
        assert resp.status_code == 403
