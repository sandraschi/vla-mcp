# vla-mcp Agent Context

FastMCP 3.2 VLA bridge (v0.2.0): Wall-OSS-0.5, WALL-WM, DMuon, HF weights, event joints.

## Quick ref

```powershell
uv sync --extra dev
uv run pytest tests -q
just serve    # :11024
just web      # :11025
.\start.bat
```

GitHub: https://github.com/sandraschi/vla-mcp

## Phase 2 tools

| Tool | New ops |
|------|---------|
| vla_weights | list_models, download, local_status |
| vla_events | segment, vocab |
| vla_dataset | segment_telemetry, export_numpy_shard |
| vla_training | launch_co_train, job_status, stop_job |
| vla_fleet | call_peer |

DMuon launch requires `confirm=True`. HF download needs valid repo ids + optional HF token.

## Docs

README.md (user) · INSTALL.md · docs/TOOLS.md · docs/CONFIGURATION.md
