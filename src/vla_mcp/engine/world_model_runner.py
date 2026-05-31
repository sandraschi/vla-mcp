"""Bridge to WALL-WM world action model (Wan video prior + action DiT)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import VLAConfig, get_config

WALL_WM_REPO = "https://github.com/X-Square-Robot/wall-x"
EVENT_VOCAB = (
    "approaching",
    "making_contact",
    "lifting",
    "sliding",
    "releasing",
    "colliding",
    "recovering",
    "idle",
)


@dataclass
class WorldModelRunner:
    """Validates WALL-WM paths and event-grounded rollout prep."""

    config: VLAConfig

    @classmethod
    def default(cls) -> WorldModelRunner:
        return cls(config=get_config())

    def upstream_resolved(self) -> Path | None:
        root = self.config.wall_wm_root or self.config.wall_x_root
        if not root:
            return None
        p = Path(root).expanduser().resolve()
        return p if p.is_dir() else None

    def health(self) -> dict:
        root = self.upstream_resolved()
        return {
            "model": "WALL-WM",
            "upstream_configured": root is not None,
            "upstream_path": str(root) if root else None,
            "reference_repo": WALL_WM_REPO,
            "video_prior": "Wan text-to-video",
            "action_head": "Action Diffusion Transformer (DiT)",
            "perception": "multi_view_calibration_free",
            "event_segments": len(EVENT_VOCAB),
            "device": self.config.device,
        }

    def train_prepare(self, notes: str | None = None) -> dict:
        root = self.upstream_resolved()
        if not root:
            return {
                "success": False,
                "error": "VLA_WALL_WM_ROOT or VLA_WALL_X_ROOT not configured",
                "recovery_options": [
                    f"Clone {WALL_WM_REPO} (wall-x monorepo)",
                    "Set VLA_WALL_WM_ROOT to the WALL-WM subtree or repo root",
                ],
            }
        return {
            "success": True,
            "message": (
                "WALL-WM training uses action-grounded semantic events and Wan coupling. "
                "Feed multiview video + action arrays from vla_dataset exports."
            ),
            "upstream": str(root),
            "notes": notes,
        }

    def predict_prepare(self, horizon_steps: int = 16) -> dict:
        root = self.upstream_resolved()
        if not root:
            return {
                "success": False,
                "error": "WALL-WM upstream not configured",
                "recovery_options": ["Set VLA_WALL_WM_ROOT"],
            }
        return {
            "success": True,
            "message": "Roll-forward world model inference hook (does not start GPU job).",
            "upstream": str(root),
            "horizon_steps": horizon_steps,
            "checkpoint": self.config.checkpoint_path,
        }

    def event_vocab(self) -> dict:
        return {
            "success": True,
            "events": list(EVENT_VOCAB),
            "count": len(EVENT_VOCAB),
            "message": "Action-grounded semantic events for trajectory segmentation.",
        }
