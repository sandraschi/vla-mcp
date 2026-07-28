"""Fleet bridge yahboom REST routing tests."""

from __future__ import annotations

import pytest

from vla_mcp.engine.fleet_bridge import FleetBridge
from vla_mcp.engine.pipeline_runner import PipelineRunner, _telemetry_from_boomy_demo


def test_yahboom_tool_body():
    bridge = FleetBridge.default()
    body = bridge._yahboom_tool_body({"operation": "read_imu"})
    assert body == {"operation": "read_imu"}


def test_yahboom_demo_routes_talkbot():
    bridge = FleetBridge.default()
    routes = bridge._yahboom_demo_routes({"operation": "talkbot", "max_turns": 2, "scripted_user_lines": ["Hi"]})
    assert routes[0] == (
        "POST",
        "/api/v1/demo/talkbot",
        {"max_turns": 2, "scripted_user_lines": ["Hi"]},
    )


@pytest.mark.asyncio
async def test_yahboom_tool_uses_control_tool(monkeypatch):
    bridge = FleetBridge.default()
    captured: dict = {}

    async def fake_post(path, body=None, **kw):
        captured["path"] = path
        captured["body"] = body
        return {"success": True, "result": {"imu": [1, 2, 3]}}

    monkeypatch.setattr(bridge, "yahboom_post", fake_post)
    out = await bridge.yahboom_tool("read_imu")
    assert out["success"] is True
    assert captured["path"] == "/api/v1/control/tool"
    assert captured["body"]["operation"] == "read_imu"


@pytest.mark.asyncio
async def test_poll_yahboom_demo_completes(monkeypatch):
    bridge = FleetBridge.default()
    calls = {"n": 0}

    async def fake_get(path, **kw):
        calls["n"] += 1
        if calls["n"] < 2:
            return {"success": True, "result": {"running": True, "status": "running"}}
        return {"success": True, "result": {"running": False, "status": "completed"}}

    monkeypatch.setattr(bridge, "yahboom_get", fake_get)
    out = await bridge.poll_yahboom_demo("talkbot", timeout_s=5, poll_s=0.01)
    assert out["success"] is True
    assert out["result"]["status"] == "completed"


def test_telemetry_from_boomy_talkbot():
    demo_result = {
        "demo": "talkbot",
        "final": {
            "transcript": [
                {"role": "boomy", "text": "Hi, I am Boomy. Who are you?"},
                {"role": "user", "text": "I am Alex"},
            ]
        },
    }
    rows = _telemetry_from_boomy_demo("talkbot", demo_result, include_failures=False)
    assert rows[0]["event"] == "approaching"
    assert any(r.get("event") == "dialogue" for r in rows)


@pytest.mark.asyncio
async def test_pipeline_live_boomy_mocked(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    monkeypatch.setenv("YAHBOOM_DEMO_FAST", "1")

    runner = PipelineRunner.default()

    async def fake_live_steps(bridge, **kwargs):
        return (
            [{"name": "boomy_talkbot", "success": True}],
            {
                "reachable_count": 1,
                "boomy_demo": {
                    "success": True,
                    "demo": "talkbot",
                    "final": {"transcript": [{"role": "user", "text": "Alex"}]},
                },
            },
        )

    monkeypatch.setattr(runner, "_live_fleet_steps", fake_live_steps)
    out = await runner.run(live=True, boomy_demo="talkbot", fallback_simulate=False)
    assert out["success"] is True
    assert out["mode"] == "live"
    assert out["boomy_demo"] == "talkbot"
