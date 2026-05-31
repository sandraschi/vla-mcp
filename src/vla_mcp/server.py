"""VLA-MCP - FastMCP 3.2 bridge for Vision-Language-Action stacks."""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Literal

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import Context, FastMCP

from . import __version__
from .config import get_config
from .engine.dataset_store import DatasetStore
from .engine.dmuon_runner import DMuonRunner
from .engine.event_segmenter import EventSegmenter
from .engine.fleet_bridge import FleetBridge
from .engine.hf_weights import HFWeightManager
from .engine.wall_runner import WallRunner
from .engine.world_model_runner import WorldModelRunner
from .prompts_resources import register_prompts_and_resources
from .tools.prefab import register_prefab_tools
from .web import setup_webapp

if os.name == "nt":
    try:
        import msvcrt

        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    except (ImportError, OSError, AttributeError):
        pass

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

INSTRUCTIONS = (
    "You are VLA-MCP (FastMCP 3.2): bridge to X Square wall-x (Wall-OSS-0.5 VLA, WALL-WM on Wan, "
    "DMuon co-training). Orchestrate worldlabs-mcp, robotics-mcp, avatarops for event-joint data. "
    "Use vla_status first; vla_weights to pull HF checkpoints; vla_dataset segment_telemetry for "
    "event joints; vla_training launch_co_train requires confirm=True."
)

_READ_ONLY = {"readOnlyHint": True}
_ALL_TOOLS: dict[str, Callable[..., Awaitable[Any]]] = {}


def _mount_fleet_proxies(mcp: FastMCP) -> list[str]:
    from fastmcp.server import create_proxy

    mounted: list[str] = []
    cfg = get_config()
    raw = cfg.mcp_bridge_urls or os.getenv("VLA_MCP_BRIDGE_URLS", "")
    if not raw:
        peers = FleetBridge.default().peer_urls()
        raw = ",".join(u for u in peers.values() if u)
    for url in raw.split(","):
        url = url.strip()
        if not url:
            continue
        mcp_url = url if url.endswith("/mcp") else url.rstrip("/") + "/mcp"
        try:
            mcp.add_provider(create_proxy(mcp_url))
            mounted.append(mcp_url)
        except Exception as exc:
            logger.warning("fleet_proxy_skipped", url=mcp_url, error=str(exc))
    return mounted


def _add_skills_provider(mcp: FastMCP) -> None:
    try:
        from fastmcp.server.providers.skills import SkillsDirectoryProvider
    except ImportError:
        return
    roots = Path(__file__).resolve().parent / "skills"
    if not roots.is_dir():
        return
    try:
        mcp.add_provider(SkillsDirectoryProvider(roots=roots))
    except Exception as exc:
        logger.warning("skills_provider_skipped", error=str(exc))


def build_mcp() -> FastMCP:
    mcp = FastMCP(
        "vla-mcp",
        version=__version__,
        instructions=INSTRUCTIONS,
    )
    _mount_fleet_proxies(mcp)

    @mcp.tool(annotations=_READ_ONLY)
    async def vla_status() -> dict[str, Any]:
        """VLA_STATUS - Snapshot of Wall-OSS, WALL-WM, DMuon, HF cache, and dataset."""
        cfg = get_config()
        store = DatasetStore.default()
        ep = store.list_episodes(limit=1)
        hf = HFWeightManager.default().list_models()
        return {
            "success": True,
            "wall": WallRunner.default().health(),
            "world_model": WorldModelRunner.default().health(),
            "dmuon": DMuonRunner.default().health(),
            "weights": hf,
            "dataset_root": cfg.dataset_root,
            "dataset_episodes": ep.get("total", 0),
            "device": cfg.device,
            "phase": "0.2.0",
            "message": "VLA stack status.",
        }

    @mcp.tool()
    async def vla_weights(
        operation: Literal["list_models", "local_status", "download"],
        model_key: str | None = None,
        revision: str | None = None,
    ) -> dict[str, Any]:
        """VLA_WEIGHTS - Hugging Face checkpoint download for Wall-OSS and WALL-WM.

        Args:
            operation: list_models, local_status, or download
            model_key: wall-oss-0.5 or wall-wm (required for download/local_status)
            revision: Optional HF git revision

        Returns:
            Structured dict with paths and download status.
        """
        mgr = HFWeightManager.default()
        if operation == "list_models":
            return mgr.list_models()
        if operation == "local_status":
            return mgr.local_status(model_key)
        if operation == "download":
            if not model_key:
                return {"success": False, "error": "model_key required for download"}
            return mgr.download(model_key, revision=revision)
        return {
            "success": False,
            "error": f"Unknown operation: {operation}",
            "recovery_options": ["list_models", "local_status", "download"],
        }

    @mcp.tool()
    async def vla_wall(
        operation: Literal["health", "infer_prepare", "finetune_prepare", "list_tasks"],
        task_hint: str | None = None,
        recipe: str | None = None,
    ) -> dict[str, Any]:
        """VLA_WALL - Portmanteau for Wall-OSS-0.5 VLA (gradient-bridged MoT + flow matching)."""
        runner = WallRunner.default()
        if operation == "health":
            return {"success": True, "result": runner.health(), "message": "Wall-OSS-0.5 status."}
        if operation == "infer_prepare":
            return runner.infer_prepare(task_hint=task_hint)
        if operation == "finetune_prepare":
            return runner.finetune_prepare(recipe=recipe)
        if operation == "list_tasks":
            return runner.list_tasks()
        return {"success": False, "error": f"Unknown operation: {operation}"}

    @mcp.tool()
    async def vla_world_model(
        operation: Literal["health", "train_prepare", "predict_prepare", "event_vocab"],
        notes: str | None = None,
        horizon_steps: int = 16,
    ) -> dict[str, Any]:
        """VLA_WORLD_MODEL - WALL-WM world action model (event joints, Wan prior)."""
        runner = WorldModelRunner.default()
        if operation == "health":
            return {"success": True, "result": runner.health(), "message": "WALL-WM status."}
        if operation == "train_prepare":
            return runner.train_prepare(notes=notes)
        if operation == "predict_prepare":
            return runner.predict_prepare(horizon_steps=horizon_steps)
        if operation == "event_vocab":
            return runner.event_vocab()
        return {"success": False, "error": f"Unknown operation: {operation}"}

    @mcp.tool()
    async def vla_dataset(
        operation: Literal[
            "ingest_episode",
            "list_episodes",
            "export_shard",
            "export_numpy_shard",
            "validate_multiview",
            "segment_telemetry",
        ],
        source: str | None = None,
        events: list[str] | None = None,
        video_paths: list[str] | None = None,
        action_path: str | None = None,
        metadata: dict[str, Any] | None = None,
        telemetry: list[dict[str, Any]] | None = None,
        limit: int = 50,
        offset: int = 0,
        shard_name: str | None = None,
        episode_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """VLA_DATASET - Event-grounded trajectory registry and numpy export for DMuon."""
        store = DatasetStore.default()
        if operation == "ingest_episode":
            if not source or not events:
                return {"success": False, "error": "source and events required", "error_type": "validation"}
            return store.ingest_episode(
                source=source,
                events=events,
                video_paths=video_paths,
                action_path=action_path,
                metadata=metadata,
            )
        if operation == "segment_telemetry":
            if not source or not telemetry:
                return {"success": False, "error": "source and telemetry required", "error_type": "validation"}
            return store.segment_and_ingest(
                source=source,
                telemetry=telemetry,
                video_paths=video_paths,
                action_path=action_path,
                metadata=metadata,
            )
        if operation == "list_episodes":
            return store.list_episodes(limit=limit, offset=offset)
        if operation == "export_shard":
            if not shard_name:
                return {"success": False, "error": "shard_name required", "error_type": "validation"}
            return store.export_shard(shard_name=shard_name, episode_ids=episode_ids)
        if operation == "export_numpy_shard":
            if not shard_name:
                return {"success": False, "error": "shard_name required", "error_type": "validation"}
            return store.export_numpy_shard(shard_name=shard_name, episode_ids=episode_ids)
        if operation == "validate_multiview":
            paths = video_paths or []
            if not paths:
                return {"success": False, "error": "video_paths required", "error_type": "validation"}
            return store.validate_multiview(video_paths=paths)
        return {"success": False, "error": f"Unknown operation: {operation}"}

    @mcp.tool()
    async def vla_events(
        operation: Literal["segment", "vocab"],
        samples: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """VLA_EVENTS - Event-joint segmentation (WALL-WM style, not equilong chunks).

        Args:
            operation: segment or vocab
            samples: Telemetry rows for segment (timestamp, velocity, contact_force, ...)

        Returns:
            segments, events chain, or vocabulary list.
        """
        seg = EventSegmenter()
        if operation == "vocab":
            return seg.vocab()
        if operation == "segment":
            if not samples:
                return {"success": False, "error": "samples required", "error_type": "validation"}
            return seg.segment(samples)
        return {"success": False, "error": f"Unknown operation: {operation}"}

    @mcp.tool()
    async def vla_training(
        operation: Literal[
            "health",
            "co_train_prepare",
            "config_template",
            "launch_co_train",
            "job_status",
            "stop_job",
        ],
        dataset_shard: str | None = None,
        confirm: bool = False,
        dry_run: bool = False,
        job_id: str | None = None,
        extra_args: list[str] | None = None,
    ) -> dict[str, Any]:
        """VLA_TRAINING - DMuon co-training launch and job tracking.

        Args:
            operation: health, co_train_prepare, config_template, launch_co_train, job_status, stop_job
            dataset_shard: Export shard name for training
            confirm: Must be True to start GPU subprocess (launch_co_train)
            dry_run: Preview command without launching
            job_id: Job id for job_status / stop_job
            extra_args: Extra CLI args forwarded to upstream train script

        Returns:
            Job ids, log paths, or training prep fields.
        """
        runner = DMuonRunner.default()
        if operation == "health":
            return {"success": True, "result": runner.health(), "message": "DMuon status."}
        if operation == "co_train_prepare":
            return runner.co_train_prepare(dataset_shard=dataset_shard)
        if operation == "config_template":
            return runner.config_template()
        if operation == "launch_co_train":
            return await runner.launch_co_train(
                confirm=confirm,
                dataset_shard=dataset_shard,
                extra_args=extra_args,
                dry_run=dry_run,
            )
        if operation == "job_status":
            return runner.job_status(job_id=job_id)
        if operation == "stop_job":
            if not job_id:
                return {"success": False, "error": "job_id required for stop_job"}
            return runner.stop_job(job_id)
        return {"success": False, "error": f"Unknown operation: {operation}"}

    @mcp.tool(annotations=_READ_ONLY)
    async def vla_fleet(
        operation: Literal["bridge_status", "scenario_brief", "list_peers", "call_peer"],
        room_style: str = "cluttered_indoor",
        include_failures: bool = True,
        agents: list[str] | None = None,
        peer: str | None = None,
        tool_name: str | None = None,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """VLA_FLEET - Simulation peers and REST tool bridge."""
        bridge = FleetBridge.default()
        if operation == "list_peers":
            return {"success": True, "peers": bridge.peer_urls()}
        if operation == "bridge_status":
            return await bridge.bridge_status()
        if operation == "scenario_brief":
            return bridge.scenario_brief(
                room_style=room_style,
                include_failures=include_failures,
                agents=agents,
            )
        if operation == "call_peer":
            if not peer or not tool_name:
                return {"success": False, "error": "peer and tool_name required for call_peer"}
            return await bridge.call_peer(peer, tool_name, arguments)
        return {"success": False, "error": f"Unknown operation: {operation}"}

    @mcp.tool()
    async def vla_agentic_workflow(
        ctx: Context,
        goal: str,
        max_steps: int = 10,
    ) -> dict[str, Any]:
        """VLA_AGENTIC_WORKFLOW - Multi-step VLA + world-model session planning."""
        fallback_steps = [
            "vla_weights(operation='list_models')",
            "vla_fleet(operation='scenario_brief', include_failures=True)",
            "vla_fleet(operation='call_peer', peer='robotics', tool_name='...')",
            "vla_dataset(operation='segment_telemetry', ...)",
            "vla_dataset(operation='export_numpy_shard', shard_name='train_001')",
            "vla_training(operation='launch_co_train', confirm=True)",
        ]
        sample_ok = hasattr(ctx, "sample")
        plan: str | None = None
        if sample_ok:
            try:
                prompt = (
                    f"Goal: {goal}\nNumbered plan (max {max_steps} steps) using vla_* tools. "
                    "Include event-joint data and DMuon. No markdown fences."
                )
                out = await ctx.sample(prompt)  # type: ignore[misc]
                plan = getattr(out, "text", None) or str(out)
            except Exception as exc:
                logger.warning("agentic_sample_failed", error=str(exc))
        return {
            "success": True,
            "goal": goal,
            "sampling_available": bool(sample_ok),
            "plan": plan,
            "fallback_steps": fallback_steps,
            "message": plan or "Use fallback_steps when sampling unavailable.",
        }

    register_prompts_and_resources(mcp)
    register_prefab_tools(mcp)
    _add_skills_provider(mcp)

    _ALL_TOOLS.clear()
    _ALL_TOOLS.update(
        {
            "vla_status": vla_status,
            "vla_weights": vla_weights,
            "vla_wall": vla_wall,
            "vla_world_model": vla_world_model,
            "vla_dataset": vla_dataset,
            "vla_events": vla_events,
            "vla_training": vla_training,
            "vla_fleet": vla_fleet,
            "vla_agentic_workflow": vla_agentic_workflow,
        }
    )
    return mcp


mcp = build_mcp()
_mcp_http = mcp.http_app(path="/")
app = FastAPI(title="VLA-MCP", lifespan=_mcp_http.lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
setup_webapp(app, mcp, _ALL_TOOLS)
app.mount("/mcp", _mcp_http)


def main() -> None:
    from .transport import run_server

    run_server(mcp, server_name="vla-mcp")


if __name__ == "__main__":
    main()
