"""Hugging Face weight download and cache management for Wall-OSS / WALL-WM / X-VLA."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import VLAConfig, get_config

CATALOG = {
    "wall-oss-0.5": {
        "env_key": "hf_wall_oss_repo",
        "description": "Wall-OSS-0.5 VLA execution weights (gradient-bridged MoT)",
    },
    "wall-wm": {
        "env_key": "hf_wall_wm_repo",
        "description": "WALL-WM world action model (Wan video prior + action DiT)",
    },
    "x-vla": {
        "env_key": "hf_xvla_repo",
        "description": "2toinf X-VLA 0.9B soft-prompted flow-matching VLA for edge PEFT (ICLR 2026; in LeRobot)",
    },
}


def _slug(model_key: str) -> str:
    return model_key.strip().lower().replace(".", "_").replace("-", "_")


@dataclass
class HFWeightManager:
    """Download and track open-weight checkpoints from Hugging Face."""

    config: VLAConfig

    @classmethod
    def default(cls) -> HFWeightManager:
        return cls(config=get_config())

    def cache_root(self) -> Path:
        p = Path(self.config.hf_cache_dir).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    def local_dir_for(self, model_key: str) -> Path:
        return self.cache_root() / _slug(model_key)

    def repo_id_for(self, model_key: str) -> str | None:
        key = model_key.strip().lower()
        if key in ("wall-oss", "wall-oss-0.5", "wall_oss"):
            return self.config.hf_wall_oss_repo
        if key in ("wall-wm", "wall_wm", "wallwm"):
            return self.config.hf_wall_wm_repo
        if key in ("x-vla", "xvla", "x_vla"):
            return self.config.hf_xvla_repo
        return None

    def list_models(self) -> dict:
        items = []
        for key, meta in CATALOG.items():
            repo = self.repo_id_for(key)
            local = self.local_dir_for(key)
            items.append(
                {
                    "key": key,
                    "repo_id": repo,
                    "description": meta["description"],
                    "local_path": str(local),
                    "downloaded": local.is_dir() and any(local.iterdir()) if local.exists() else False,
                }
            )
        return {"success": True, "models": items, "cache_dir": str(self.cache_root())}

    def local_status(self, model_key: str | None = None) -> dict:
        if model_key:
            repo = self.repo_id_for(model_key)
            if not repo:
                return {"success": False, "error": f"Unknown model key: {model_key}"}
            local = self.local_dir_for(model_key)
            return {
                "success": True,
                "model_key": model_key,
                "repo_id": repo,
                "path": str(local),
                "exists": local.is_dir() and any(local.iterdir()) if local.exists() else False,
            }
        return self.list_models()

    def download(self, model_key: str, *, revision: str | None = None) -> dict:
        repo_id = self.repo_id_for(model_key)
        if not repo_id:
            return {
                "success": False,
                "error": f"Unknown model key: {model_key}",
                "recovery_options": list(CATALOG.keys()),
            }
        target = self.local_dir_for(model_key)
        try:
            from huggingface_hub import snapshot_download
        except ImportError:
            return {
                "success": False,
                "error": "huggingface_hub not installed",
                "recovery_options": ["uv sync"],
            }
        try:
            path = snapshot_download(
                repo_id=repo_id,
                revision=revision,
                local_dir=str(target),
            )
            return {
                "success": True,
                "model_key": model_key,
                "repo_id": repo_id,
                "path": path,
                "message": f"Downloaded {repo_id} to {path}",
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "error_type": "hf_download",
                "repo_id": repo_id,
                "recovery_options": [
                    "Verify repo id on Hugging Face",
                    "Set VLA_HF_*_REPO env vars",
                    "Run huggingface-cli login if gated",
                ],
            }
