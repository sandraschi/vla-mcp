# vla-mcp ⚠️ Alpha — Preemptive Infrastructure

**Status: Alpha / Shelfware.** This server was scaffolded as infrastructure for a future robotics training pipeline. It has never been used in production. No robots have been trained with it. It exists so that when someone collects teleoperation demos and runs DMuon training, the bridge is ready. Until then it's preemptive — not broken, just waiting.

MCP bridge for **Vision-Language-Action** — orchestrates X Square [wall-x](https://github.com/X-Square-Robot/wall-x) (Wall-OSS-0.5, WALL-WM, DMuon) with your fleet: **worldlabs-mcp**, **robotics-mcp**, **avatarops**. Event-joint data pipelines instead of ROS bag spaghetti.

**Why VLA though?** VLA (Vision-Language-Action) models take camera images + text commands and output robot motor commands. Think "pick up the red cube" → joint angle trajectory. This server bridges telemetry collection (multiview video, sim state) to co-training jobs (DMuon on wall-x weights). It's not a Tapo cam script — it's a training pipeline for behavioral cloning from demonstration.

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

<p align="center">
  <a href="https://github.com/sandraschi/vla-mcp"><img src="https://img.shields.io/badge/Status-Alpha/orange?style=flat-square" alt="Alpha"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

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
- Fleet peers optional: worldlabs-mcp, robotics-mcp, yahboom-mcp, avatarops
- aiwatcher fleet ingest on pipeline complete (`docs/FLEET_INTEGRATION.md`)
- MCP help: `vla_help(topic="fleet_integration")` | webapp Help tab

## License

MIT
