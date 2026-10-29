"""Bridge to World Action Models: WALL-WM (Wan video prior + action DiT) and Google DeepMind Genie 4."""

from __future__ import annotations

import os
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
    """Validates WALL-WM paths, Genie 4 integrations, and event-grounded rollout prep."""

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

    def genie4_health(self) -> dict:
        """Health check for Google DeepMind Genie 4 interactive world model."""
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        return {
            "model": "Genie 4",
            "provider": "Google DeepMind",
            "release_date": "2026-10-27",
            "access_tier": "Research Preview / Trusted Tester",
            "api_key_configured": api_key is not None,
            "gemini_omni_anchor": True,
            "gemini_flash_reasoning": True,
            "multimodal_audio": True,
            "interactive_steering": True,
            "physics_gating": "MuJoCo 3.x / Isaac Lab",
            "evaluator_script": "D:/Dev/repos/robotics-mcp/pipeline/11_genie4_world_model_evaluator.py",
        }

    def genie4_rollout_prepare(
        self,
        scenario_prompt: str = "Tiled floor with unexpected moving obstacles",
        horizon_steps: int = 32,
        dt: float = 0.02,
    ) -> dict:
        """Prepares a prompt-conditioned neural rollout inside Genie 4."""
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        return {
            "success": True,
            "model": "Genie 4",
            "mode": "live" if api_key else "mock_preview",
            "scenario_prompt": scenario_prompt,
            "horizon_steps": horizon_steps,
            "dt": dt,
            "message": "Genie 4 world model rollout prepared for robotics dojo.",
            "next_step": "Execute pipeline/11_genie4_world_model_evaluator.py for neural rollout and plausibility gating.",
        }
