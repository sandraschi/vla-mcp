"""FastAPI routes for the VLA dashboard."""

from __future__ import annotations

import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

from .config import get_config
from .engine.dataset_store import DatasetStore
from .engine.dmuon_runner import DMuonRunner
from .engine.fleet_bridge import FleetBridge
from .engine.wall_runner import WallRunner
from .engine.world_model_runner import WorldModelRunner

_START = time.time()


def setup_webapp(app: FastAPI, mcp: FastMCP) -> None:
    """Register REST endpoints used by the Vite frontend."""

    @app.get("/api/v1/status")
    async def api_status() -> JSONResponse:
        cfg = get_config()
        return JSONResponse(
            {
                "server": "vla-mcp",
                "mcp_name": mcp.name,
                "version": mcp.version,
                "api_port": cfg.api_port,
                "frontend_port": cfg.frontend_port,
                "uptime_s": round(time.time() - _START, 1),
                "wall": WallRunner.default().health(),
                "world_model": WorldModelRunner.default().health(),
                "dmuon": DMuonRunner.default().health(),
                "dataset_root": cfg.dataset_root,
            }
        )

    @app.get("/api/v1/fleet")
    async def api_fleet() -> JSONResponse:
        body = await FleetBridge.default().bridge_status()
        return JSONResponse(body)

    @app.get("/api/capabilities")
    async def api_capabilities() -> dict:
        cfg = get_config()
        store = DatasetStore.default()
        idx = store.list_episodes(limit=1)
        return {
            "server": {"name": "vla-mcp", "version": mcp.version},
            "features": {
                "wall_oss": True,
                "wall_wm": True,
                "dmuon": True,
                "dataset_store": True,
                "fleet_bridge": True,
                "prefab": cfg.prefab_apps,
            },
            "ports": {"backend": cfg.api_port, "frontend": cfg.frontend_port},
            "dataset_episodes": idx.get("total", 0),
        }

    @app.get("/.well-known/mcp/manifest.json")
    async def well_known_manifest() -> dict:
        return {
            "name": "vla-mcp",
            "version": mcp.version,
            "description": "Vision-Language-Action bridge: Wall-OSS-0.5, WALL-WM, DMuon, fleet loops",
            "transport": {"stdio": True, "http": f"http://127.0.0.1:{get_config().api_port}/mcp"},
        }
