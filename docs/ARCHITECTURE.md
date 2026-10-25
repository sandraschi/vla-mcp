# Architecture - vla-mcp

## Layers

```
src/vla_mcp/
  server.py           FastMCP + FastAPI mount /mcp (16 tools + 2 Prefab cards)
  config.py           VLA_* environment
  transport.py        stdio / HTTP (combined FastAPI app w/ CORS)
  web.py              REST /api/* (skills, fleet/apps, logs, llm proxy, diagnostics)
  errors.py           _error_response / _wrap dialogic envelope
  logbuffer.py        In-memory ring log (Logger modal source)
  rest_policy.py      REST allow/block lists (terminal ops blocked from generic control)
  pipeline_liveness.py Bounded probes (6s/peer, 10s gather, 20s overall, 60s cache)
  engine/
    wall_runner.py    Wall-OSS-0.5 bridge
    world_model_runner.py  WALL-WM bridge
    xvla_adapter.py   X-VLA edge adapter (PEFT)
    dmuon_runner.py   DMuon co-training bridge
    dataset_store.py  Episode JSON registry + export shards
    event_segmenter.py WALL-WM style event joints
    fleet_bridge.py   Bounded peer probes + scenario briefs + call_peer
    notebook_store.py Diary SQLite (dev/personal/news)
    pipeline_runner.py End-to-end loop + provenance
  tools/
    prefab.py         show_vla_status_card, show_pipeline_run_card
    diary.py          vla_diary portmanteau
    help.py           vla_help topics
  skills/vla-expert/ Agent skill resource
webapp/               React 19 + Tailwind (16 pages: Dashboard hero, Chat, Settings,
                      Inbox, Logs, Skills, Apps Hub, Dataset, Pipeline, Training,
                      Weights, Notebooks, Fleet, Tools, Help, Status) + e2e smoke
native/              Tauri 2 root (sidecar backend manager, NSIS client registration)
```

## Data flow

1. **Simulation boundary** - Fleet MCPs produce multiview video + actions tagged with semantic events.
2. **vla_dataset** - Episodes stored as JSON under `{VLA_DATASET_ROOT}/episodes/`; index at `index.json`.
3. **export_numpy_shard** - Manifest JSON + `.npy` actions for wall-x dataloaders.
4. **vla_training** - Points DMuon config at shards; launches only with `confirm=True`.

## Probing (inbox + supervisors)

Peer probes are bounded: 2s per HTTP attempt, max 6s per peer, 10s total gather,
20s overall probe budget, 60s result cache. The Inbox page loads the fast
last-run row first and streams peer rows in, so a dead robot never blocks the UI.

## Ports (fleet registry)

| Port | Role |
|------|------|
| 11024 | Backend API + MCP HTTP |
| 11025 | Vite frontend |

Registered in `mcp-central-docs/operations/WEBAPP_PORTS.md`.

## Extension plan

- Phase 2: Subprocess wrappers for wall-x infer CLI — DONE (dry_run/confirm launch)
- Phase 3: MCP `create_proxy` federation to worldlabs/robotics/avatar — DONE (behind `VLA_MOUNT_FLEET_PROXIES`)
- Phase 4: Webapp training monitor + episode viewer — DONE (Training/Logs pages, Apps Hub)
- Phase 5: X-VLA lightweight edge adapter — DONE (`vla_xvla`, PEFT)
- Next: collect real teleoperation demos (LeRobot recording is the natural first workload)
