---
name: vla-expert
description: Vision-Language-Action co-training with Wall-OSS-0.5, WALL-WM, X-VLA PEFT, and fleet simulation loops
---

# VLA Expert Skill

## Who this is for (routing)

- **Agents**: call the `vla_*` MCP tools directly with the operation names below.
  Always start with `vla_status` + `vla_pipeline_liveness`, and close dev work
  with `vla_diary(operation="log", category="repo_fix", tags=["repo:vla-mcp"])`.
- **Humans**: use the dashboard (ports 11024/11025) — Chat, Dataset, Pipeline,
  Training, Weights, Notebooks, Fleet pages — or ask the Chat page, which loads
  this skill as its system preprompt via `GET /api/skills`.

## When to use

- Zero-shot robot control via Wall-OSS-0.5 (flow-matching VLA)
- Synthetic training data via WALL-WM world model on the Wan video prior
- Lightweight edge agents via X-VLA 0.9B PEFT (Raspbot/Boomy)
- Fleet simulation loops (worldlabs-mcp + robotics-mcp + avatarops) with
  event-joint segmentation instead of equilong chunks
- DMuon co-training prep, dry-run, launch (confirm-gated), and job tracking

## Tool catalog (all portmanteau — pass `operation=`)

| Tool | Operations |
|------|-----------|
| `vla_status` | — (read-only snapshot: wall, world_model, dmuon, xvla, weights, episodes) |
| `vla_pipeline_liveness` | — (`stale_hours` default 168; supervisors/daily checks) |
| `vla_weights` | `list_models`, `local_status`, `download` |
| `vla_wall` | `health`, `infer_prepare`, `finetune_prepare`, `list_tasks`, `edge_prepare` |
| `vla_xvla` | `health`, `list_targets`, `peft_config_template`, `peft_prepare`, `edge_prepare`, `infer_prepare` |
| `vla_world_model` | `health`, `train_prepare`, `predict_prepare`, `event_vocab` |
| `vla_dataset` | `ingest_episode`, `segment_telemetry`, `list_episodes`, `export_shard`, `export_numpy_shard`, `validate_multiview` |
| `vla_events` | `segment`, `vocab` |
| `vla_training` | `health`, `co_train_prepare`, `config_template`, `introspect_train_args`, `launch_co_train` (confirm=True), `job_status`, `job_log`, `stop_job` |
| `vla_pipeline` | `describe`, `run` (live or simulate), `last_run` |
| `vla_fleet` | `bridge_status`, `scenario_brief`, `list_peers`, `call_peer` |
| `vla_world` | `describe`, `generate` (returns Marble viewer URL) |
| `vla_diary` | `log`, `list`, `get`, `delete` (confirm=True), `news`, `status`, `summary` |
| `vla_agentic_workflow` | multi-step planning (needs MCP host Context) |
| `vla_help` | `topic=` index: fleet_integration, api_keys, tools, configuration, troubleshooting |
| `vla_shutdown` | orderly self-termination (agents/fleet launcher) |
| `show_vla_status_card`, `show_pipeline_run_card` | Prefab in-chat cards |

REST mirror: `GET /api/v1/status`, `/api/v1/tools`, `/api/v1/dataset/episodes`,
`/api/v1/training/jobs[/{id}/log[/stream]]`, `/api/v1/pipeline/{last,run}`,
`/api/v1/notebooks`, `/api/capabilities`, `/api/skills`, `/api/v1/diagnostics`,
`/api/llm/{discover,providers,models,chat,chat/stream,onboarding}`.
`POST /api/shutdown` exits in ~500 ms. Mutating REST needs `X-VLA-Confirm: 1`.

## Workflow 1 — data-collection loop (simulation to shard)

```
vla_status()                                            # clones wired? dataset root?
vla_fleet(operation="scenario_brief")                   # room, agents, failure modes
# generate episodes with fleet MCPs; tag EVENTS: approaching, contact, lift, slide, recovery
vla_dataset(operation="segment_telemetry", source="boomy_b", telemetry=[...])
vla_dataset(operation="ingest_episode", source="boomy_b", events=[...])
vla_dataset(operation="export_numpy_shard", shard_name="train_001")
vla_training(operation="launch_co_train", dataset_shard="train_001", dry_run=True)
```

## Workflow 2 — zero-shot deploy on Raspbot

```
vla_wall(operation="health")                            # Wall-OSS-0.5 upstream present?
vla_wall(operation="infer_prepare", task_hint="pick up the red cube")
# too heavy for the edge box?
vla_xvla(operation="peft_config_template", target="raspbot", rank=8)
vla_xvla(operation="edge_prepare", target="raspbot")
```

## Workflow 3 — world-model rollout + diary close

```
vla_world_model(operation="event_vocab")                # approaching, contact, lift, slide, recovery
vla_world(operation="generate", prompt="cluttered workshop")   # Marble viewer URL
vla_world_model(operation="predict_prepare", horizon_steps=16)
vla_pipeline(operation="run", live=False)               # E2E dry run
vla_diary(operation="log", category="repo_fix", title="...", body="...",
          tags=["repo:vla-mcp"], metrics={"tests_passed": 54})
```

## Upstream

- **wall-x**: https://github.com/X-Square-Robot/wall-x (Wall-OSS-0.5 + WALL-WM + DMuon)
- **X-VLA** (lightweight alt): Tsinghua 0.9B flow-matching VLA for PEFT on edge

## Env vars

| Variable | Purpose |
|----------|---------|
| VLA_WALL_X_ROOT | Clone of wall-x |
| VLA_WALL_WM_ROOT | WALL-WM subtree (defaults to wall-x root) |
| VLA_DMUON_ROOT | DMuon training scripts root |
| VLA_XVLA_ROOT / VLA_XVLA_PEFT_DIR / VLA_XVLA_PEFT_ADAPTER | X-VLA weights + PEFT adapter |
| VLA_DATASET_ROOT | Local episode + export store (default `%TEMP%/vla_mcp_data`) |
| VLA_HF_CACHE_DIR | HF weights cache |
| VLA_HF_WALL_OSS_REPO / VLA_HF_WALL_WM_REPO / VLA_HF_XVLA_REPO | HF repo ids |
| VLA_CHECKPOINT | Model weights path |
| VLA_DEVICE / VLA_DMUON_VRAM_SHARDS | `cuda:0`, shard count |
| VLA_WORLDLABS_MCP_URL / VLA_ROBOTICS_MCP_URL / VLA_AVATAR_MCP_URL / VLA_YAHBOOM_MCP_URL | Fleet peer bases |
| VLA_AIWATCHER_BASE_URL / VLA_AIWATCHER_API_KEY | News digest + event push |
| VLA_MOUNT_FLEET_PROXIES / VLA_MCP_BRIDGE_URLS | MCP proxy federation (default off) |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `vla_status` shows upstream `not configured` | Set `VLA_WALL_X_ROOT` (etc.) to a real clone; prep tools still work without it |
| Peer `unreachable` in `bridge_status` | Start that fleet server; `live=False` simulates meanwhile |
| `download` 401/404 | Set `HF_TOKEN`, check repo id (`vla_weights(operation="list_models")`) |
| `launch_co_train` refuses | Pass `confirm=True` (and `dry_run=True` first); needs `VLA_DMUON_ROOT` |
| Chat says provider unreachable | Start Ollama (`ollama pull qwen3:8b`) or LM Studio; pick model in Settings |
| News digest empty | Set `VLA_AIWATCHER_BASE_URL` to aiwatcher-mcp `/api/items` |

## Honesty

This MCP **orchestrates and prepares**; it does not run GPU training unless
upstream is wired. Always report missing clones/checkpoints truthfully —
`vla_pipeline_liveness` exists so supervisors can see the gaps too.
