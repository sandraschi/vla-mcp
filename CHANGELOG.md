# Changelog

## [Unreleased] - 2026-10-25 assfix
### Fixed
- MCPB `mcpb/manifest.json` `${PWD}` → `${__dirname}` (bundle starts on real installs).
- CORS: explicit Tauri origins + LAN/Tailscale `allow_origin_regex`; HTTP transport now serves
  the combined FastAPI app (CORS + REST + /mcp) instead of bare `run_http_async`.
- Webapp `api.ts`: same-origin relative by default, absolute backend only behind Tauri gate.
- Added `vla_shutdown` MCP tool + `POST /api/shutdown` (orderly 500 ms exit).
- `.env.example`: repo-machine `D:\Dev\repos\...` defaults cleared (code falls back to `%TEMP%\vla_mcp_data`).
- Ruff: dropped `S110`/`S112` silences (fixed real `except: pass` in pipeline_runner), enabled `T20`; added `fmt` recipe.
- Standards files: `.pre-commit-config.yaml`, `.gitattributes`, `.cursorrules`, `.windsurfrules`,
  copilot instructions, Claude-Code hook, opencode skill, `docs/ONBOARDING.md`, `scripts/pre-commit-biome.ps1`.
- `.gitignore`: `reports/`, `*.mcpb`, `*.bak.*`; `.mcpbignore`: `webapp/`, `data/`, `*.bak.*`.
- README: Claude Desktop `.mcpb` + `install.ps1` one-liner.

### Fixed (deferred round, 2026-10-25)
- Tool docstrings fleet-wide: `Annotated[..., Field(...)]` params, `## Return Format` +
  `## Examples` on all 16 tools; `vla_diary` too. `vla_shutdown` REST-blocked (was callable
  without confirm via generic control endpoint).
- Backend: `GET /api/skills`, `/api/llm/*` proxy (discover/providers/models/chat/stream/onboarding),
  `GET /api/v1/diagnostics`. `run_sse_async` dead call removed (FastMCP 3.x has no SSE).
- Webapp catch-them-all: Chat (skill-first, 4+1 personalities, localStorage, export/clear),
  Settings (provider cards, model dropdown, Test, onboarding facts), Inbox, Logs, Skills pages;
  red under-hero onboarding cue (`data-testid="onboarding-cue"`); `/api` same-origin + Tauri gate.
- Gates: pyright 0 errors (fixed Prefab `css_class`, `run_sse_async`, Optional member access);
  pytest-cov threshold 55 (actual 56); Biome clean (`biome.json`, `biome:ci`/`check` scripts,
  exhaustive-deps + key fixes); e2e scaffold (playwright config + 3 smoke specs, all passing).
- CI: push/PR triggers, node 22, jobs test (ruff/format/pyright/pytest) + web (biome/tsc/build)
  + e2e (playwright). Release v0.3.1b1 now carries `.mcpb` + `install.ps1` assets.
- NSIS: fleet `mcp-clients.nsh` vendored + registered (NOREG cleared); `native/build.ps1`
  `$envSrc` crash + stray-flag syntax error fixed; MCPB audit `clean`, bundle packed +
  smoke-launched (85 KB).

### Fixed (round 3, 2026-10-25 — all remaining deferreds)
- Discord `fleet-vla`: channel existed with 5 stale pins; posted 2 fresh template posts
  (humans + agents), unpinned the 5 superseded, pinned the 2 new (exactly 2 pins).
- Annotations `READ_ONLY`/`MUTATING`/`DESTRUCTIVE` on all 16 tools + `vla_diary`;
  `output_schema` dialogic envelope on all dict-returning tools.
- `src/vla_mcp/errors.py`: `_error_response()` (logger.exception auto-log) used on every
  error path; `_wrap()` normalizes engine results into the envelope (no input mutation).
- `just e2e` + `just gates-green` recipes; `manifest.json` tools list gains `vla_shutdown`.
- Webapp: Zustand `store/llm` (provider/model/detected/gpu) wired into Chat + Settings
  (localStorage persistence kept); Tauri `backend-status` listener + HTTP-poll fallback
  hook with sidebar dot + Restart Backend (invokes sidecar `start_backend` under Tauri).
- Apps Hub: backend `GET /api/fleet/apps` (known peers + experimental extras) + Apps page
  (search, Experimental section) + nav.
- All 16 pages carry root `data-testid`; Dataset (search/sort/paginate/count), Tools
  (search/count), Weights (filter/count), Inbox (search/count) leporello-complete;
  loading/empty/error + retry states everywhere data is fetched.
- Type scale pass: no `text-xs` on UI text (kept in `<pre>`/code), `text-gray-500/600`
  body text brightened.
- Deleted 7 stale `.bak` files; added `renovate.json` (fleet standard: stabilityDays 3,
  Monday schedule, GH Actions automerge).

### Fixed (round 4, 2026-10-25 — "fix all" remainder)
- Discord `fleet-vla`: posted fresh humans/agents pair, unpinned 5 superseded, pinned 2.
- `just e2e` + `just gates-green`; `manifest.json` + `mcpb/manifest.json` tool lists
  accurate (incl. `vla_shutdown`); `.agents/skills` injection; `bootstrap` installs
  pre-commit hook (hook materialized); `actionlint` clean; JSON schemas validated.
- Server log ring buffer (`logbuffer.py`, 500 rec) + `GET /api/logs` (level/text filter).
- Logger modal (filter/search/export/close, Ctrl+L, Esc) + backend dot + Restart Backend
  (invokes sidecar `start_backend` under Tauri, re-probe in browser) + zoom % indicator
  + Ctrl+0 reset; Ctrl+H goes to Help, Ctrl+K focuses page search.
- MOCK-until-onboarded KPI cards with MOCK badges (clear on first live status);
  GPU opportunity prompt (`nvidia-smi` presence + no local LLM) in onboarding + Settings.
- 6 new endpoint tests (shutdown blocked, skills, fleet/apps, onboarding, logs,
  diagnostics); pytest 60 passed, coverage 58.7%; e2e 3/3 on final tree.
- Re-packed 85 KB bundle + re-uploaded release assets (current code).

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
