"""Fleet peer URLs for worldlabs-mcp, yahboom-mcp, avatarops."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from ..config import VLAConfig, get_config

DEFAULT_PEERS = {
    "worldlabs-mcp": "http://127.0.0.1:10865",
    "yahboom-mcp": "http://127.0.0.1:10892",
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
            "yahboom-mcp": self.config.yahboom_mcp_url or DEFAULT_PEERS["yahboom-mcp"],
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
        results = await asyncio.gather(
            *[self.probe_peer(name, url) for name, url in peers.items()]
        )
        return {
            "success": True,
            "peers": list(results),
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
            "yahboom-mcp: run Raspbot car tasks with event tags (approaching, contact, recovery)",
            "avatarops: VRoid interaction episodes with slip/collision corrections",
            "vla_dataset: ingest_episode for each run (success + failure trajectories)",
            "vla_xvla: PEFT adapter for edge Raspbot; Wall-OSS on workstation",
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

    async def call_peer(
        self,
        peer: str,
        tool_name: str,
        arguments: dict | None = None,
    ) -> dict:
        """Invoke a tool on a fleet peer via HTTP REST bridge."""
        urls = self.peer_urls()
        key = peer.strip().lower().replace("_", "-")
        alias = {
            "worldlabs": "worldlabs-mcp",
            "yahboom": "yahboom-mcp",
            "robotics": "yahboom-mcp",
            "robotics-mcp": "yahboom-mcp",
            "avatar": "avatarops",
            "avatar-mcp": "avatarops",
            "avatarops": "avatarops",
        }
        name = alias.get(key, key)
        base = urls.get(name)
        if not base:
            return {
                "success": False,
                "error": f"Unknown peer: {peer}",
                "recovery_options": list(urls.keys()),
            }
        args = arguments or {}
        endpoints = [
            ("/api/v1/control/" + tool_name, args),
            ("/api/v1/tools/execute", {"tool_name": tool_name, "arguments": args}),
            ("/api/execute", {"tool": tool_name, "params": args}),
        ]
        async with httpx.AsyncClient(timeout=120.0) as client:
            for path, body in endpoints:
                try:
                    r = await client.post(base.rstrip("/") + path, json=body)
                    if r.status_code == 404:
                        continue
                    r.raise_for_status()
                    data = r.json()
                    return {
                        "success": True,
                        "peer": name,
                        "endpoint": path,
                        "result": data,
                    }
                except httpx.HTTPError:
                    continue
        return {
            "success": False,
            "error": f"No REST bridge accepted tool {tool_name} on {name}",
            "peer_url": base,
            "recovery_options": ["Start peer MCP HTTP server", "Set VLA_*_MCP_URL"],
        }
