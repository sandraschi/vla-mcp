"""FastAPI routes for the VLA dashboard."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastmcp import FastMCP

from .config import get_config
from .engine.dataset_store import DatasetStore
from .engine.dmuon_runner import DMuonRunner
from .engine.fleet_bridge import FleetBridge
from .engine.hf_weights import HFWeightManager
from .engine.notebook_store import NOTEBOOKS, NotebookStore
from .engine.pipeline_runner import PipelineRunner
from .engine.wall_runner import WallRunner
from .engine.world_model_runner import WorldModelRunner
from .engine.xvla_adapter import XVLAAdapter
from .pipeline_liveness import check_pipeline_liveness
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

    @app.get("/api/health")
    async def api_health() -> JSONResponse:
        return JSONResponse({"status": "ok", "server": "vla-mcp"})

    @app.get("/api/pipeline/liveness")
    async def api_pipeline_liveness(stale_hours: int = 168) -> JSONResponse:
        return JSONResponse(await check_pipeline_liveness(stale_hours=stale_hours))

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

    @app.get("/api/v1/training/jobs/{job_id}/log")
    async def api_job_log(job_id: str, offset: int = 0) -> dict:
        return DMuonRunner.default().job_log(job_id, offset=offset)

    @app.get("/api/v1/training/jobs/{job_id}/log/stream")
    async def api_job_log_stream(job_id: str) -> StreamingResponse:
        runner = DMuonRunner.default()

        async def event_stream():
            offset = 0
            while True:
                chunk = runner.job_log(job_id, offset=offset)
                if not chunk.get("success"):
                    yield f"data: {json.dumps(chunk)}\n\n"
                    break
                payload = {
                    "offset": chunk.get("offset"),
                    "next_offset": chunk.get("next_offset"),
                    "text": chunk.get("text", ""),
                    "eof": chunk.get("eof"),
                }
                yield f"data: {json.dumps(payload)}\n\n"
                offset = int(chunk.get("next_offset") or offset)
                job = runner.job_status(job_id=job_id).get("job") or {}
                if chunk.get("eof") and job.get("status") != "running":
                    break
                await asyncio.sleep(1.0)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.get("/api/v1/pipeline/last")
    async def api_pipeline_last() -> dict:
        return PipelineRunner.default().last_run()

    @app.post("/api/v1/pipeline/run")
    async def api_pipeline_run(request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        allowed, reason = rest_control_allowed(
            "vla_pipeline",
            {"operation": "run", **body},
            confirm_header=request.headers.get("X-VLA-Confirm"),
        )
        if not allowed:
            raise HTTPException(status_code=403, detail=reason or "REST control denied")
        fn = all_tools.get("vla_pipeline")
        if fn is None:
            raise HTTPException(status_code=404, detail="vla_pipeline not registered")
        return await fn(operation="run", **{k: v for k, v in body.items() if k != "operation"})

    @app.get("/api/v1/notebooks")
    async def api_notebooks() -> JSONResponse:
        return JSONResponse({"success": True, "notebooks": NotebookStore.default().summaries()})

    @app.get("/api/v1/notebooks/{name}/entries")
    async def api_notebook_entries(
        name: str,
        limit: int = 50,
        offset: int = 0,
        category: str | None = None,
    ) -> JSONResponse:
        if name not in NOTEBOOKS:
            raise HTTPException(status_code=404, detail=f"Notebook must be one of {NOTEBOOKS}")
        return JSONResponse(NotebookStore.default().list_entries(name, limit=limit, offset=offset, category=category))

    @app.post("/api/v1/notebooks/{name}/entries")
    async def api_notebook_add(name: str, request: Request) -> Any:
        if name not in NOTEBOOKS:
            raise HTTPException(status_code=404, detail=f"Notebook must be one of {NOTEBOOKS}")
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        result = NotebookStore.default().add_entry(
            name,
            title=str(body.get("title") or ""),
            body=str(body.get("body") or ""),
            category=str(body.get("category") or "note"),
            author=str(body.get("author") or "sandra"),
            tags=body.get("tags") if isinstance(body.get("tags"), list) else None,
            metrics=body.get("metrics") if isinstance(body.get("metrics"), dict) else None,
        )
        if not result.get("success"):
            raise HTTPException(status_code=422, detail=result.get("error", "Invalid entry"))
        return result

    @app.delete("/api/v1/notebooks/{name}/entries/{entry_id}")
    async def api_notebook_delete(name: str, entry_id: str) -> dict:
        if name not in NOTEBOOKS:
            raise HTTPException(status_code=404, detail=f"Notebook must be one of {NOTEBOOKS}")
        deleted = NotebookStore.default().delete_entry(name, entry_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Entry not found")
        return {"success": True, "deleted": entry_id}

    @app.post("/api/v1/notebooks/news/digest")
    async def api_notebook_news_digest() -> Any:
        from .tools.diary import _build_digest

        return await _build_digest()

    @app.get("/api/v1/help")
    async def api_help_index() -> dict:
        from .help_content import get_help, list_slugs

        index = get_help(None)
        return {"slugs": list_slugs(), "topics": index.get("topics", []), "overview": index.get("markdown", "")}

    @app.get("/api/v1/help/{slug}")
    async def api_help_slug(slug: str) -> dict:
        from .help_content import get_help

        result = get_help(slug)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Unknown help slug"))
        return {
            "slug": slug,
            "markdown": result.get("markdown", ""),
            "content": result.get("content") or result.get("markdown", ""),
        }

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
                "e2e_pipeline": True,
                "job_persistence": True,
                "log_streaming": True,
                "prefab": cfg.prefab_apps,
                "sampling": True,
                "agentic_workflows": True,
                "prompts": True,
                "resources": True,
                "skills": True,
            },
            "inventory": {
                "workflow_tools": ["vla_agentic_workflow", "vla_pipeline"],
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
