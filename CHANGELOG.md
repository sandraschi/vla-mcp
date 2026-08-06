# Changelog

## [0.3.1b1] - 2026-08-06

### Added
- **Notebooks** (personal / dev / news diaries):
  - `vla_diary` MCP portmanteau — `log` (repo_fix, tool_install, blooper,
    decision, note), `list`, `get`, `delete` (confirm=True), `news`, `status`
  - SQLite store (`{VLA_DATASET_ROOT}/notebooks/notebooks.sqlite3`, WAL,
    500-entry cap per notebook, auto-migration for the `metrics` column)
  - Agent conventions: `repo:{name}` tags, `decision` category,
    `metrics` JSON gate evidence
  - REST: `/api/v1/notebooks`, `/api/v1/notebooks/{name}/entries`
    (GET/POST/DELETE), `/api/v1/notebooks/news/digest`
  - News diary pulls the last 24h from aiwatcher `/api/items` (top 10,
    abridged) — requires `VLA_AIWATCHER_BASE_URL`
  - Webapp: `/notebooks` page (3 tabs, composer, delete, digest button) +
    dashboard notebook cards; CORS now allows DELETE
- `fetch_fleet_items()` in `integrations/aiwatcher.py` (pull direction)

### Fixed
- Pre-existing tsc gate errors: WeightsPage response generic,
  missing `vite/client` types reference

## [0.3.0] - 2026-05-31

- Initial scaffold: Wall-OSS-0.5 / WALL-WM / DMuon / X-VLA prep tools,
  event segmentation, dataset registry, fleet bridge, pipeline runner,
  Vite webapp (Dashboard, Dataset, Pipeline, Training, Weights, Fleet,
  Tools, Help, Status).
