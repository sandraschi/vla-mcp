# Product Requirements Document - vla-mcp

**Version:** 0.3.0  
**Last updated:** 2026-05-31  
**Upstream:** https://github.com/X-Square-Robot/wall-x  
**Fleet standard:** mcp-central-docs SOTA 3.2

## Overview

vla-mcp is a **FastMCP 3.2 orchestration server** that connects the Chinese open-weight spatial stack (Wall-OSS-0.5 VLA + WALL-WM world model + DMuon optimizer) to Sandra's local MCP fleet for synthetic data generation and co-training prep.

It does **not** reimplement VLA or world models in Python. It validates upstream clones, registers event-grounded trajectories, probes fleet peers, and returns honest prep guidance.

## Problem

- Western VLA stacks often need heavy per-gripper fine-tuning; Wall-OSS-0.5 targets zero-shot via flow-matching action supervision.
- WALL-WM needs **event-segmented** multiview video + action data, not chunk-only velocity dumps.
- Fleet already has worldlabs (rooms), robotics (Raspbot), avatar (VRoid) - no unified VLA bridge existed.

## Architecture

```
[worldlabs-mcp] --> 3D rooms + camera rigs
[robotics-mcp]  --> Raspbot physics episodes
[avatarops]     --> VRoid interaction episodes
        |
        v  vla_dataset (event-grounded export)
[vla-mcp] --> wall-x / DMuon co-training prep
        |
        v
Wall-OSS-0.5 (edge infer) + WALL-WM (sim rollouts)
```

## Functional requirements (scaffold phase)

| ID | Requirement | Status |
|----|-------------|--------|
| REQ-01 | Portmanteau MCP tools (wall, wm, dataset, training, fleet) | Done |
| REQ-02 | Local episode registry under VLA_DATASET_ROOT | Done |
| REQ-03 | Fleet peer probe + scenario_brief | Done |
| REQ-04 | Dual transport stdio + HTTP on 11024 | Done |
| REQ-05 | Vite dashboard on 11025 | Done |
| REQ-06 | Skills + prompts + Prefab status card | Done |
| REQ-07 | Wire real wall-x train/infer subprocess hooks | Done (DMuon launch + dry_run) |
| REQ-08 | MCP bridge proxy to worldlabs/robotics/avatar | Done |
| REQ-09 | numpy shard writer for DMuon | Done |
| REQ-10 | X-VLA 0.9B PEFT path for edge secondary agents | Done (`vla_xvla`, `vla_wall edge_prepare`) |
| REQ-11 | HF weight download helper | Done |
| REQ-12 | Event telemetry segmenter | Done |
| REQ-14 | E2E pipeline (fleet → ingest → export → DMuon dry_run) | Done (`vla_pipeline`) |

## Non-goals (v0.1)

- Shipping Wan or Wall-OSS weights in-repo
- Replacing robotics-mcp low-level motor control
- Fake GPU success when CUDA/upstream missing

## Success metrics

| Metric | Target |
|--------|--------|
| Cold start | `uv sync` + pytest green without GPU |
| Honesty | Missing upstream returns recovery_options |
| Fleet loop | scenario_brief lists 7+ orchestration steps |
| Docs | PRD + ARCHITECTURE + SKILL aligned with wall-x |

## Related repos

- wall-x: Wall-OSS-0.5 + WALL-WM + DMuon
- worldlabs-mcp: Marble / spatial worlds
- robotics-mcp: Raspbot + sim fleet
- avatarops: VRoid dynamics
- lewm-mcp: prior art for world-model MCP bridge pattern
