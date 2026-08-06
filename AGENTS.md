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
| vla_diary | log (repo_fix/tool_install/blooper/decision/note), list, get, delete (confirm=True), news, status |

## Notebooks (vla_diary)

- SQLite at `{VLA_DATASET_ROOT}/notebooks/notebooks.sqlite3` (WAL, 500/notebook cap)
- **Agents MUST log dev work at session end**: `vla_diary(operation="log", ...)` —
  tags carry `repo:{name}`, `metrics` carries gate evidence (tests_passed, build_ok)
- News digest pulls aiwatcher `/api/items` — needs `VLA_AIWATCHER_BASE_URL`
- REST: `/api/v1/notebooks` (dashboard cards + `/notebooks` page)

DMuon launch requires `confirm=True`. HF download needs valid repo ids + optional HF token.

## Docs

README.md (user) · INSTALL.md · docs/TOOLS.md · docs/CONFIGURATION.md
