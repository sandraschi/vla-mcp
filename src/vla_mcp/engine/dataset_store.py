"""Local event-grounded trajectory store (video + action shards)."""

from __future__ import annotations

import json
import os
import shutil
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..config import VLAConfig, get_config

_index_lock = threading.Lock()


@dataclass
class DatasetStore:
    """Filesystem-backed episode registry for co-training exports."""

    config: VLAConfig

    @classmethod
    def default(cls) -> DatasetStore:
        return cls(config=get_config())

    @property
    def root(self) -> Path:
        p = Path(self.config.dataset_root).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        (p / "episodes").mkdir(exist_ok=True)
        (p / "exports").mkdir(exist_ok=True)
        return p

    def _index_path(self) -> Path:
        return self.root / "index.json"

    def _load_index(self) -> dict[str, Any]:
        path = self._index_path()
        if not path.is_file():
            return {"episodes": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_index(self, data: dict[str, Any]) -> None:
        path = self._index_path()
        tmp = path.with_suffix(".json.tmp")
        payload = json.dumps(data, indent=2)
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, path)

    def ingest_episode(
        self,
        *,
        source: str,
        events: list[str],
        video_paths: list[str] | None = None,
        action_path: str | None = None,
        actions: list[Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        episode_id = uuid.uuid4().hex[:12]
        meta = dict(metadata or {})
        if actions is not None:
            meta["actions"] = actions
        record = {
            "id": episode_id,
            "source": source,
            "events": events,
            "video_paths": video_paths or [],
            "action_path": action_path,
            "metadata": meta,
            "created_at": datetime.now(UTC).isoformat(),
        }
        ep_file = self.root / "episodes" / f"{episode_id}.json"
        ep_file.write_text(json.dumps(record, indent=2), encoding="utf-8")
        with _index_lock:
            idx = self._load_index()
            idx["episodes"].append({"id": episode_id, "source": source, "events": events})
            self._save_index(idx)
        return {
            "success": True,
            "episode_id": episode_id,
            "path": str(ep_file),
            "message": "Episode registered for WALL-WM / Wall-OSS co-training export.",
        }

    def list_episodes(self, *, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        limit = max(1, min(limit, 200))
        offset = max(0, offset)
        with _index_lock:
            rows = self._load_index().get("episodes", [])
        page = rows[offset : offset + limit]
        return {
            "success": True,
            "items": page,
            "count": len(page),
            "total": len(rows),
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < len(rows),
        }

    def export_shard(self, *, shard_name: str, episode_ids: list[str] | None = None) -> dict[str, Any]:
        with _index_lock:
            idx = self._load_index()
        ids = episode_ids or [e["id"] for e in idx.get("episodes", [])]
        manifest = {"shard": shard_name, "episodes": []}
        for eid in ids:
            ep = self.root / "episodes" / f"{eid}.json"
            if ep.is_file():
                manifest["episodes"].append(json.loads(ep.read_text(encoding="utf-8")))
        out = self.root / "exports" / f"{shard_name}.json"
        out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return {
            "success": True,
            "export_path": str(out),
            "episode_count": len(manifest["episodes"]),
            "message": "Shard manifest written for DMuon / wall-x dataloader wiring.",
        }

    def validate_multiview(self, *, video_paths: list[str]) -> dict[str, Any]:
        missing = [p for p in video_paths if not Path(p).expanduser().is_file()]
        return {
            "success": len(missing) == 0,
            "views": len(video_paths),
            "missing": missing,
            "calibration_required": False,
            "message": (
                "WALL-WM cross-view attention expects aligned streams; "
                "calibration-free fusion is upstream-side."
            ),
        }

    def segment_and_ingest(
        self,
        *,
        source: str,
        telemetry: list[dict[str, Any]],
        video_paths: list[str] | None = None,
        action_path: str | None = None,
        actions: list[Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from .event_segmenter import EventSegmenter

        seg = EventSegmenter().segment(telemetry)
        if not seg.get("success"):
            return seg
        events = seg.get("events") or []
        meta = {**(metadata or {}), "segments": seg.get("segments", [])}
        result = self.ingest_episode(
            source=source,
            events=events,
            video_paths=video_paths,
            action_path=action_path,
            actions=actions,
            metadata=meta,
        )
        result["segments"] = seg.get("segments", [])
        result["events"] = events
        return result

    def export_numpy_shard(self, *, shard_name: str, episode_ids: list[str] | None = None) -> dict[str, Any]:
        import numpy as np

        manifest_result = self.export_shard(shard_name=shard_name, episode_ids=episode_ids)
        if not manifest_result.get("success"):
            return manifest_result
        manifest_path = Path(manifest_result["export_path"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        arrays_dir = self.root / "exports" / "numpy" / shard_name
        arrays_dir.mkdir(parents=True, exist_ok=True)
        written = 0
        for ep in manifest.get("episodes", []):
            out = arrays_dir / f"{ep['id']}_actions.npy"
            actions = ep.get("metadata", {}).get("actions")
            if isinstance(actions, list) and actions:
                np.save(out, np.asarray(actions, dtype=np.float32))
                written += 1
                continue
            ap = ep.get("action_path")
            if ap:
                src = Path(ap).expanduser()
                if src.suffix == ".npy" and src.is_file():
                    shutil.copy2(src, out)
                    written += 1
        return {
            "success": True,
            "manifest_path": str(manifest_path),
            "numpy_dir": str(arrays_dir),
            "arrays_written": written,
            "episode_count": manifest_result.get("episode_count", 0),
            "message": "JSON manifest + numpy action arrays for DMuon dataloaders.",
        }
