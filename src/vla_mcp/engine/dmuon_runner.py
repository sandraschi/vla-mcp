"""Bridge to DMuon distributed Muon optimizer (wall-x training stack)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import VLAConfig, get_config

DMUON_REPO = "https://github.com/X-Square-Robot/wall-x"


@dataclass
class DMuonRunner:
    """Validates DMuon clone and co-training launch guidance."""

    config: VLAConfig

    @classmethod
    def default(cls) -> DMuonRunner:
        return cls(config=get_config())

    def upstream_resolved(self) -> Path | None:
        root = self.config.dmuon_root or self.config.wall_x_root
        if not root:
            return None
        p = Path(root).expanduser().resolve()
        return p if p.is_dir() else None

    def health(self) -> dict:
        root = self.upstream_resolved()
        return {
            "optimizer": "DMuon",
            "upstream_configured": root is not None,
            "upstream_path": str(root) if root else None,
            "reference_repo": DMUON_REPO,
            "device": self.config.device,
            "notes": "Matrix-sharded Muon for VLA co-training; see wall-x training docs.",
        }

    def co_train_prepare(self, *, dataset_shard: str | None = None) -> dict:
        root = self.upstream_resolved()
        if not root:
            return {
                "success": False,
                "error": "VLA_DMUON_ROOT or VLA_WALL_X_ROOT not configured",
                "recovery_options": [f"Clone {DMUON_REPO}", "Export shards via vla_dataset"],
            }
        return {
            "success": True,
            "message": (
                "DMuon co-training ready to wire. Point wall-x config at VLA_DATASET_ROOT exports."
            ),
            "upstream": str(root),
            "dataset_shard": dataset_shard,
            "dataset_root": self.config.dataset_root,
        }

    def config_template(self) -> dict:
        return {
            "success": True,
            "template": {
                "wall_x_root": self.config.wall_x_root or "${VLA_WALL_X_ROOT}",
                "dataset_root": self.config.dataset_root,
                "device": self.config.device,
                "optimizer": "dmuon",
                "co_train": {
                    "vla_model": "Wall-OSS-0.5",
                    "world_model": "WALL-WM",
                    "action_supervision": "flow_matching",
                },
            },
            "message": "Starter config skeleton; merge with upstream wall-x YAML.",
        }
