"""Bridge to DMuon distributed Muon optimizer (wall-x training stack)."""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import VLAConfig, get_config
from .job_registry import load_jobs, read_log_tail, upsert_job

DMUON_REPO = "https://github.com/X-Square-Robot/wall-x"

_jobs: dict[str, dict[str, Any]] = {}
_drain_tasks: dict[str, asyncio.Task] = {}
_registry_loaded = False


def _serialize_job(job: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in job.items() if k != "drain_task"}


def _ensure_registry(runner: DMuonRunner) -> None:
    global _registry_loaded
    if _registry_loaded:
        return
    disk = load_jobs(runner.config.dataset_root)
    for job_id, record in disk.items():
        if job_id not in _jobs:
            _jobs[job_id] = record
    _registry_loaded = True


def _persist_job(runner: DMuonRunner, job_id: str) -> None:
    upsert_job(runner.config.dataset_root, _jobs, job_id, _serialize_job(_jobs[job_id]))


@dataclass
class DMuonRunner:
    """Validates DMuon clone, launches co-training subprocesses, tracks jobs."""

    config: VLAConfig

    @classmethod
    def default(cls) -> DMuonRunner:
        runner = cls(config=get_config())
        _ensure_registry(runner)
        return runner

    def upstream_resolved(self) -> Path | None:
        root = self.config.dmuon_root or self.config.wall_x_root
        if not root:
            return None
        p = Path(root).expanduser().resolve()
        return p if p.is_dir() else None

    def health(self) -> dict:
        root = self.upstream_resolved()
        active = sum(1 for j in _jobs.values() if j.get("status") == "running")
        return {
            "optimizer": "DMuon",
            "upstream_configured": root is not None,
            "upstream_path": str(root) if root else None,
            "reference_repo": DMUON_REPO,
            "device": self.config.device,
            "vram_shards": self.config.dmuon_vram_shards,
            "active_jobs": active,
            "persisted_jobs": len(_jobs),
            "notes": "Matrix-sharded Muon (Newton-Schulz) for gradient-bridged co-training.",
        }

    def _discover_train_script(self, root: Path) -> Path | None:
        candidates = [
            root / "scripts" / "train_dmuon.py",
            root / "scripts" / "train.py",
            root / "train.py",
            root / "tools" / "train_dmuon.py",
        ]
        for c in candidates:
            if c.is_file():
                return c
        for hit in root.rglob("train*dmuon*.py"):
            if hit.is_file():
                return hit
        return None

    def introspect_train_args(self, script: Path | None = None) -> dict[str, Any]:
        root = self.upstream_resolved()
        if not root:
            return {"success": False, "error": "Upstream not configured"}
        path = script or self._discover_train_script(root)
        if not path or not path.is_file():
            return {"success": False, "error": "No train script found"}
        try:
            proc = subprocess.run(
                [sys.executable, str(path), "--help"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            return {"success": False, "error": str(exc), "script": str(path)}
        text = (proc.stdout or "") + "\n" + (proc.stderr or "")
        flags = sorted(set(re.findall(r"(--[\w-]+)", text)))
        return {
            "success": True,
            "script": str(path),
            "exit_code": proc.returncode,
            "flags": flags,
            "help_excerpt": text[:2000],
        }

    def _build_train_cmd(
        self,
        script: Path,
        *,
        dataset_shard: str | None,
        extra_args: list[str] | None,
    ) -> tuple[list[str], dict[str, Any]]:
        intro = self.introspect_train_args(script)
        flags = set(intro.get("flags") or [])
        cmd = [sys.executable, str(script)]
        mapping = [
            ("--dataset-root", self.config.dataset_root),
            ("--device", self.config.device),
            ("--dmuon-shards", str(self.config.dmuon_vram_shards)),
        ]
        applied: list[str] = []
        for flag, value in mapping:
            if not flags or flag in flags:
                cmd.extend([flag, value])
                applied.append(flag)
        if dataset_shard and (not flags or "--shard" in flags):
            cmd.extend(["--shard", dataset_shard])
            applied.append("--shard")
        if extra_args:
            cmd.extend(extra_args)
        return cmd, {"introspected": intro.get("success"), "applied_flags": applied, "known_flags": list(flags)}

    def co_train_prepare(self, *, dataset_shard: str | None = None) -> dict:
        root = self.upstream_resolved()
        if not root:
            return {
                "success": False,
                "error": "VLA_DMUON_ROOT or VLA_WALL_X_ROOT not configured",
                "recovery_options": [f"Clone {DMUON_REPO}", "Export shards via vla_dataset"],
            }
        script = self._discover_train_script(root)
        export_path = None
        if dataset_shard:
            export_path = Path(self.config.dataset_root) / "exports" / f"{dataset_shard}.json"
        arg_info = self.introspect_train_args(script) if script else {"success": False}
        return {
            "success": True,
            "message": "DMuon co-training ready. Use launch_co_train with confirm=True to start GPU job.",
            "upstream": str(root),
            "train_script": str(script) if script else None,
            "train_args": arg_info,
            "dataset_shard": dataset_shard,
            "dataset_export": str(export_path) if export_path else None,
            "dataset_root": self.config.dataset_root,
            "vram_shards": self.config.dmuon_vram_shards,
        }

    def config_template(self) -> dict:
        return {
            "success": True,
            "template": {
                "wall_x_root": self.config.wall_x_root or "${VLA_WALL_X_ROOT}",
                "dataset_root": self.config.dataset_root,
                "device": self.config.device,
                "optimizer": "dmuon",
                "vram_shards": self.config.dmuon_vram_shards,
                "co_train": {
                    "vla_model": "Wall-OSS-0.5",
                    "world_model": "WALL-WM",
                    "action_supervision": "flow_matching",
                    "segmentation": "event_joints",
                },
            },
            "message": "Starter config skeleton; merge with upstream wall-x YAML.",
        }

    async def launch_co_train(
        self,
        *,
        confirm: bool = False,
        dataset_shard: str | None = None,
        extra_args: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict:
        if dry_run and not self.upstream_resolved():
            cmd = [
                sys.executable,
                "train_dmuon.py",
                "--dataset-root",
                self.config.dataset_root,
                "--device",
                self.config.device,
                "--dmuon-shards",
                str(self.config.dmuon_vram_shards),
            ]
            if dataset_shard:
                cmd.extend(["--shard", dataset_shard])
            if extra_args:
                cmd.extend(extra_args)
            return {
                "success": True,
                "dry_run": True,
                "upstream_missing": True,
                "command": cmd,
                "cwd": None,
                "message": "Speculative DMuon command (VLA_WALL_X_ROOT not set).",
            }

        prep = self.co_train_prepare(dataset_shard=dataset_shard)
        if not prep.get("success"):
            return prep
        root = self.upstream_resolved()
        assert root is not None
        script_path = prep.get("train_script")
        if not script_path:
            return {
                "success": False,
                "error": "No train script found in upstream repo",
                "recovery_options": [
                    "Check wall-x for scripts/train_dmuon.py",
                    "Set VLA_DMUON_LAUNCH_CMD env override (future)",
                ],
            }
        script = Path(script_path)
        cmd, cmd_meta = self._build_train_cmd(script, dataset_shard=dataset_shard, extra_args=extra_args)
        if dry_run or not confirm:
            return {
                "success": True,
                "dry_run": True,
                "command": cmd,
                "cwd": str(root),
                "cmd_meta": cmd_meta,
                "message": "Pass confirm=True to launch GPU co-training subprocess.",
            }
        job_id = uuid.uuid4().hex[:10]
        log_path = Path(self.config.dataset_root) / "logs" / f"dmuon_{job_id}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["VLA_DATASET_ROOT"] = self.config.dataset_root
        env["CUDA_VISIBLE_DEVICES"] = env.get("CUDA_VISIBLE_DEVICES", "0")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )
        _jobs[job_id] = {
            "id": job_id,
            "status": "running",
            "pid": proc.pid,
            "command": cmd,
            "started_at": time.time(),
            "log_path": str(log_path),
            "dataset_shard": dataset_shard,
        }
        _persist_job(self, job_id)

        async def _drain() -> None:
            assert proc.stdout is not None
            with log_path.open("w", encoding="utf-8") as logf:
                async for line in proc.stdout:
                    logf.write(line.decode("utf-8", errors="replace"))
            code = await proc.wait()
            _jobs[job_id]["status"] = "completed" if code == 0 else "failed"
            _jobs[job_id]["exit_code"] = code
            _jobs[job_id]["finished_at"] = time.time()
            _persist_job(self, job_id)

        task = asyncio.create_task(_drain())
        _drain_tasks[job_id] = task
        return {
            "success": True,
            "job_id": job_id,
            "pid": proc.pid,
            "log_path": str(log_path),
            "message": "DMuon co-training subprocess started.",
        }

    def job_status(self, job_id: str | None = None) -> dict:
        if job_id:
            job = _jobs.get(job_id)
            if not job:
                return {"success": False, "error": f"Unknown job_id: {job_id}"}
            return {"success": True, "job": _serialize_job(job)}
        return {
            "success": True,
            "jobs": [_serialize_job(j) for j in _jobs.values()],
            "count": len(_jobs),
        }

    def job_log(self, job_id: str, *, offset: int = 0) -> dict:
        job = _jobs.get(job_id)
        if not job:
            return {"success": False, "error": f"Unknown job_id: {job_id}"}
        log_path = job.get("log_path")
        if not log_path:
            return {"success": False, "error": "Job has no log_path"}
        out = read_log_tail(str(log_path), offset=offset)
        out["job_id"] = job_id
        return out

    def stop_job(self, job_id: str) -> dict:
        job = _jobs.get(job_id)
        if not job:
            return {"success": False, "error": f"Unknown job_id: {job_id}"}
        pid = job.get("pid")
        if job.get("status") != "running":
            return {"success": True, "message": f"Job {job_id} already {job.get('status')}"}
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F", "/T"],
                check=False,
                capture_output=True,
            )
            job["status"] = "stopped"
            _persist_job(self, job_id)
            return {"success": True, "message": f"Stopped job {job_id}"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
