"""Prefab status + pipeline cards for vla-mcp."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    H3,
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
    Code,
    Grid,
    Mermaid,
    Metric,
    Text,
)

from ..config import get_config
from ..engine.pipeline_runner import PipelineRunner

LOOP_MERMAID = """flowchart LR
  WL["worldlabs<br/>3D room"] --> YB["yahboom<br/>telemetry"]
  YB --> SEG["event-joint<br/>segmentation"]
  SEG --> ING["ingest<br/>episode"]
  ING --> NPY["numpy<br/>shard"]
  NPY --> DM["DMuon<br/>co-train"]
"""


def register_prefab_tools(
    mcp,
    all_tools: dict[str, Callable[..., Awaitable[Any]]],
) -> None:
    """Register in-chat Prefab cards when VLA_PREFAB_APPS=1."""
    if not get_config().prefab_apps:
        return

    @mcp.tool(app=True)
    async def show_vla_status_card() -> PrefabApp:
        """Show VLA stack status as an in-chat Prefab card."""
        fn = all_tools.get("vla_status")
        data = await fn() if fn else {"success": False}
        wall = data.get("wall") or {}
        wm = data.get("world_model") or {}
        dm = data.get("dmuon") or {}
        xvla = data.get("xvla") or {}
        with Card(className="max-w-lg") as card:
            with CardHeader():
                CardTitle("VLA-MCP Status")
            with CardContent():
                Text(f"Wall-OSS: {wall.get('upstream_path') or 'not configured'}")
                Text(f"WALL-WM: {wm.get('upstream_path') or 'not configured'}")
                Text(f"DMuon jobs: {dm.get('active_jobs', 0)} active")
                Text(f"X-VLA edge: {xvla.get('upstream_path') or 'not configured'}")
                Text(f"Dataset: {data.get('dataset_root', '?')}")
                Text(f"Episodes: {data.get('dataset_episodes', 0)}")
        return PrefabApp(view=card, title="VLA-MCP Status")

    @mcp.tool(app=True)
    async def show_pipeline_run_card() -> PrefabApp:
        """Show the most recent end-to-end pipeline run as an in-chat Prefab card.

        Renders the closed-loop diagram, metric tiles (shard arrays, event-joints, mode),
        the event chain, and the DMuon command. Run vla_pipeline(operation='run') first.
        """
        out = PipelineRunner.default().last_run()
        if not out.get("success"):
            with Card(className="max-w-xl") as empty:
                with CardHeader():
                    CardTitle("VLA-MCP Pipeline")
                    CardDescription(content="No run recorded yet")
                with CardContent():
                    Mermaid(chart=LOOP_MERMAID)
                    Text("Run vla_pipeline(operation='run', live=False) to populate this card.")
            return PrefabApp(view=empty, title="VLA-MCP Pipeline")

        run = out.get("run") or {}
        mode = str(run.get("mode", "?"))
        run_id = str(run.get("run_id", "?"))
        shard = str(run.get("shard_name", "?"))
        arrays = run.get("arrays_written", 0)
        chain = run.get("event_chain") or []
        cmd = run.get("dmuon_command") or []
        cmd_str = " ".join(str(c) for c in cmd) if isinstance(cmd, list) else str(cmd)
        finished = str(run.get("finished_at", ""))

        with Card(className="max-w-2xl") as card:
            with CardHeader():
                CardTitle("VLA-MCP Pipeline")
                CardDescription(content=f"{mode} · run {run_id} · {finished}")
            with CardContent():
                with Grid(columns=3):
                    Metric(label="Shard arrays", value=str(arrays), description=shard)
                    Metric(label="Event joints", value=str(len(chain)), description="transitions")
                    Metric(label="Mode", value=mode, description="sim / live")
                Mermaid(chart=LOOP_MERMAID)
                if chain:
                    Text(f"Events: {' → '.join(str(e) for e in chain)}")
                if cmd_str:
                    H3(content="DMuon command")
                    Code(content=cmd_str, language="bash")
        return PrefabApp(view=card, title="VLA-MCP Pipeline")
