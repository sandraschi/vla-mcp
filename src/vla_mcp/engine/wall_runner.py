"""Bridge to X Square wall-x (Wall-OSS-0.5 VLA execution engine)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import VLAConfig, get_config

WALL_X_REPO = "https://github.com/X-Square-Robot/wall-x"
WALL_OSS_TASKS = (
    "pick_place",
    "drawer_open",
    "pour",
    "wipe",
    "stack",
    "push",
    "insert",
    "fold",
    "unscrew",
    "button_press",
    "slide",
    "lift",
    "navigate",
    "reach",
    "grasp",
    "release",
    "tool_use",
)


@dataclass
class WallRunner:
    """Validates wall-x clone and describes Wall-OSS-0.5 invoke paths."""

    config: VLAConfig

    @classmethod
    def default(cls) -> WallRunner:
        return cls(config=get_config())

    def upstream_resolved(self) -> Path | None:
        if not self.config.wall_x_root:
            return None
        p = Path(self.config.wall_x_root).expanduser().resolve()
        return p if p.is_dir() else None

    def health(self) -> dict:
        root = self.upstream_resolved()
        ck = self.config.checkpoint_path
        ck_ok = bool(ck and Path(ck).expanduser().is_file())
        return {
            "model": "Wall-OSS-0.5",
            "upstream_configured": root is not None,
            "upstream_path": str(root) if root else None,
            "reference_repo": WALL_X_REPO,
            "checkpoint_set": ck is not None,
            "checkpoint_exists": ck_ok,
            "device": self.config.device,
            "zero_shot_tasks": len(WALL_OSS_TASKS),
            "control_mode": "flow_matching_action_supervision",
        }

    def infer_prepare(self, task_hint: str | None = None) -> dict:
        root = self.upstream_resolved()
        if not root:
            return {
                "success": False,
                "error": "VLA_WALL_X_ROOT is not set or not a directory",
                "error_type": "not_configured",
                "recovery_options": [
                    f"Clone {WALL_X_REPO}",
                    "Set VLA_WALL_X_ROOT to the clone root",
                    "Set VLA_CHECKPOINT to a Wall-OSS-0.5 weight file",
                ],
            }
        return {
            "success": True,
            "message": (
                "Wall-OSS-0.5 upstream found. Run inference from wall-x per upstream README "
                "(flow-matching action head, zero-shot capable on new grippers)."
            ),
            "upstream": str(root),
            "task_hint": task_hint,
            "checkpoint": self.config.checkpoint_path,
        }

    def finetune_prepare(self, recipe: str | None = None) -> dict:
        root = self.upstream_resolved()
        if not root:
            return {
                "success": False,
                "error": "VLA_WALL_X_ROOT not configured",
                "recovery_options": [f"Clone {WALL_X_REPO}"],
            }
        return {
            "success": True,
            "message": (
                "Gradient-bridged co-training recipe available in wall-x. "
                "Use vla_training(operation='co_train_prepare') for DMuon wiring."
            ),
            "upstream": str(root),
            "recipe": recipe or "gradient_bridged_co_train",
        }

    def list_tasks(self) -> dict:
        return {
            "success": True,
            "tasks": list(WALL_OSS_TASKS),
            "count": len(WALL_OSS_TASKS),
            "message": "Representative Wall-OSS zero-shot task families (see upstream for full eval).",
        }

    def edge_prepare(self, *, target: str = "raspbot") -> dict:
        from .xvla_adapter import XVLAAdapter

        return XVLAAdapter.default().edge_prepare(target=target)
