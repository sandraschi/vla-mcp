"""Help topics for vla_help MCP tool and /api/v1/help."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_DOC_SLUGS: dict[str, str] = {
    "overview": "overview",
    "fleet": "FLEET_INTEGRATION.md",
    "fleet_integration": "FLEET_INTEGRATION.md",
    "api_keys": "FLEET_INTEGRATION.md",
    "configuration": "CONFIGURATION.md",
    "tools": "TOOLS.md",
    "setup": "SETUP.md",
    "architecture": "ARCHITECTURE.md",
    "troubleshooting": "TROUBLESHOOTING.md",
    "prd": "PRD.md",
}


def _repo_docs() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "docs"
        if candidate.is_dir() and (candidate / "TOOLS.md").is_file():
            return candidate
    return here.parents[2] / "docs"


def _read_doc(name: str) -> str:
    path = _repo_docs() / name
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return f"(missing doc: {name})"


def _overview() -> str:
    return """# vla-mcp help

Vision-Language-Action bridge: Wall-OSS, WALL-WM, DMuon, X-VLA + fleet loops.

## Topics (`vla_help(topic="...")`)

| topic | Content |
|-------|---------|
| `fleet` / `fleet_integration` | aiwatcher ingest, peers, liveness |
| `api_keys` | VLA_AIWATCHER_API_KEY / AIWATCHER_API_KEY |
| `tools` | Portmanteau tool reference |
| `configuration` | All env vars |
| `setup` | Install |
| `troubleshooting` | Common failures |

## Key tools

- `vla_pipeline` — worldlabs → yahboom → dataset → DMuon dry-run
- `vla_fleet` — peer probes + scenario brief
- `vla_weights` — HuggingFace Wall-OSS / X-VLA
- `vla_help` — this help

## Ports

- Backend: **11024** | Webapp: **11025**

## Fleet peers

worldlabs :10865 | robotics-mcp :10706 | yahboom :10892 | avatarops :10793
"""


def get_help(topic: str | None = None) -> dict[str, Any]:
    topics = sorted(
        {
            "overview",
            "fleet",
            "fleet_integration",
            "api_keys",
            "configuration",
            "tools",
            "setup",
            "architecture",
            "troubleshooting",
            "prd",
        }
    )
    if not topic:
        return {
            "success": True,
            "server": "vla-mcp",
            "topics": topics,
            "markdown": _overview(),
            "content": _overview(),
            "message": "Call vla_help(topic='fleet_integration') for fleet docs.",
        }

    key = topic.strip().lower().replace("-", "_")
    if key == "api_keys":
        md = _read_doc("FLEET_INTEGRATION.md")
        # Prepend key summary for agents that only read the top.
        prefix = (
            "## API keys (summary)\n\n"
            "- `AIWATCHER_API_KEY` on aiwatcher-mcp — optional REST auth\n"
            "- `VLA_AIWATCHER_API_KEY` on vla-mcp — **same value** when auth is on\n"
            "- Leave both empty for localhost-only fleet ingest\n\n"
        )
        md = prefix + md
    elif key in ("overview",):
        md = _overview()
    else:
        file_name = _DOC_SLUGS.get(key)
        if not file_name or file_name == "overview":
            return {
                "success": False,
                "error": f"Unknown topic: {topic}",
                "topics": topics,
            }
        md = _read_doc(file_name)

    return {
        "success": True,
        "topic": key,
        "markdown": md,
        "content": md,
        "message": f"Loaded help topic '{key}'",
    }


def list_slugs() -> list[str]:
    docs = _repo_docs()
    slugs = []
    for name in (
        "PRD.md",
        "ARCHITECTURE.md",
        "SETUP.md",
        "TOOLS.md",
        "CONFIGURATION.md",
        "TROUBLESHOOTING.md",
        "FLEET_INTEGRATION.md",
    ):
        if (docs / name).is_file():
            slugs.append(name.replace(".md", "").lower())
    return slugs
