# vla-mcp

FastMCP 3.2 bridge for **Vision-Language-Action (VLA)** — orchestrates [X Square wall-x](https://github.com/X-Square-Robot/wall-x) (**Wall-OSS-0.5**, **WALL-WM**, **DMuon**) with fleet peers **worldlabs-mcp**, **robotics-mcp**, and **avatarops** for closed-loop synthetic training.

Replaces ad-hoc ROS glue with event-grounded trajectory export and honest upstream subprocess boundaries.

## Quick start

```powershell
cd D:\Dev\repos\vla-mcp
uv sync --extra dev
uv run pytest tests -q
.\start.bat
```

| Service | Port |
|---------|------|
| Backend (FastAPI + MCP HTTP `/mcp`) | 11024 |
| Frontend (Vite dashboard) | 11025 |

## MCP tools

| Tool | Purpose |
|------|---------|
| `vla_status` | Wall-OSS, WALL-WM, DMuon, dataset snapshot |
| `vla_wall` | Wall-OSS-0.5 infer/finetune prep |
| `vla_world_model` | WALL-WM train/predict + event vocab |
| `vla_dataset` | Ingest/list/export multiview episodes |
| `vla_training` | DMuon co-training prep |
| `vla_fleet` | worldlabs / robotics / avatar scenario brief |
| `vla_agentic_workflow` | Multi-step VLA session planning |

## Configuration

Copy `.env.example` to `.env` or set:

```powershell
$env:VLA_WALL_X_ROOT = "D:\Dev\repos\external\wall-x"
$env:VLA_DATASET_ROOT = "$env:TEMP\vla_mcp_data"
```

See [docs/SETUP.md](docs/SETUP.md) and [docs/PRD.md](docs/PRD.md).

## Fleet standards

Built per [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs): FastMCP 3.2, portmanteau tools, Prefab status cards, skills, dual transport, uv + justfile.

## License

MIT
