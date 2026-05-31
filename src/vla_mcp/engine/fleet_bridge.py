"""Fleet peer URLs for worldlabs-mcp, yahboom-mcp, avatarops."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

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

    def _resolve_peer(self, peer: str) -> tuple[str | None, str | None]:
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
        return name, urls.get(name)

    def _yahboom_tool_body(self, args: dict[str, Any]) -> dict[str, Any]:
        body: dict[str, Any] = {"operation": args.get("operation", "health_check")}
        for key in ("param1", "param2", "param3", "payload"):
            if key in args:
                body[key] = args[key]
        return body

    def _yahboom_demo_routes(self, args: dict[str, Any]) -> list[tuple[str, str, dict[str, Any] | None]]:
        """Return (method, path, json_body) candidates for yahboom_demo operations."""
        op = str(args.get("operation", "describe")).strip().lower()
        if op == "draw":
            body = {
                k: args[k]
                for k in ("pattern", "speed", "skip_color_swap_pause")
                if k in args
            }
            return [("POST", "/api/v1/demo/draw", body)]
        if op == "talkbot":
            body = {
                k: args[k]
                for k in ("approach", "max_turns", "use_speech_mcp", "scripted_user_lines")
                if k in args
            }
            return [("POST", "/api/v1/demo/talkbot", body)]
        if op == "draw_status":
            return [("GET", "/api/v1/demo/draw/status", None)]
        if op == "talkbot_status":
            return [("GET", "/api/v1/demo/talkbot/status", None)]
        if op == "describe":
            return [("GET", "/api/v1/demo", None)]
        return []

    async def yahboom_post(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        timeout: float = 120.0,
    ) -> dict[str, Any]:
        base = self.peer_urls().get("yahboom-mcp")
        if not base:
            return {"success": False, "error": "yahboom-mcp URL not configured"}
        url = base.rstrip("/") + path
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                r = await client.post(url, json=body or {})
                r.raise_for_status()
                data = r.json()
                return {"success": True, "endpoint": path, "result": data}
            except httpx.HTTPError as exc:
                return {"success": False, "error": str(exc), "endpoint": path}

    async def yahboom_get(self, path: str, *, timeout: float = 30.0) -> dict[str, Any]:
        base = self.peer_urls().get("yahboom-mcp")
        if not base:
            return {"success": False, "error": "yahboom-mcp URL not configured"}
        url = base.rstrip("/") + path
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
                return {"success": True, "endpoint": path, "result": data}
            except httpx.HTTPError as exc:
                return {"success": False, "error": str(exc), "endpoint": path}

    async def yahboom_tool(self, operation: str, **kwargs: Any) -> dict[str, Any]:
        body = self._yahboom_tool_body({"operation": operation, **kwargs})
        out = await self.yahboom_post("/api/v1/control/tool", body)
        if out.get("success"):
            out["peer"] = "yahboom-mcp"
            out["tool"] = "yahboom_tool"
        return out

    async def yahboom_run_demo(self, demo: str, **kwargs: Any) -> dict[str, Any]:
        """Start a Boomy show-floor demo (draw or talkbot) via yahboom-mcp REST."""
        demo = demo.strip().lower()
        if demo == "draw":
            body = {
                k: kwargs[k]
                for k in ("pattern", "speed", "skip_color_swap_pause")
                if k in kwargs
            }
            return await self.yahboom_post("/api/v1/demo/draw", body)
        if demo == "talkbot":
            body = {
                k: kwargs[k]
                for k in ("approach", "max_turns", "use_speech_mcp", "scripted_user_lines")
                if k in kwargs
            }
            return await self.yahboom_post("/api/v1/demo/talkbot", body)
        return {"success": False, "error": f"Unknown Boomy demo: {demo}"}

    async def poll_yahboom_demo(
        self,
        demo: str,
        *,
        timeout_s: float = 600.0,
        poll_s: float = 1.0,
    ) -> dict[str, Any]:
        """Poll draw/talkbot status until idle or timeout."""
        demo = demo.strip().lower()
        if demo not in ("draw", "talkbot"):
            return {"success": False, "error": f"Cannot poll demo: {demo}"}
        path = f"/api/v1/demo/{demo}/status"
        deadline = time.monotonic() + timeout_s
        last: dict[str, Any] = {}
        while time.monotonic() < deadline:
            snap = await self.yahboom_get(path)
            if not snap.get("success"):
                return snap
            last = snap.get("result") or {}
            running = last.get("running")
            status = str(last.get("status", "")).lower()
            if running is False or status in ("completed", "error", "stopped", "cancelled", "idle"):
                return {"success": True, "demo": demo, "result": last, "endpoint": path}
            await asyncio.sleep(poll_s)
        return {
            "success": False,
            "error": f"Boomy {demo} demo timed out after {timeout_s}s",
            "last_status": last,
        }

    async def call_peer(
        self,
        peer: str,
        tool_name: str,
        arguments: dict | None = None,
    ) -> dict:
        """Invoke a tool on a fleet peer via HTTP REST bridge."""
        name, base = self._resolve_peer(peer)
        if not base:
            return {
                "success": False,
                "error": f"Unknown peer: {peer}",
                "recovery_options": list(self.peer_urls().keys()),
            }
        args = arguments or {}
        endpoints: list[tuple[str, str, dict[str, Any] | None]] = []

        if name == "yahboom-mcp":
            if tool_name == "yahboom_tool":
                endpoints.append(
                    ("POST", "/api/v1/control/tool", self._yahboom_tool_body(args))
                )
            elif tool_name == "yahboom_demo":
                endpoints.extend(self._yahboom_demo_routes(args))

        endpoints.extend(
            [
                ("POST", "/api/v1/control/" + tool_name, args),
                ("POST", "/api/v1/tools/execute", {"tool_name": tool_name, "arguments": args}),
                ("POST", "/api/execute", {"tool": tool_name, "params": args}),
            ]
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            for method, path, body in endpoints:
                try:
                    url = base.rstrip("/") + path
                    if method == "GET":
                        r = await client.get(url)
                    else:
                        r = await client.post(url, json=body or {})
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

    @staticmethod
    def find_viewer_url(data: Any, *, _depth: int = 0) -> str | None:
        """Best-effort extraction of a Marble/world viewer URL from a peer result."""
        if _depth > 6 or data is None:
            return None
        if isinstance(data, str):
            s = data.strip()
            if s.startswith("http") and any(k in s for k in ("marble", "viewer", "world")):
                return s
            return None
        if isinstance(data, dict):
            for key in ("viewer_url", "marble_url", "world_url", "url", "viewer", "link"):
                v = data.get(key)
                if isinstance(v, str) and v.startswith("http"):
                    return v
            for v in data.values():
                found = FleetBridge.find_viewer_url(v, _depth=_depth + 1)
                if found:
                    return found
            return None
        if isinstance(data, (list, tuple)):
            for v in data:
                found = FleetBridge.find_viewer_url(v, _depth=_depth + 1)
                if found:
                    return found
        return None

    async def generate_world(self, prompt: str, *, extra: dict | None = None) -> dict:
        """Ask worldlabs-mcp to generate a navigable 3D room; surface the viewer URL.

        The peer tool name and prompt argument are configurable
        (VLA_WORLDLABS_GEN_TOOL / VLA_WORLDLABS_GEN_ARG) to match the live worldlabs-mcp API.
        """
        cfg = self.config
        args: dict[str, Any] = {cfg.worldlabs_gen_arg: prompt}
        if extra:
            args.update(extra)
        res = await self.call_peer("worldlabs-mcp", cfg.worldlabs_gen_tool, args)
        if not res.get("success"):
            return {
                **res,
                "prompt": prompt,
                "tool": cfg.worldlabs_gen_tool,
                "hint": "Set VLA_WORLDLABS_GEN_TOOL / VLA_WORLDLABS_GEN_ARG to match worldlabs-mcp",
            }
        return {
            "success": True,
            "prompt": prompt,
            "tool": cfg.worldlabs_gen_tool,
            "endpoint": res.get("endpoint"),
            "viewer_url": self.find_viewer_url(res.get("result")),
            "result": res.get("result"),
        }
