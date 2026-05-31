"""FastAPI routes for the VLA dashboard."""

from __future__ import annotations

import json
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastmcp import FastMCP

from .config import get_config
from .engine.dataset_store import DatasetStore
from .engine.dmuon_runner import DMuonRunner
from .engine.fleet_bridge import FleetBridge
from .engine.hf_weights import HFWeightManager
from .engine.wall_runner import WallRunner
from .engine.world_model_runner import WorldModelRunner
from .engine.xvla_adapter import XVLAAdapter
from .rest_policy import rest_control_allowed

_START = time.time()
_REPO_ROOT: Path | None = None


def _repo_root() -> Path:
    global _REPO_ROOT
    if _REPO_ROOT is not None:
        return _REPO_ROOT
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            _REPO_ROOT = parent
            return parent
    _REPO_ROOT = here.parents[2]
    return _REPO_ROOT


def setup_webapp(
    app: FastAPI,
    mcp: FastMCP,
    all_tools: dict[str, Callable[..., Awaitable[Any]]],
) -> None:
    """Register REST endpoints used by the Vite frontend."""

    @app.get("/api/v1/status")
    async def api_status() -> JSONResponse:
        cfg = get_config()
        store = DatasetStore.default()
        ep = store.list_episodes(limit=1)
        return JSONResponse(
            {
                "server": "vla-mcp",
                "mcp_name": mcp.name,
                "version": mcp.version,
                "mode": "dual",
                "api_port": cfg.api_port,
                "frontend_port": cfg.frontend_port,
                "uptime_s": round(time.time() - _START, 1),
                "wall": WallRunner.default().health(),
                "world_model": WorldModelRunner.default().health(),
                "dmuon": DMuonRunner.default().health(),
                "xvla": XVLAAdapter.default().health(),
                "weights": HFWeightManager.default().list_models(),
                "dataset_root": cfg.dataset_root,
                "dataset_episodes": ep.get("total", 0),
            }
        )

    @app.get("/api/v1/tools")
    async def api_tools() -> dict:
        return {"count": len(all_tools), "tools": sorted(all_tools.keys())}

    @app.post("/api/v1/control/{tool_name}")
    async def api_control(tool_name: str, request: Request) -> Any:
        fn = all_tools.get(tool_name)
        if fn is None:
            raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        allowed, reason = rest_control_allowed(
            tool_name,
            body,
            confirm_header=request.headers.get("X-VLA-Confirm"),
        )
        if not allowed:
            raise HTTPException(status_code=403, detail=reason or "REST control denied")
        return await fn(**body)

    @app.get("/api/v1/fleet")
    async def api_fleet() -> JSONResponse:
        body = await FleetBridge.default().bridge_status()
        return JSONResponse(body)

    @app.get("/api/v1/dataset/episodes")
    async def api_episodes(limit: int = 50, offset: int = 0) -> dict:
        return DatasetStore.default().list_episodes(limit=limit, offset=offset)

    @app.get("/api/v1/training/jobs")
    async def api_jobs() -> dict:
        return DMuonRunner.default().job_status()

    @app.get("/api/v1/help")
    async def api_help_index() -> dict:
        docs = _repo_root() / "docs"
        slugs = []
        for name in ("PRD.md", "ARCHITECTURE.md", "SETUP.md", "TOOLS.md", "CONFIGURATION.md", "TROUBLESHOOTING.md"):
            if (docs / name).is_file():
                slugs.append(name.replace(".md", "").lower())
        return {"slugs": slugs}

    @app.get("/api/v1/help/{slug}")
    async def api_help_slug(slug: str) -> dict:
        mapping = {
            "prd": "PRD.md",
            "architecture": "ARCHITECTURE.md",
            "setup": "SETUP.md",
            "tools": "TOOLS.md",
            "configuration": "CONFIGURATION.md",
            "troubleshooting": "TROUBLESHOOTING.md",
            "development": "DEVELOPMENT.md",
        }
        fname = mapping.get(slug.lower(), f"{slug.upper()}.md")
        path = _repo_root() / "docs" / fname
        if not path.is_file():
            raise HTTPException(status_code=404, detail=f"Unknown help slug: {slug}")
        content = path.read_text(encoding="utf-8")
        return {"slug": slug, "markdown": content, "content": content}

    @app.get("/api/capabilities")
    async def api_capabilities() -> dict:
        cfg = get_config()
        store = DatasetStore.default()
        idx = store.list_episodes(limit=1)
        tool_names = sorted(all_tools.keys())
        return {
            "status": "ok",
            "server": {"name": "vla-mcp", "version": mcp.version, "fastmcp": "3.2+"},
            "tool_surface": {
                "total": len(tool_names),
                "portmanteau_count": len(tool_names),
                "atomic_count": 0,
                "portmanteau_tools": tool_names,
                "atomic_tools": [],
            },
            "features": {
                "wall_oss": True,
                "wall_wm": True,
                "dmuon": True,
                "xvla_peft": True,
                "hf_weights": True,
                "event_joints": True,
                "dataset_store": True,
                "fleet_bridge": True,
                "prefab": cfg.prefab_apps,
                "sampling": True,
                "agentic_workflows": True,
                "prompts": True,
                "resources": True,
                "skills": True,
            },
            "inventory": {
                "workflow_tools": ["vla_agentic_workflow"],
                "prompt_names": ["vla_co_train_session", "vla_zero_shot_deploy"],
                "resource_uris": ["resource://vla/quickstart"],
                "skill_uris": ["skill://vla-expert/SKILL.md"],
            },
            "runtime": {"transport": "dual", "surface_mode": "portmanteau"},
            "ports": {"backend": cfg.api_port, "frontend": cfg.frontend_port},
            "dataset_episodes": idx.get("total", 0),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    @app.get("/.well-known/mcp/manifest.json")
    async def well_known_manifest() -> dict:
        manifest = _repo_root() / "manifest.json"
        if manifest.is_file():
            return json.loads(manifest.read_text(encoding="utf-8"))
        return {
            "name": "vla-mcp",
            "version": mcp.version,
            "description": "Vision-Language-Action bridge: Wall-OSS-0.5, WALL-WM, DMuon",
            "transport": {"stdio": True, "http": f"http://127.0.0.1:{get_config().api_port}/mcp"},
        }
