"""End-to-end fleet loop: worldlabs → yahboom → ingest → export → DMuon dry_run."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from ..config import VLAConfig, get_config
from .dataset_store import DatasetStore
from .dmuon_runner import DMuonRunner
from .fleet_bridge import FleetBridge

BoomyDemo = Literal["none", "draw", "talkbot"]


def _synthetic_telemetry(*, include_failures: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {"timestamp": 0.0, "velocity": 0.12, "distance_to_target": 1.4, "gripper_open": True},
        {"timestamp": 0.4, "velocity": 0.55, "distance_to_target": 0.55, "gripper_open": True},
        {"timestamp": 0.8, "velocity": 0.25, "distance_to_target": 0.22, "contact_force": 0.42},
        {"timestamp": 1.1, "velocity": 0.08, "contact_force": 0.78, "gripper_open": False},
        {"timestamp": 1.5, "velocity": 0.15, "contact_force": 0.65},
    ]
    if include_failures:
        rows.extend(
            [
                {"timestamp": 1.9, "velocity": 0.4, "slip_variance": 0.35, "contact_force": 0.5},
                {"timestamp": 2.2, "collision_flag": True, "velocity": 0.0},
                {"timestamp": 2.6, "velocity": 0.1, "slip_variance": 0.2, "contact_force": 0.3},
            ]
        )
    else:
        rows.append({"timestamp": 1.9, "velocity": 0.05, "contact_force": 0.2, "gripper_open": True})
    return rows


def _actions_from_telemetry(samples: list[dict[str, Any]]) -> list[list[float]]:
    actions: list[list[float]] = []
    for row in samples:
        actions.append(
            [
                float(row.get("velocity", 0.0) or 0.0),
                float(row.get("contact_force", 0.0) or 0.0),
                float(row.get("distance_to_target", 0.0) or 0.0),
                1.0 if row.get("gripper_open") else 0.0,
            ]
        )
    return actions


def _telemetry_from_boomy_demo(
    demo: str,
    demo_result: dict[str, Any],
    *,
    include_failures: bool,
) -> list[dict[str, Any]]:
    """Derive episode rows from Boomy demo status/transcript when live."""
    final = demo_result.get("final") or {}
    status = final.get("result") if isinstance(final.get("result"), dict) else final
    rows: list[dict[str, Any]] = []

    if demo == "talkbot":
        rows.append(
            {
                "timestamp": 0.0,
                "velocity": 0.14,
                "distance_to_target": 1.1,
                "event": "approaching",
            }
        )
        transcript = status.get("transcript") or []
        for i, turn in enumerate(transcript):
            rows.append(
                {
                    "timestamp": 0.6 + i * 0.9,
                    "velocity": 0.0,
                    "contact_force": 0.1,
                    "event": "dialogue",
                    "speaker": turn.get("role", "unknown"),
                    "utterance": turn.get("text", ""),
                }
            )
        if not transcript:
            rows.append(
                {
                    "timestamp": 0.8,
                    "velocity": 0.0,
                    "event": "dialogue",
                    "utterance": "Hi, I am Boomy. Who are you?",
                }
            )

    elif demo == "draw":
        rows.append(
            {
                "timestamp": 0.0,
                "velocity": 0.06,
                "contact_force": 0.35,
                "event": "making_contact",
            }
        )
        logs = status.get("logs") or []
        for i, line in enumerate(logs[:12]):
            rows.append(
                {
                    "timestamp": 0.2 + i * 0.25,
                    "velocity": 0.05,
                    "contact_force": 0.5,
                    "event": "drawing",
                    "log": line,
                }
            )
        if len(rows) == 1:
            rows.append({"timestamp": 0.5, "velocity": 0.04, "contact_force": 0.55, "event": "drawing"})

    if not rows:
        return _synthetic_telemetry(include_failures=include_failures)

    if include_failures:
        rows.append(
            {
                "timestamp": rows[-1]["timestamp"] + 0.4,
                "velocity": 0.02,
                "slip_variance": 0.12,
                "contact_force": 0.28,
                "event": "recovery",
            }
        )
    return rows


@dataclass
class PipelineRunner:
    """Orchestrates the closed-loop VLA data path with simulated or live fleet steps."""

    config: VLAConfig
    _last_run: dict[str, Any] = field(default_factory=dict, init=False)

    @classmethod
    def default(cls) -> PipelineRunner:
        return cls(config=get_config())

    def describe(self) -> dict[str, Any]:
        return {
            "success": True,
            "pipeline": "worldlabs → yahboom (Boomy demo) → ingest → export_numpy → dmuon_dry_run",
            "modes": {
                "simulated": "Always runs; uses synthetic Raspbot telemetry (CI-safe).",
                "live": (
                    "Probes fleet peers; optional worldlabs generate; runs Boomy draw/talkbot "
                    "when boomy_demo is set; reads yahboom IMU via /api/v1/control/tool."
                ),
            },
            "live_peer_tools": {
                "worldlabs-mcp": {"tool": "health", "arguments": {}},
                "yahboom-mcp": {
                    "yahboom_tool": {"operation": "read_imu"},
                    "yahboom_demo": {"operation": "talkbot|draw", "rest": "/api/v1/demo/*"},
                    "control_tool": "/api/v1/control/tool",
                },
            },
            "boomy_demo_options": ["none", "draw", "talkbot"],
            "env": {
                "VLA_PIPELINE_BOOMY_DEMO": self.config.pipeline_boomy_demo or "(unset)",
                "VLA_PIPELINE_GENERATE_WORLD": self.config.pipeline_generate_world,
            },
            "outputs": ["episode_id", "numpy_dir", "manifest_path", "dmuon_command", "provenance_path"],
            "message": "Use run(live=False) for CI; run(live=True, boomy_demo='talkbot') on the show floor.",
        }

    def last_run(self) -> dict[str, Any]:
        if self._last_run:
            return {"success": True, "run": self._last_run}
        provenance = self._load_latest_provenance()
        if provenance:
            return {"success": True, "run": provenance}
        return {"success": False, "error": "No pipeline run recorded yet"}

    def _provenance_dir(self) -> Path:
        p = Path(self.config.dataset_root).expanduser().resolve() / "logs" / "pipeline"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _load_latest_provenance(self) -> dict[str, Any] | None:
        folder = self._provenance_dir()
        files = sorted(folder.glob("run_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files:
            return None
        return json.loads(files[0].read_text(encoding="utf-8"))

    def _write_provenance(self, run_id: str, payload: dict[str, Any]) -> str:
        path = self._provenance_dir() / f"run_{run_id}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(path)

    def _resolve_boomy_demo(self, boomy_demo: str | None) -> str | None:
        raw = (boomy_demo or self.config.pipeline_boomy_demo or "none").strip().lower()
        if raw in ("", "none", "off", "false", "0"):
            return None
        if raw in ("draw", "talkbot"):
            return raw
        return None

    async def _run_boomy_demo(
        self,
        bridge: FleetBridge,
        demo: str,
        *,
        pattern: str,
    ) -> dict[str, Any]:
        fast = os.getenv("YAHBOOM_DEMO_FAST", "0") == "1"
        if demo == "talkbot":
            start = await bridge.yahboom_run_demo(
                "talkbot",
                approach=not fast,
                max_turns=1 if fast else 2,
                use_speech_mcp=True,
                scripted_user_lines=["Hi Boomy, I am Alex."],
            )
        else:
            start = await bridge.yahboom_run_demo(
                "draw",
                pattern=pattern,
                skip_color_swap_pause=pattern != "smiley" or fast,
            )
        if not start.get("success"):
            return {"success": False, "demo": demo, "start": start}

        timeout = 30.0 if fast else 600.0
        polled = await bridge.poll_yahboom_demo(demo, timeout_s=timeout, poll_s=0.5 if fast else 1.0)
        return {
            "success": polled.get("success", False),
            "demo": demo,
            "pattern": pattern if demo == "draw" else None,
            "start": start.get("result"),
            "final": polled.get("result"),
            "error": polled.get("error"),
        }

    async def _live_fleet_steps(
        self,
        bridge: FleetBridge,
        *,
        boomy_demo: str | None,
        boomy_pattern: str,
        generate_world: bool,
        room_style: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        step_log: list[dict[str, Any]] = []
        peer_data: dict[str, Any] = {}

        status = await bridge.bridge_status()
        step_log.append({"name": "fleet_probe", "success": status.get("success", False), "result": status})

        if generate_world:
            prompt = f"Small {room_style.replace('_', ' ')} demo booth for a mobile robot"
            wl_gen = await bridge.generate_world(prompt)
            step_log.append(
                {
                    "name": "worldlabs_generate",
                    "success": wl_gen.get("success", False),
                    "skipped": not wl_gen.get("success"),
                    "result": wl_gen,
                }
            )
            if wl_gen.get("success"):
                peer_data["worldlabs_generate"] = wl_gen

        wl = await bridge.call_peer("worldlabs-mcp", "health", {})
        step_log.append(
            {
                "name": "worldlabs_health",
                "success": wl.get("success", False),
                "skipped": not wl.get("success"),
                "result": wl,
            }
        )
        if wl.get("success"):
            peer_data["worldlabs"] = wl.get("result")

        yb_health = await bridge.yahboom_tool("health_check")
        step_log.append(
            {
                "name": "yahboom_health",
                "success": yb_health.get("success", False),
                "skipped": not yb_health.get("success"),
                "result": yb_health,
            }
        )

        if boomy_demo:
            demo_out = await self._run_boomy_demo(bridge, boomy_demo, pattern=boomy_pattern)
            step_log.append(
                {
                    "name": f"boomy_{boomy_demo}",
                    "success": demo_out.get("success", False),
                    "skipped": not demo_out.get("success"),
                    "result": demo_out,
                }
            )
            if demo_out.get("success"):
                peer_data["boomy_demo"] = demo_out

        yb_imu = await bridge.yahboom_tool("read_imu")
        step_log.append(
            {
                "name": "yahboom_imu",
                "success": yb_imu.get("success", False),
                "skipped": not yb_imu.get("success"),
                "result": yb_imu,
            }
        )
        if yb_imu.get("success"):
            peer_data["yahboom_imu"] = yb_imu.get("result")
        elif yb_health.get("success"):
            peer_data["yahboom_health"] = yb_health.get("result")

        reachable = [p for p in status.get("peers", []) if p.get("reachable")]
        peer_data["reachable_count"] = len(reachable)
        return step_log, peer_data

    async def run(
        self,
        *,
        live: bool = False,
        shard_name: str | None = None,
        include_failures: bool = True,
        room_style: str = "cluttered_indoor",
        fallback_simulate: bool = True,
        boomy_demo: str | None = None,
        boomy_pattern: str = "boomy_b",
        generate_world: bool | None = None,
    ) -> dict[str, Any]:
        run_id = uuid.uuid4().hex[:10]
        shard = shard_name or f"e2e_{run_id}"
        store = DatasetStore.default()
        bridge = FleetBridge.default()
        dmuon = DMuonRunner.default()
        steps: list[dict[str, Any]] = []
        mode = "simulated"
        peer_data: dict[str, Any] = {}
        resolved_demo = self._resolve_boomy_demo(boomy_demo) if live else None
        do_generate = (
            self.config.pipeline_generate_world if generate_world is None else generate_world
        )

        if live:
            steps, peer_data = await self._live_fleet_steps(
                bridge,
                boomy_demo=resolved_demo,
                boomy_pattern=boomy_pattern,
                generate_world=do_generate,
                room_style=room_style,
            )
            reachable = int(peer_data.get("reachable_count", 0))
            if reachable == 0:
                if not fallback_simulate:
                    payload = {
                        "success": False,
                        "run_id": run_id,
                        "mode": "live",
                        "steps": steps,
                        "error": "No fleet peers reachable",
                        "recovery_options": [
                            "Start worldlabs-mcp and yahboom-mcp HTTP servers",
                            "Run with live=False for simulated loop",
                            "Set fallback_simulate=True",
                        ],
                    }
                    self._write_provenance(run_id, payload)
                    return payload
                mode = "live_partial"
            else:
                mode = "live"

        if peer_data.get("boomy_demo"):
            telemetry = _telemetry_from_boomy_demo(
                str(peer_data["boomy_demo"].get("demo", "talkbot")),
                peer_data["boomy_demo"],
                include_failures=include_failures,
            )
        else:
            telemetry = _synthetic_telemetry(include_failures=include_failures)

        if peer_data.get("yahboom_imu"):
            telemetry[0]["peer_imu"] = peer_data["yahboom_imu"]

        ingest = store.segment_and_ingest(
            source="live_raspbot" if live and mode == "live" else "sim_raspbot",
            telemetry=telemetry,
            actions=_actions_from_telemetry(telemetry),
            metadata={
                "room_style": room_style,
                "pipeline_run_id": run_id,
                "mode": mode,
                "boomy_demo": resolved_demo,
                "peer_data": peer_data,
            },
        )
        steps.append({"name": "ingest", "success": ingest.get("success", False), "result": ingest})
        if not ingest.get("success"):
            payload = {
                "success": False,
                "run_id": run_id,
                "mode": mode,
                "steps": steps,
                "error": ingest.get("error", "ingest failed"),
            }
            self._write_provenance(run_id, payload)
            return payload

        export = store.export_numpy_shard(shard_name=shard)
        steps.append({"name": "export_numpy", "success": export.get("success", False), "result": export})
        if not export.get("success"):
            payload = {
                "success": False,
                "run_id": run_id,
                "mode": mode,
                "steps": steps,
                "error": export.get("error", "export failed"),
            }
            self._write_provenance(run_id, payload)
            return payload

        dry = await dmuon.launch_co_train(dataset_shard=shard, dry_run=True)
        steps.append({"name": "dmuon_dry_run", "success": dry.get("success", False), "result": dry})

        payload = {
            "success": dry.get("success", False),
            "run_id": run_id,
            "mode": mode,
            "boomy_demo": resolved_demo,
            "shard_name": shard,
            "episode_id": ingest.get("episode_id"),
            "numpy_dir": export.get("numpy_dir"),
            "manifest_path": export.get("manifest_path"),
            "arrays_written": export.get("arrays_written"),
            "event_chain": ingest.get("events", []),
            "segments": ingest.get("segments", []),
            "event_duration": max(
                (float(r.get("timestamp", i)) for i, r in enumerate(telemetry)), default=0.0
            ),
            "dmuon_command": dry.get("command"),
            "steps": steps,
            "finished_at": datetime.now(UTC).isoformat(),
            "message": (
                "End-to-end loop completed (simulated telemetry + real export + DMuon dry_run)."
                if mode != "live"
                else (
                    f"Live fleet loop with Boomy {resolved_demo or 'probe-only'} "
                    "+ ingest + export + DMuon dry_run completed."
                )
            ),
        }
        provenance_path = self._write_provenance(run_id, payload)
        payload["provenance_path"] = provenance_path
        self._last_run = payload
        if payload.get("success"):
            try:
                from ..integrations.aiwatcher import push_pipeline_complete

                await push_pipeline_complete(payload, config=self.config)
            except Exception:
                pass
        return payload
