"""Environment configuration for VLA-MCP."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _i(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class VLAConfig:
    """Runtime paths, ports, and upstream model roots."""

    wall_x_root: str | None
    wall_wm_root: str | None
    dmuon_root: str | None
    checkpoint_path: str | None
    dataset_root: str
    hf_cache_dir: str
    hf_wall_oss_repo: str
    hf_wall_wm_repo: str
    device: str
    dmuon_vram_shards: int
    api_port: int
    frontend_port: int
    mcp_http_path: str
    worldlabs_mcp_url: str | None
    robotics_mcp_url: str | None
    avatar_mcp_url: str | None
    mcp_bridge_urls: str | None
    prefab_apps: bool

    @classmethod
    def from_env(cls) -> VLAConfig:
        temp = os.getenv("TEMP") or os.getenv("TMP") or "."
        default_data = os.path.join(temp, "vla_mcp_data")
        default_hf = os.path.join(default_data, "hf_cache")
        return cls(
            wall_x_root=os.getenv("VLA_WALL_X_ROOT") or None,
            wall_wm_root=os.getenv("VLA_WALL_WM_ROOT") or None,
            dmuon_root=os.getenv("VLA_DMUON_ROOT") or None,
            checkpoint_path=os.getenv("VLA_CHECKPOINT") or None,
            dataset_root=os.getenv("VLA_DATASET_ROOT", default_data),
            hf_cache_dir=os.getenv("VLA_HF_CACHE_DIR", default_hf),
            hf_wall_oss_repo=os.getenv("VLA_HF_WALL_OSS_REPO", "X-Square-Robot/Wall-OSS-0.5"),
            hf_wall_wm_repo=os.getenv("VLA_HF_WALL_WM_REPO", "X-Square-Robot/WALL-WM"),
            device=os.getenv("VLA_DEVICE", "cuda:0"),
            dmuon_vram_shards=_i("VLA_DMUON_VRAM_SHARDS", 1),
            api_port=_i("VLA_API_PORT", 11024),
            frontend_port=_i("VLA_FRONTEND_PORT", 11025),
            mcp_http_path=os.getenv("MCP_PATH", "/mcp"),
            worldlabs_mcp_url=os.getenv("VLA_WORLDLABS_MCP_URL") or None,
            robotics_mcp_url=os.getenv("VLA_ROBOTICS_MCP_URL") or None,
            avatar_mcp_url=os.getenv("VLA_AVATAR_MCP_URL") or None,
            mcp_bridge_urls=os.getenv("VLA_MCP_BRIDGE_URLS") or None,
            prefab_apps=os.getenv("VLA_PREFAB_APPS", "1") == "1",
        )


def get_config() -> VLAConfig:
    return VLAConfig.from_env()
