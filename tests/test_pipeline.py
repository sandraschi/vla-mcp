"""End-to-end pipeline and job persistence tests."""

from __future__ import annotations

import pytest

from vla_mcp.engine.dmuon_runner import DMuonRunner, _jobs
from vla_mcp.engine.job_registry import load_jobs, read_log_tail
from vla_mcp.engine.pipeline_runner import PipelineRunner
from vla_mcp.rest_policy import rest_control_allowed
from vla_mcp.server import mcp


@pytest.mark.asyncio
async def test_pipeline_simulated_run(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    runner = PipelineRunner.default()
    out = await runner.run(live=False, include_failures=True)
    assert out["success"] is True
    assert out["mode"] == "simulated"
    assert out.get("episode_id")
    assert out.get("arrays_written", 0) >= 1
    assert out.get("dmuon_command")
    provenance = tmp_path / "logs" / "pipeline" / f"run_{out['run_id']}.json"
    assert provenance.is_file()


@pytest.mark.asyncio
async def test_pipeline_mcp_tool(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    result = await mcp.call_tool(
        "vla_pipeline",
        {"operation": "run", "live": False, "include_failures": True},
    )
    assert result is not None


@pytest.mark.asyncio
async def test_pipeline_describe():
    out = PipelineRunner.default().describe()
    assert out["success"] is True
    assert "dmuon_dry_run" in out["pipeline"]


def test_job_registry_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    _jobs.clear()
    _jobs["persist1"] = {
        "id": "persist1",
        "status": "completed",
        "pid": 1,
        "log_path": str(tmp_path / "logs" / "dmuon_persist1.log"),
    }
    from vla_mcp.engine.job_registry import upsert_job

    upsert_job(str(tmp_path), _jobs, "persist1", _jobs["persist1"])
    loaded = load_jobs(str(tmp_path))
    assert "persist1" in loaded
    assert loaded["persist1"]["status"] == "completed"


def test_read_log_tail(tmp_path):
    log = tmp_path / "sample.log"
    log.write_text("line1\nline2\n", encoding="utf-8")
    out = read_log_tail(str(log))
    assert out["success"] is True
    assert "line1" in out["text"]


def test_rest_pipeline_requires_confirm():
    ok, _ = rest_control_allowed("vla_pipeline", {"operation": "run"}, confirm_header=None)
    assert ok is False
    ok2, _ = rest_control_allowed("vla_pipeline", {"operation": "run"}, confirm_header="1")
    assert ok2 is True


@pytest.mark.asyncio
async def test_api_pipeline_run(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    from httpx import ASGITransport, AsyncClient

    from vla_mcp.server import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/pipeline/run",
            json={"live": False},
            headers={"X-VLA-Confirm": "1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("success") is True
        assert body.get("mode") == "simulated"

        last = await client.get("/api/v1/pipeline/last")
        assert last.status_code == 200
        assert last.json().get("success") is True


def test_dmuon_introspect_without_upstream():
    out = DMuonRunner.default().introspect_train_args()
    assert out["success"] is False
