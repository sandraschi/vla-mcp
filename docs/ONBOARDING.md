# Onboarding — vla-mcp

> **Start here:** this server bridges X Square wall-x (Wall-OSS-0.5, WALL-WM, DMuon)
> with your fleet for event-joint training prep. No robots needed to explore it.

## 1. What you need
- Windows 10/11, Python 3.12+, [uv](https://docs.astral.dev/uv/)
- Optional: CUDA GPU, a clone of https://github.com/X-Square-Robot/wall-x,
  Hugging Face token (only for gated weights), fleet peers
  (worldlabs-mcp :10865, robotics-mcp :10706, avatarops :10793).

## 2. Install (2 min)
```powershell
git clone https://github.com/sandraschi/vla-mcp
cd vla-mcp
uv sync --extra dev
.\start.bat
```
Open http://127.0.0.1:11025/ — backend health: http://127.0.0.1:11024/api/v1/status.

## 3. Sanity check (no hardware)
- MCP: `vla_status` → wall/world_model/dmuon/xvla health + episode count.
- Supervisors: `vla_pipeline_liveness` → stale loops + peer reachability.
- Dry run: `vla_pipeline(operation="run", live=false)` then
  `vla_training(operation="launch_co_train", confirm=false)` (dry-run only).

## 4. Pitfalls
- `VLA_DATASET_ROOT`/`VLA_HF_CACHE_DIR` default to `%TEMP%\vla_mcp_data` — set them
  explicitly for real datasets (see `.env.example`).
- DMuon `launch_co_train` requires `confirm=True` and never runs unasked.
- News digest needs `VLA_AIWATCHER_BASE_URL` (aiwatcher-mcp /api/items).

## 5. Mock-until-onboarded
Until `vla_status` returns healthy at least once, the dashboard shows MOCK sample
KPIs/cards (badged MOCK) so the UI is explorable without wall-x or HF access.
Live data replaces them after the first successful status probe.
