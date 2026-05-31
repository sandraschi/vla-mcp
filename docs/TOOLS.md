# MCP Tool Reference

## vla_status

Read-only stack snapshot: Wall-OSS, WALL-WM, DMuon, HF cache, episode count.

## vla_weights

| Operation | Description |
|-----------|-------------|
| `list_models` | Catalog wall-oss-0.5, wall-wm, and x-vla |
| `local_status` | Cache paths (`model_key` optional) |
| `download` | HF snapshot_download (`model_key` required) |

## vla_wall

Wall-OSS-0.5 VLA: `health`, `infer_prepare`, `finetune_prepare`, `list_tasks`, `edge_prepare` (X-VLA edge checklist alias).

## vla_xvla

X-VLA 0.9B flow-matching VLA with PEFT for edge agents (Raspbot, Boomy, Pi5 car via yahboom-mcp):

| Operation | Description |
|-----------|-------------|
| `health` | Upstream root, HF cache, PEFT adapter paths |
| `list_targets` | Edge agent targets |
| `peft_config_template` | LoRA skeleton (`target`, `rank`) |
| `peft_prepare` | Write `peft_config.json` when `write=True` |
| `edge_prepare` | Full deployment checklist |
| `infer_prepare` | Edge inference prep (`task_hint` optional) |

## vla_world_model

WALL-WM: `health`, `train_prepare`, `predict_prepare`, `event_vocab`.

## vla_dataset

| Operation | Description |
|-----------|-------------|
| `ingest_episode` | Manual event tags + video paths (+ optional inline `actions`) |
| `segment_telemetry` | Auto event joints from telemetry rows |
| `list_episodes` | Paginated (`limit`, `offset`) |
| `export_shard` | JSON manifest |
| `export_numpy_shard` | Manifest + `.npy` actions |
| `validate_multiview` | Check video files exist |

Telemetry sample fields: `timestamp`, `velocity`, `contact_force`, `gripper_open`, `distance_to_target`, `collision_flag`, `slip_variance`.

## vla_events

`segment` (telemetry samples), `vocab` (event joint list).

## vla_pipeline

End-to-end closed loop (provenance in `VLA_DATASET_ROOT/logs/pipeline/`):

| Operation | Description |
|-----------|-------------|
| `describe` | Pipeline steps and live peer tool map |
| `run` | Full loop (`live=False` CI-safe; `live=True` probes fleet) |
| `last_run` | Latest provenance JSON |

REST: `POST /api/v1/pipeline/run` (requires `X-VLA-Confirm: 1`).

## vla_training

| Operation | Description |
|-----------|-------------|
| `co_train_prepare` | Validate upstream + shard |
| `config_template` | YAML skeleton |
| `introspect_train_args` | Parse upstream train script `--help` |
| `launch_co_train` | Subprocess (`confirm=True` to run, `dry_run=True` to preview) |
| `job_status` | List or get job by `job_id` |
| `job_log` | Tail job log (`job_id`, `log_offset`) |
| `stop_job` | Kill Windows job by `job_id` |

## vla_fleet

| Operation | Description |
|-----------|-------------|
| `list_peers` | Default URLs |
| `bridge_status` | HTTP health probes |
| `scenario_brief` | Closed-loop sim plan |
| `call_peer` | REST bridge (`peer`, `tool_name`, `arguments`) |

## vla_agentic_workflow

Multi-step planning with optional `ctx.sample`.

## show_vla_status_card

Prefab in-chat card (when `VLA_PREFAB_APPS=1`).

## Examples

```python
await vla_dataset(operation="segment_telemetry", source="raspbot_sim", telemetry=[...])
await vla_pipeline(operation="run", live=False, include_failures=True)
await vla_training(operation="launch_co_train", dry_run=True, dataset_shard="train_001")
await vla_xvla(operation="edge_prepare", target="raspbot")
await vla_fleet(operation="call_peer", peer="yahboom", tool_name="robotics_system", arguments={"operation": "status"})
```
