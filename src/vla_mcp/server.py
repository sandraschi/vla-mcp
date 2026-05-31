"""VLA-MCP - FastMCP 3.2 bridge for Vision-Language-Action stacks."""

from __future__ import annotations

import logging
import os
import sys
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
from .engine.fleet_bridge import FleetBridge
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
    "You are VLA-MCP (FastMCP 3.2): bridge to X Square Wall-OSS-0.5 (VLA), WALL-WM (world "
    "action model on Wan), and DMuon co-training. Orchestrate worldlabs-mcp, robotics-mcp, "
    "and avatarops for event-grounded simulation data. Use vla_status first; vla_agentic_workflow "
    "for multi-step loops. Set VLA_WALL_X_ROOT to a clone of github.com/X-Square-Robot/wall-x."
)

_READ_ONLY = {"readOnlyHint": True}


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

    @mcp.tool(annotations=_READ_ONLY)
    async def vla_status() -> dict[str, Any]:
        """VLA_STATUS - Snapshot of Wall-OSS, WALL-WM, DMuon, and dataset configuration.

        Returns:
            success, wall, world_model, dmuon, dataset_root, device, and message fields.
        """
        cfg = get_config()
        store = DatasetStore.default()
        ep = store.list_episodes(limit=1)
        return {
            "success": True,
            "wall": WallRunner.default().health(),
            "world_model": WorldModelRunner.default().health(),
            "dmuon": DMuonRunner.default().health(),
            "dataset_root": cfg.dataset_root,
            "dataset_episodes": ep.get("total", 0),
            "device": cfg.device,
            "message": "VLA stack status (upstream paths must be set for GPU jobs).",
        }

    @mcp.tool()
    async def vla_wall(
        operation: Literal["health", "infer_prepare", "finetune_prepare", "list_tasks"],
        task_hint: str | None = None,
        recipe: str | None = None,
    ) -> dict[str, Any]:
        """VLA_WALL - Portmanteau for Wall-OSS-0.5 VLA execution engine.

        [RATIONALE] Consolidates Wall-OSS lifecycle ops without separate tools per stage.

        Args:
            operation: health, infer_prepare, finetune_prepare, or list_tasks
            task_hint: Optional task name for infer_prepare
            recipe: Optional co-training recipe name for finetune_prepare

        Returns:
            Structured dict with success, message, and operation-specific fields.
        """
        runner = WallRunner.default()
        if operation == "health":
            return {"success": True, "result": runner.health(), "message": "Wall-OSS-0.5 status."}
        if operation == "infer_prepare":
            return runner.infer_prepare(task_hint=task_hint)
        if operation == "finetune_prepare":
            return runner.finetune_prepare(recipe=recipe)
        if operation == "list_tasks":
            return runner.list_tasks()
        return {
            "success": False,
            "error": f"Unknown operation: {operation}",
            "recovery_options": ["health", "infer_prepare", "finetune_prepare", "list_tasks"],
        }

    @mcp.tool()
    async def vla_world_model(
        operation: Literal["health", "train_prepare", "predict_prepare", "event_vocab"],
        notes: str | None = None,
        horizon_steps: int = 16,
    ) -> dict[str, Any]:
        """VLA_WORLD_MODEL - Portmanteau for WALL-WM world action model.

        [RATIONALE] Event-grounded world model ops share one upstream repo and GPU lock.

        Args:
            operation: health, train_prepare, predict_prepare, or event_vocab
            notes: Optional training notes for train_prepare
            horizon_steps: Rollout horizon for predict_prepare (default 16)

        Returns:
            Structured dict with success, message, and upstream hints.
        """
        runner = WorldModelRunner.default()
        if operation == "health":
            return {"success": True, "result": runner.health(), "message": "WALL-WM status."}
        if operation == "train_prepare":
            return runner.train_prepare(notes=notes)
        if operation == "predict_prepare":
            return runner.predict_prepare(horizon_steps=horizon_steps)
        if operation == "event_vocab":
            return runner.event_vocab()
        return {
            "success": False,
            "error": f"Unknown operation: {operation}",
            "recovery_options": ["health", "train_prepare", "predict_prepare", "event_vocab"],
        }

    @mcp.tool()
    async def vla_dataset(
        operation: Literal[
            "ingest_episode",
            "list_episodes",
            "export_shard",
            "validate_multiview",
        ],
        source: str | None = None,
        events: list[str] | None = None,
        video_paths: list[str] | None = None,
        action_path: str | None = None,
        metadata: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
        shard_name: str | None = None,
        episode_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """VLA_DATASET - Event-grounded trajectory registry for co-training.

        Args:
            operation: ingest_episode, list_episodes, export_shard, validate_multiview
            source: Data source label (required for ingest_episode)
            events: Semantic event tags (required for ingest_episode)
            video_paths: Multiview video file paths
            action_path: Optional numpy/json action trajectory path
            metadata: Optional episode metadata dict
            limit: Page size for list_episodes (1-200, default 50)
            offset: Page offset for list_episodes
            shard_name: Export filename stem for export_shard
            episode_ids: Subset of episodes to export (default: all)

        Returns:
            Structured dict; list_episodes includes has_more for pagination.
        """
        store = DatasetStore.default()
        if operation == "ingest_episode":
            if not source or not events:
                return {
                    "success": False,
                    "error": "source and events are required for ingest_episode",
                    "error_type": "validation",
                }
            return store.ingest_episode(
                source=source,
                events=events,
                video_paths=video_paths,
                action_path=action_path,
                metadata=metadata,
            )
        if operation == "list_episodes":
            return store.list_episodes(limit=limit, offset=offset)
        if operation == "export_shard":
            if not shard_name:
                return {
                    "success": False,
                    "error": "shard_name is required for export_shard",
                    "error_type": "validation",
                }
            return store.export_shard(shard_name=shard_name, episode_ids=episode_ids)
        if operation == "validate_multiview":
            paths = video_paths or []
            if not paths:
                return {
                    "success": False,
                    "error": "video_paths required for validate_multiview",
                    "error_type": "validation",
                }
            return store.validate_multiview(video_paths=paths)
        return {
            "success": False,
            "error": f"Unknown operation: {operation}",
            "recovery_options": [
                "ingest_episode",
                "list_episodes",
                "export_shard",
                "validate_multiview",
            ],
        }

    @mcp.tool()
    async def vla_training(
        operation: Literal["health", "co_train_prepare", "config_template"],
        dataset_shard: str | None = None,
    ) -> dict[str, Any]:
        """VLA_TRAINING - DMuon optimizer and co-training prep for Wall-OSS + WALL-WM.

        Args:
            operation: health, co_train_prepare, or config_template
            dataset_shard: Optional export shard name for co_train_prepare

        Returns:
            Structured dict with upstream paths and training hints.
        """
        runner = DMuonRunner.default()
        if operation == "health":
            return {"success": True, "result": runner.health(), "message": "DMuon status."}
        if operation == "co_train_prepare":
            return runner.co_train_prepare(dataset_shard=dataset_shard)
        if operation == "config_template":
            return runner.config_template()
        return {
            "success": False,
            "error": f"Unknown operation: {operation}",
            "recovery_options": ["health", "co_train_prepare", "config_template"],
        }

    @mcp.tool(annotations=_READ_ONLY)
    async def vla_fleet(
        operation: Literal["bridge_status", "scenario_brief", "list_peers"],
        room_style: str = "cluttered_indoor",
        include_failures: bool = True,
        agents: list[str] | None = None,
    ) -> dict[str, Any]:
        """VLA_FLEET - Simulation boundary peers (worldlabs, robotics, avatar).

        Args:
            operation: bridge_status, scenario_brief, or list_peers
            room_style: Scenario style for scenario_brief
            include_failures: Include failure/recovery trajectories in brief
            agents: Agent types (default raspbot + vroid)

        Returns:
            Structured dict with peer URLs and orchestration steps.
        """
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
        return {
            "success": False,
            "error": f"Unknown operation: {operation}",
            "recovery_options": ["bridge_status", "scenario_brief", "list_peers"],
        }

    @mcp.tool()
    async def vla_agentic_workflow(
        ctx: Context,
        goal: str,
        max_steps: int = 10,
    ) -> dict[str, Any]:
        """VLA_AGENTIC_WORKFLOW - Multi-step VLA + world-model session planning (SEP-1577).

        Args:
            goal: Natural-language goal for the closed-loop VLA session
            max_steps: Soft cap for suggested steps (informational)

        Returns:
            plan, fallback_steps, sampling_available, and message fields.
        """
        fallback_steps = [
            "vla_status()",
            "vla_fleet(operation='scenario_brief', include_failures=True)",
            "Run worldlabs-mcp + robotics-mcp + avatarops simulations",
            "vla_dataset(operation='ingest_episode', ...) for each trajectory",
            "vla_dataset(operation='export_shard', shard_name='train_001')",
            "vla_training(operation='co_train_prepare')",
            "vla_wall(operation='infer_prepare') on edge hardware",
        ]
        sample_ok = hasattr(ctx, "sample")
        plan: str | None = None
        if sample_ok:
            try:
                prompt = (
                    f"Goal: {goal}\nProduce a numbered plan (max {max_steps} steps) using "
                    "vla_* MCP tools for Wall-OSS + WALL-WM co-training. No markdown fences."
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
            "message": plan or "Use fallback_steps when sampling is unavailable.",
        }

    register_prompts_and_resources(mcp)
    register_prefab_tools(mcp)
    _add_skills_provider(mcp)
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
setup_webapp(app, mcp)
app.mount("/mcp", _mcp_http)


def main() -> None:
    from .transport import run_server

    run_server(mcp, server_name="vla-mcp")


if __name__ == "__main__":
    main()
