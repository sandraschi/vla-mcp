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

    @app.get("/api/fleet/apps")
    async def api_fleet_apps() -> dict:
        """Apps Hub discovery: known fleet apps + experimental extras.

        Known = this server + the four configured peers. Anything arriving via
        VLA_MCP_BRIDGE_URLS that is not a known peer lands in "experimental".
        """
        cfg = get_config()
        bridge = FleetBridge.default()
        peers = bridge.peer_urls()
        apps: list[dict[str, Any]] = [
            {
                "name": "vla-mcp",
                "role": "this server",
                "backend_url": f"http://127.0.0.1:{cfg.api_port}",
                "frontend_url": f"http://127.0.0.1:{cfg.frontend_port}",
                "reachable": True,
                "experimental": False,
            }
        ]
        for name, url in peers.items():
            probe = await bridge.probe_peer(name, url)
            apps.append(
                {
                    "name": name,
                    "role": "fleet peer",
                    "backend_url": url,
                    "frontend_url": None,
                    "reachable": bool(probe.get("reachable", False)),
                    "experimental": False,
                }
            )
        experimental: list[dict[str, Any]] = []
        known_urls = {u.rstrip("/") for u in peers.values() if u}
        raw = cfg.mcp_bridge_urls or ""
        for url in [u.strip() for u in raw.split(",") if u.strip()]:
            if url.rstrip("/") in known_urls:
                continue
            probe = await bridge.probe_peer(url, url)
            experimental.append(
                {
                    "name": url,
                    "role": "extra bridge",
                    "backend_url": url,
                    "frontend_url": None,
                    "reachable": bool(probe.get("reachable", False)),
                    "experimental": True,
                }
            )
        return {"apps": apps, "experimental": experimental}

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

    @app.post("/api/shutdown")
    async def api_shutdown() -> JSONResponse:
        import os as _os

        async def _exit_later() -> None:
            await asyncio.sleep(0.5)
            _os._exit(0)

        _task = asyncio.create_task(_exit_later())
        _task.set_name("vla-shutdown")
        return JSONResponse({"success": True, "message": "vla-mcp shutting down"})

    @app.get("/api/skills")
    async def api_skills() -> dict:
        """Skill-first chat preprompt source: bundled domain skills."""
        skills: list[dict[str, Any]] = [
            {
                "uri": "resource://vla/quickstart",
                "name": "vla-quickstart",
                "description": "VLA-MCP quickstart: status, fleet brief, ingest, export, DMuon.",
            }
        ]
        skill_file = _repo_root() / "src" / "vla_mcp" / "skills" / "vla-expert" / "SKILL.md"
        if skill_file.is_file():
            skills.append(
                {
                    "uri": "skill://vla-expert/SKILL.md",
                    "name": "vla-expert",
                    "description": "VLA co-training with Wall-OSS-0.5, WALL-WM, and fleet loops.",
                    "content": skill_file.read_text(encoding="utf-8"),
                }
            )
        return {"skills": skills}

    @app.get("/api/llm/discover")
    async def api_llm_discover() -> dict:
        """Probe local LLM providers (Ollama :11434, LM Studio :1234)."""
        import httpx as _httpx

        providers: list[dict[str, Any]] = []
        async with _httpx.AsyncClient(timeout=2.0) as client:
            for pid, label, base in (
                ("ollama", "Ollama (local, free)", "http://127.0.0.1:11434"),
                ("lmstudio", "LM Studio (local, free)", "http://127.0.0.1:1234"),
            ):
                detected = False
                try:
                    path = "/api/tags" if pid == "ollama" else "/v1/models"
                    resp = await client.get(base + path)
                    detected = resp.status_code == 200
                except Exception:
                    detected = False
                providers.append({"id": pid, "label": label, "detected": detected, "base_url": base})
        return {"providers": providers}

    @app.get("/api/llm/providers")
    async def api_llm_providers() -> dict:
        """Local detected flags + cloud configured flags (never key bytes)."""
        import os as _os

        discovered = await api_llm_discover()
        providers = discovered["providers"]
        clouds = [
            {"id": "openai", "label": "OpenAI (cloud, paid)", "configured": bool(_os.getenv("OPENAI_API_KEY"))},
            {
                "id": "anthropic",
                "label": "Anthropic (cloud, paid)",
                "configured": bool(_os.getenv("ANTHROPIC_API_KEY")),
            },
        ]
        return {"providers": providers, "cloud": clouds}

    @app.get("/api/llm/models")
    async def api_llm_models(provider: str = "ollama") -> dict:
        """Model list per provider: live when reachable, curated fallback otherwise."""
        import httpx as _httpx

        fallback = {
            "ollama": ["qwen3:8b", "llama3.1:8b", "mistral:7b"],
            "lmstudio": ["local-model"],
        }
        base = "http://127.0.0.1:11434" if provider == "ollama" else "http://127.0.0.1:1234"
        path = "/api/tags" if provider == "ollama" else "/v1/models"
        models: list[str] = []
        try:
            async with _httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(base + path)
                if resp.status_code == 200:
                    data = resp.json()
                    if provider == "ollama":
                        models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    else:
                        models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                    if models:
                        return {"provider": provider, "models": models, "live": True}
        except Exception:
            models = []
        return {"provider": provider, "models": fallback.get(provider, []), "live": False}

    @app.get("/api/llm/onboarding")
    async def api_llm_onboarding() -> dict:
        """Fresh-install starter facts + recommended path for the under-hero cue."""
        discovered = await api_llm_discover()
        detected = [p["id"] for p in discovered["providers"] if p["detected"]]
        if detected:
            path = f"Chat works now via {detected[0]}. Pick a model in Settings."
        else:
            path = "Install Ollama (https://ollama.me) and pull qwen3:8b, then chat here for free."
        return {
            "detected": detected,
            "mock": not detected,
            "recommended_path": path,
            "facts": [
                "vla-mcp is a training-pipeline bridge; chat answers VLA/fleet questions.",
                "DMuon launches and weight downloads are confirm-gated and never auto-run.",
                "Keys never leave this server: chat goes through POST /api/llm/chat.",
            ],
        }

    @app.post("/api/llm/chat")
    async def api_llm_chat(request: Request) -> Any:
        """Backend chat proxy — the ONLY path Chat uses. Keys never leave the server."""
        import httpx as _httpx

        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        provider = str(body.get("provider") or "ollama")
        model = str(body.get("model") or "")
        messages = body.get("messages") or []
        if not messages:
            raise HTTPException(status_code=422, detail="messages required")
        try:
            async with _httpx.AsyncClient(timeout=120.0) as client:
                if provider == "lmstudio":
                    resp = await client.post(
                        "http://127.0.0.1:1234/v1/chat/completions",
                        json={"model": model or "local-model", "messages": messages},
                    )
                    if resp.status_code != 200:
                        raise HTTPException(status_code=502, detail="LM Studio unreachable")
                    data = resp.json()
                    text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
                    return {"success": True, "provider": provider, "model": model, "text": text}
                resp = await client.post(
                    "http://127.0.0.1:11434/api/chat",
                    json={"model": model or "qwen3:8b", "messages": messages, "stream": False},
                )
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=502,
                        detail="Ollama unreachable - start Ollama or pick LM Studio in Settings",
                    )
                data = resp.json()
                text = data.get("message", {}).get("content", "")
                return {"success": True, "provider": provider, "model": model, "text": text}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"LLM provider error: {exc}") from exc

    @app.post("/api/llm/chat/stream")
    async def api_llm_chat_stream(request: Request) -> StreamingResponse:
        """Streaming backend chat proxy (SSE, OpenAI-style chunks)."""
        import httpx as _httpx

        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        provider = str(body.get("provider") or "ollama")
        model = str(body.get("model") or "")
        messages = body.get("messages") or []

        async def event_stream():
            try:
                async with _httpx.AsyncClient(timeout=120.0) as client:
                    if provider == "lmstudio":
                        async with client.stream(
                            "POST",
                            "http://127.0.0.1:1234/v1/chat/completions",
                            json={
                                "model": model or "local-model",
                                "messages": messages,
                                "stream": True,
                            },
                        ) as resp:
                            async for line in resp.aiter_lines():
                                if line.startswith("data:"):
                                    yield line + "\n\n"
                    else:
                        async with client.stream(
                            "POST",
                            "http://127.0.0.1:11434/api/chat",
                            json={
                                "model": model or "qwen3:8b",
                                "messages": messages,
                                "stream": True,
                            },
                        ) as resp:
                            async for line in resp.aiter_lines():
                                if not line.strip():
                                    continue
                                try:
                                    chunk = json.loads(line)
                                except Exception:
                                    chunk = None
                                if chunk is None:
                                    continue
                                text = chunk.get("message", {}).get("content", "")
                                done = chunk.get("done", False)
                                yield f"data: {json.dumps({'text': text, 'done': done})}\n\n"
                                if done:
                                    break
            except Exception as exc:
                yield f"data: {json.dumps({'error': str(exc)})}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.get("/api/v1/diagnostics")
    async def api_diagnostics() -> dict:
        """Full diagnostics for CUA-NSIS smoke testing: tools, system, errors."""
        import platform as _platform
        import sys as _sys

        tools: list[dict[str, str]] = []
        for name in sorted(all_tools.keys()):
            fn = all_tools[name]
            doc = (fn.__doc__ or "").strip().splitlines()
            tools.append({"name": name, "summary": doc[0] if doc else ""})
        return {
            "server": "vla-mcp",
            "version": mcp.version,
            "python": _sys.version.split()[0],
            "platform": _platform.platform(),
            "uptime_s": round(time.time() - _START, 1),
            "tool_count": len(tools),
            "tools": tools,
            "ports": {"backend": get_config().api_port, "frontend": get_config().frontend_port},
        }
