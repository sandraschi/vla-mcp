"""End-to-end fleet loop: worldlabs → yahboom → ingest → export → DMuon dry_run."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..config import VLAConfig, get_config
from .dataset_store import DatasetStore
from .dmuon_runner import DMuonRunner
from .fleet_bridge import FleetBridge


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
            "pipeline": "worldlabs → yahboom → ingest → export_numpy → dmuon_dry_run",
            "modes": {
                "simulated": "Always runs; uses synthetic Raspbot telemetry (CI-safe).",
                "live": "Probes fleet peers; calls worldlabs health + yahboom IMU when reachable.",
            },
            "live_peer_tools": {
                "worldlabs-mcp": {"tool": "health", "arguments": {}},
                "yahboom-mcp": {
                    "tool": "yahboom_tool",
                    "arguments": {"operation": "read_imu"},
                },
            },
            "outputs": ["episode_id", "numpy_dir", "manifest_path", "dmuon_command", "provenance_path"],
            "message": "Use run(live=False) for CI; run(live=True) when fleet HTTP servers are up.",
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

    async def _live_fleet_steps(self, bridge: FleetBridge) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        step_log: list[dict[str, Any]] = []
        peer_data: dict[str, Any] = {}

        status = await bridge.bridge_status()
        step_log.append({"name": "fleet_probe", "success": status.get("success", False), "result": status})

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

        yb_health = await bridge.call_peer(
            "yahboom-mcp",
            "yahboom_tool",
            {"operation": "health_check"},
        )
        step_log.append(
            {
                "name": "yahboom_health",
                "success": yb_health.get("success", False),
                "skipped": not yb_health.get("success"),
                "result": yb_health,
            }
        )

        yb_imu = await bridge.call_peer(
            "yahboom-mcp",
            "yahboom_tool",
            {"operation": "read_imu"},
        )
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
    ) -> dict[str, Any]:
        run_id = uuid.uuid4().hex[:10]
        shard = shard_name or f"e2e_{run_id}"
        store = DatasetStore.default()
        bridge = FleetBridge.default()
        dmuon = DMuonRunner.default()
        steps: list[dict[str, Any]] = []
        mode = "simulated"
        peer_data: dict[str, Any] = {}

        if live:
            steps, peer_data = await self._live_fleet_steps(bridge)
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
            "shard_name": shard,
            "episode_id": ingest.get("episode_id"),
            "numpy_dir": export.get("numpy_dir"),
            "manifest_path": export.get("manifest_path"),
            "arrays_written": export.get("arrays_written"),
            "dmuon_command": dry.get("command"),
            "steps": steps,
            "finished_at": datetime.now(UTC).isoformat(),
            "message": (
                "End-to-end loop completed (simulated telemetry + real export + DMuon dry_run)."
                if mode != "live"
                else "Live fleet probes + ingest + export + DMuon dry_run completed."
            ),
        }
        provenance_path = self._write_provenance(run_id, payload)
        payload["provenance_path"] = provenance_path
        self._last_run = payload
        return payload
