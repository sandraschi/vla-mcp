# vla-mcp

MCP bridge for **Vision-Language-Action** — orchestrates X Square [wall-x](https://github.com/X-Square-Robot/wall-x) (Wall-OSS-0.5, WALL-WM, DMuon) with your fleet: **worldlabs-mcp**, **robotics-mcp**, **avatarops**. Event-joint data pipelines instead of ROS bag spaghetti.

## How it runs

| Mode | When |
|------|------|
| **Stdio MCP** | Cursor / Claude Desktop (`python -m vla_mcp.server --stdio`) |
| **HTTP + dashboard** | Local co-training prep on ports **11024** / **11025** |

> **Headless by default for GPU jobs** — DMuon launch requires `confirm=True`; downloads need Hugging Face access.

## Hands-in / Hands-out

| Direction | Artifacts | Notes |
|-----------|-----------|-------|
| **Hands-in** | Multiview video, action trajectories, sim telemetry | Tag **event joints** (approaching, contact, lift, recovery) |
| **Hands-out** | JSON/numpy shards, HF weights cache, DMuon job logs | Feeds wall-x co-training; Wall-OSS infer on edge |

## Features

- Wall-OSS-0.5 VLA prep (gradient-bridged MoT, flow-matching actions)
- WALL-WM world model prep (Wan prior, event joints vs equilong chunks)
- Hugging Face weight download helper
- Telemetry → event-joint auto-segmentation
- Dataset registry + numpy export for DMuon
- DMuon co-train launch with job tracking
- Fleet peer probe + REST `call_peer` bridge
- MCP proxy federation to worldlabs / robotics / avatar
- FastMCP 3.2: skills, prompts, Prefab status card

## Quick install

```powershell
git clone https://github.com/sandraschi/vla-mcp
cd vla-mcp
uv sync --extra dev
.\start.bat
```

Full paths: [INSTALL.md](INSTALL.md)

## What you can do

> "Run vla_status and give me a scenario brief for Raspbot + VRoid training in a cluttered room."

> "Segment this telemetry into event joints and ingest as a dataset episode."

> "Dry-run DMuon co-training on shard train_001."

## Documentation

| Doc | Contents |
|-----|----------|
| [Installation](INSTALL.md) | winget, uv, Claude config, verify |
| [Configuration](docs/CONFIGURATION.md) | Env vars |
| [Tool Reference](docs/TOOLS.md) | All MCP tools |
| [Development](docs/DEVELOPMENT.md) | just, pytest, contributing |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common errors |
| [Architecture](docs/ARCHITECTURE.md) | System design |
| [PRD](docs/PRD.md) | Product requirements |

## Requirements

- Windows 10/11 (primary), Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Optional: CUDA GPU, clone of wall-x, Hugging Face token for gated weights
- Fleet peers optional: worldlabs-mcp, robotics-mcp, avatarops

## License

MIT
