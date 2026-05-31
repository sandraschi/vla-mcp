"""Prefab status cards for vla-mcp."""

from __future__ import annotations

from fastmcp import FastMCP

from ..config import get_config
from ..engine.dmuon_runner import DMuonRunner
from ..engine.fleet_bridge import FleetBridge
from ..engine.wall_runner import WallRunner
from ..engine.world_model_runner import WorldModelRunner


def register_prefab_tools(mcp: FastMCP) -> None:
    """Register in-chat Prefab cards when VLA_PREFAB_APPS=1."""
    if not get_config().prefab_apps:
        return
    try:
        from prefab_ui.app import PrefabApp
        from prefab_ui.types import ToolResult
    except ImportError:
        return

    @mcp.tool(app=True)
    async def show_vla_status_card() -> ToolResult:
        """Show VLA fleet status as an in-chat Prefab card.

        Returns:
            ToolResult with plain-text summary and PrefabApp structured_content.
        """
        wall = WallRunner.default().health()
        wm = WorldModelRunner.default().health()
        dm = DMuonRunner.default().health()
        peers = FleetBridge.default().peer_urls()
        lines = [
            f"Wall-OSS: {'ready' if wall['upstream_configured'] else 'not configured'}",
            f"WALL-WM: {'ready' if wm['upstream_configured'] else 'not configured'}",
            f"DMuon: {'ready' if dm['upstream_configured'] else 'not configured'}",
            f"Peers: {', '.join(peers.keys())}",
        ]
        text = "VLA-MCP status\n" + "\n".join(f"- {ln}" for ln in lines)
        card = PrefabApp(
            title="VLA-MCP",
            subtitle="Wall-OSS-0.5 + WALL-WM + DMuon",
            sections=[
                {"title": "Wall-OSS-0.5", "body": str(wall.get("upstream_path") or "unset")},
                {"title": "WALL-WM", "body": str(wm.get("upstream_path") or "unset")},
                {"title": "Dataset", "body": get_config().dataset_root},
            ],
        )
        return ToolResult(content=text, structured_content=card)
