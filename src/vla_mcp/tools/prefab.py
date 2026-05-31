"""Prefab status cards for vla-mcp."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from prefab_ui.app import PrefabApp
from prefab_ui.components import Card, CardContent, CardHeader, CardTitle, Text

from ..config import get_config


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
        with Card(className="max-w-lg"):
            with CardHeader():
                CardTitle("VLA-MCP Status")
            with CardContent():
                Text(f"Wall-OSS: {wall.get('upstream_path') or 'not configured'}")
                Text(f"WALL-WM: {wm.get('upstream_path') or 'not configured'}")
                Text(f"DMuon jobs: {dm.get('active_jobs', 0)} active")
                Text(f"X-VLA edge: {xvla.get('upstream_path') or 'not configured'}")
                Text(f"Dataset: {data.get('dataset_root', '?')}")
                Text(f"Episodes: {data.get('dataset_episodes', 0)}")
        return PrefabApp(view=Card, title="VLA-MCP Status")
