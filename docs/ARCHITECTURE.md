# Architecture - vla-mcp

## Layers

```
src/vla_mcp/
  server.py           FastMCP + FastAPI mount /mcp
  config.py           VLA_* environment
  transport.py        stdio / HTTP
  web.py              REST /api/v1/*
  engine/
    wall_runner.py    Wall-OSS-0.5 bridge
    world_model_runner.py  WALL-WM bridge
    dmuon_runner.py   DMuon co-training bridge
    dataset_store.py  Episode JSON registry + export shards
    fleet_bridge.py   HTTP probes + scenario briefs
  tools/prefab.py     show_vla_status_card
  skills/vla-expert/  Agent skill resource
```

## Data flow

1. **Simulation boundary** - Fleet MCPs produce multiview video + actions tagged with semantic events.
2. **vla_dataset** - Episodes stored as JSON under `{VLA_DATASET_ROOT}/episodes/`; index at `index.json`.
3. **export_shard** - Manifest JSON for wall-x dataloaders (Phase 2: numpy/zarr/LanceDB).
4. **vla_training** - Points DMuon config at shards; does not spawn training without explicit future hook.

## Ports (fleet registry)

| Port | Role |
|------|------|
| 11024 | Backend API + MCP HTTP |
| 11025 | Vite frontend |

Register in `mcp-central-docs/operations/WEBAPP_PORTS.md` on fleet promotion.

## Extension plan

- Phase 2: Subprocess wrappers for wall-x infer CLI
- Phase 3: MCP `create_proxy` federation to worldlabs/robotics/avatar
- Phase 4: Webapp training monitor + episode viewer
- Phase 5: X-VLA lightweight edge adapter
