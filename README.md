# vla-mcp — Vision-Language-Action bridge (Alpha - Preemptive Infrastructure)

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
- **Notebooks**: personal diary + AI-logged dev diary (repo fixes, tools installed, bloopers) + abridged daily news digest from aiwatcher — dashboard cards + `/notebooks` page, `vla_diary` MCP tool

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

Claude Desktop: download `vla-mcp.mcpb` + `install.ps1` from
[releases/latest](https://github.com/sandraschi/vla-mcp/releases/latest/download/install.ps1)
and run `install.ps1` — or use `uvx vla-mcp` for other clients.

## What you can do

> "Run vla_status and give me a scenario brief for Raspbot + VRoid training in a cluttered room."

> "Segment this telemetry into event joints and ingest as a dataset episode."

> "Dry-run DMuon co-training on shard train_001."

## The models, in plain words

This bridge exists to feed training data to four open-source projects. Short version of each (verified Oct 2026; details live in the webapp Help tab under Models):

| Model | What it is | From whom | Open? | How fresh | Rivals | What we use it for |
|-------|-----------|-----------|-------|-----------|--------|-------------------|
| **Wall-OSS-0.5** | 4B robot brain: camera images + text command in, motor commands out. Runs on real robots with no extra training | X Square Robot, Shenzhen ([wall-x](https://github.com/X-Square-Robot/wall-x), paper arXiv 2605.30877) | Yes: code, weights ([HF](https://huggingface.co/x-square-robot/wall-oss-0.5)), GPU ops, docs | May 2026 (+ June stack update) | Open: pi0, OpenVLA, RDT-1B, SmolVLA, Octo. Closed: RT-2, Gemini Robotics | The big brain we prepare (`vla_wall`) and fine-tune toward |
| **WALL-WM** | World action model: imagines future video of the motion and learns from meaningful steps (reach, grasp, lift), not fixed chunks | Same X Square team ([wall-wm](https://github.com/X-Square-Robot/wall-wm), paper arXiv 2606.01955; video half reuses Alibaba's open Wan model) | Yes: paper + code open | May 2026 | Chunk-based world-action models (V-JEPA Policy line) | The event-joint idea behind `vla_events` / `vla_world_model` |
| **DMuon** | Distributed Muon optimizer: trains across GPUs almost as cheaply as AdamW, ~30% faster embodied training | X Square training team ([dmuon](https://github.com/X-Square-Robot/dmuon), paper arXiv 2606.27153) | Open source (check repo license) | June-July 2026 | AdamW, Moonshot's ZeRO-1 distributed Muon | The optimizer our co-training launches with (`vla_training`, dry-run first) |
| **X-VLA** | Tiny 0.9B open robot brain that matches 3B pi0 via a 9M adapter | Tsinghua AIR + Shanghai AI Lab + Peking U (paper arXiv 2510.10274, ICLR 2026, [site](https://thu-air-dream.github.io/X-VLA)) | Fully open: data, code, params | Oct 2025 | pi0-3B (the baseline it matches) | The small brain for edge & bimanual robots (`vla_xvla`: `raspbot`, `boomy`, `saschibot`, `nori_a3`, `isaac_twin`) |
| **SmolVLA (450M)** | Ultra-compact 450M asynchronous flow-matching VLA (`>30–50 Hz`) native to LeRobot & SO-101 Feetech arms | Hugging Face LeRobot (`lerobot/smolvla_base`) | Open weights & code | 2025–2026 | OpenVLA, Octo | High-rate local bimanual reflex policy for `saschibot` and `nori_a3` (`vla_weights` key `smolvla`) |
| **pi0.5 / pi0-FAST** | Open-world mobile manipulation VLA with DCT frequency-space action tokenization (`5x` faster training) | Physical Intelligence (`openpi` / `lerobot/pi05_base`) | Open weights & code | 2025–2026 | RT-2, Wall-OSS-0.5 | Whole-body wheeled base + telescopic lift + bimanual manipulation (`vla_weights` key `pi0.5-fast`) |
| **Isaac GR00T N1.5** | 3B cross-embodiment dual-system (VLM System 2 + Flow DiT System 1) foundation model | NVIDIA (`nvidia/GR00T-N1.5-3B`) | Open weights | 2025–2026 | pi0.5, Wall-OSS | Sim-to-real Isaac Lab bimanual + waist/lift fine-tuning on RTX 4090 (`vla_weights` key `gr00t-n1.5`) |

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
