# vla-mcp Agent Context

FastMCP 3.2 bridge for Vision-Language-Action: Wall-OSS-0.5, WALL-WM (Wan), DMuon, fleet simulation loops.

## Quick ref

```powershell
uv sync --extra dev
uv run pytest tests -q
just serve          # backend :11024
just web            # frontend :11025
.\start.bat         # both
```

## Ports

| Service | Port |
|---------|------|
| Backend | 11024 |
| Frontend | 11025 |

## Tools

| Tool | Operations |
|------|------------|
| vla_wall | health, infer_prepare, finetune_prepare, list_tasks |
| vla_world_model | health, train_prepare, predict_prepare, event_vocab |
| vla_dataset | ingest_episode, list_episodes, export_shard, validate_multiview |
| vla_training | health, co_train_prepare, config_template |
| vla_fleet | bridge_status, scenario_brief, list_peers |
| vla_status | Full stack snapshot |
| vla_agentic_workflow | SEP-1577 planning |

## Env

See `.env.example`. Key: `VLA_WALL_X_ROOT`, `VLA_DATASET_ROOT`, fleet MCP URLs.

## Honesty

Prep/orchestration only until Phase 2 subprocess hooks land. Never fake GPU/upstream success.
