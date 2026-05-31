"""Fleet peer URLs for worldlabs-mcp, robotics-mcp, avatarops."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from ..config import VLAConfig, get_config

DEFAULT_PEERS = {
    "worldlabs-mcp": "http://127.0.0.1:10865",
    "robotics-mcp": "http://127.0.0.1:10892",
    "avatarops": "http://127.0.0.1:10793",
}


@dataclass
class FleetBridge:
    """HTTP probes and scenario briefs for simulation data generation."""

    config: VLAConfig

    @classmethod
    def default(cls) -> FleetBridge:
        return cls(config=get_config())

    def peer_urls(self) -> dict[str, str | None]:
        return {
            "worldlabs-mcp": self.config.worldlabs_mcp_url or DEFAULT_PEERS["worldlabs-mcp"],
            "robotics-mcp": self.config.robotics_mcp_url or DEFAULT_PEERS["robotics-mcp"],
            "avatarops": self.config.avatar_mcp_url or DEFAULT_PEERS["avatarops"],
        }

    async def probe_peer(self, name: str, url: str | None) -> dict:
        if not url:
            return {"name": name, "reachable": False, "error": "URL not configured"}
        health_paths = ("/api/status", "/api/v1/status", "/health", "/")
        async with httpx.AsyncClient(timeout=3.0) as client:
            for path in health_paths:
                try:
                    r = await client.get(f"{url.rstrip('/')}{path}")
                    if r.status_code < 500:
                        return {"name": name, "url": url, "reachable": True, "probe_path": path}
                except httpx.HTTPError:
                    continue
        return {"name": name, "url": url, "reachable": False, "error": "No health endpoint responded"}

    async def bridge_status(self) -> dict:
        peers = self.peer_urls()
        results = []
        for name, url in peers.items():
            results.append(await self.probe_peer(name, url))
        return {
            "success": True,
            "peers": results,
            "message": "Fleet simulation boundary peers for VLA data loops.",
        }

    def scenario_brief(
        self,
        *,
        room_style: str = "cluttered_indoor",
        include_failures: bool = True,
        agents: list[str] | None = None,
    ) -> dict:
        agents = agents or ["raspbot", "vroid"]
        steps = [
            "worldlabs-mcp: generate navigable 3D room with multiview camera rigs",
            "robotics-mcp: run Raspbot car tasks with event tags (approaching, contact, recovery)",
            "avatarops: VRoid interaction episodes with slip/collision corrections",
            "vla_dataset: ingest_episode for each run (success + failure trajectories)",
            "vla_training: co_train_prepare with DMuon on exported shards",
        ]
        if include_failures:
            steps.insert(3, "Record non-nominal paths: slips, collisions, recovery (required for robust WM)")
        return {
            "success": True,
            "room_style": room_style,
            "agents": agents,
            "steps": steps,
            "peers": self.peer_urls(),
            "message": "Closed-loop synthetic training brief for Wall-OSS + WALL-WM.",
        }
