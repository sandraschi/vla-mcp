---
name: vla-expert
description: Vision-Language-Action co-training with Wall-OSS-0.5, WALL-WM, and fleet simulation loops
---

# VLA Expert Skill

## When to use

- User wants zero-shot robot control via Wall-OSS-0.5 (flow-matching VLA)
- User wants synthetic training data via WALL-WM world model on Wan video prior
- User orchestrates worldlabs-mcp + robotics-mcp + avatarops for multiview episodes
- User runs DMuon co-training locally on exported shards

## Workflow

1. `vla_status` - confirm upstream clones and dataset root
2. `vla_fleet(operation='scenario_brief')` - plan simulation boundary
3. Generate episodes with fleet MCPs; tag **events** (approaching, contact, lift, recovery)
4. `vla_dataset(operation='ingest_episode')` - register each run (include failures)
5. `vla_dataset(operation='export_shard')` - manifest for wall-x dataloaders
6. `vla_training(operation='co_train_prepare')` - DMuon + gradient-bridged co-train
7. `vla_wall(operation='infer_prepare')` - deploy to Raspbot / edge agents

## Upstream

- **wall-x**: https://github.com/X-Square-Robot/wall-x (Wall-OSS-0.5 + WALL-WM + DMuon)
- **X-VLA** (lightweight alt): Tsinghua 0.9B flow-matching VLA for PEFT on edge

## Env vars

| Variable | Purpose |
|----------|---------|
| VLA_WALL_X_ROOT | Clone of wall-x |
| VLA_WALL_WM_ROOT | WALL-WM subtree (defaults to wall-x root) |
| VLA_DMUON_ROOT | DMuon training scripts root |
| VLA_DATASET_ROOT | Local episode + export store |
| VLA_CHECKPOINT | Model weights path |
| VLA_WORLDLABS_MCP_URL | worldlabs-mcp HTTP base |
| VLA_ROBOTICS_MCP_URL | robotics-mcp HTTP base |
| VLA_AVATAR_MCP_URL | avatarops HTTP base |

## Honesty

This MCP **orchestrates and prepares**; it does not run GPU training unless upstream is wired.
Always report missing clones/checkpoints truthfully.
