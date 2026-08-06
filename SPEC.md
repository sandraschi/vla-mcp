# SPEC — Notebooks: Personal / Dev / News Diaries

**Status**: Draft — pending approval
**Repo**: vla-mcp
**Owner**: Sandra Schipal
**Date**: 2026-08-06

---

## 1. Goal

Add three persistent notebooks to vla-mcp, shown with medium prominence on the
dashboard:

| Notebook | Writer | Content |
|----------|--------|---------|
| **Personal diary** | Sandra (manual) | Free-form life log, typed in the UI |
| **Dev diary** | AI/agents + Sandra | Repo fixes, tools installed, bloopers — logged via MCP tool at session end, or typed |
| **News diary** | AI (digest) | Abridged daily news digest pulled from **aiwatcher-mcp** |

## 2. Why vla-mcp?

The webapp and its `{dataset_root}` data dir already exist; the aiwatcher
integration (push) is already wired via `VLA_AIWATCHER_BASE_URL`. The notebooks
make the dashboard a daily companion surface (diary + dev log + news) rather
than only a training-status panel.

## 3. Requirements

### 3.1 Storage — `engine/notebook_store.py`

**SQLite** (stdlib `sqlite3`, no new dependency) — decided 2026-08-06 over the
JSON-file pattern: one table, WAL mode, indexed queries, no rewrite-on-append.

- DB path: `{dataset_root}/notebooks/notebooks.sqlite3`
  (`VLA_DATASET_ROOT` default `%TEMP%\vla_mcp_data`)
- Connection: open per operation (cheap at this scale), `PRAGMA journal_mode=WAL`
  set on each open; no shared state across threads
- Schema (`CREATE TABLE IF NOT EXISTS`):

```sql
CREATE TABLE IF NOT EXISTS notebook_entries (
  id         TEXT PRIMARY KEY,
  notebook   TEXT NOT NULL CHECK (notebook IN ('personal','dev','news')),
  category   TEXT NOT NULL DEFAULT 'note',
  title      TEXT NOT NULL,
  body       TEXT NOT NULL,
  author     TEXT NOT NULL DEFAULT 'sandra',
  tags       TEXT NOT NULL DEFAULT '[]',      -- JSON array; repo:{name} convention
  metrics    TEXT NOT NULL DEFAULT '{}',      -- JSON dict, gate evidence
  created_at TEXT NOT NULL,                   -- ISO8601 UTC
  updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_nb_created ON notebook_entries(notebook, created_at DESC);
```

- Entry shape (API surface):

```json
{
  "id": "2026-08-06T14:03:22Z-abc123",
  "notebook": "dev",
  "category": "repo_fix | tool_install | blooper | note | digest",
  "title": "short headline",
  "body": "markdown body",
  "author": "agent:opencode | sandra | aiwatcher",
  "tags": ["vla-mcp", "ruff"],
  "created_at": "ISO8601 UTC",
  "updated_at": "ISO8601 UTC | null"
}
```

- Store methods: `add_entry`, `list_entries(notebook, limit, offset, category)`,
  `get_entry`, `update_entry`, `delete_entry`, `latest(notebook)`, `counts()`.
- Cap: keep newest 500 entries per notebook (delete oldest on insert over cap,
  single transaction).

### 3.2 REST API (in `web.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/notebooks` | GET | List notebooks + latest entry + entry count (for dashboard cards) |
| `/api/v1/notebooks/{name}/entries` | GET | Paginated entries (`limit`, `offset`, `category`) |
| `/api/v1/notebooks/{name}/entries` | POST | Add entry `{category, title, body, tags}`; `author` defaults `"sandra"` for personal, `"sandra"` otherwise |
| `/api/v1/notebooks/{name}/entries/{id}` | DELETE | Remove entry |
| `/api/v1/notebooks/{name}/entries/{id}` | PATCH | Edit title/body (optional v1.1) |
| `/api/v1/notebooks/news/digest` | POST | Trigger aiwatcher pull + digest save (manual button) |

Validation: `notebook` must be one of `personal|dev|news`; body 1–20k chars;
title 1–200 chars. 422 on violation.

### 3.3 MCP tool — `vla_diary` (portmanteau, in `tools/diary.py`)

Registers as one tool with `operation` enum; FastMCP 3.2 `@mcp.tool()`,
`version="0.1.0"`, `annotations` READ_ONLY for list/get, MUTATING for log/delete.
Registered in `server.py` alongside the other `vla_*` tools.

| operation | notebook | category | Purpose |
|-----------|----------|----------|---------|
| `log` | dev (default) or personal | repo_fix / tool_install / blooper / **decision** / note | **Primary agent hook** — call at session end. Accepts optional `author` (default `agent:opencode`), `tags`, `metrics` |
| `list` | any | — | Recent entries |
| `get` | any | — | Single entry by id |
| `delete` | any | — | Remove entry (requires `confirm=True`) |
| `news` | news | digest | Pull aiwatcher items + save digest |
| `status` | — | — | Entry counts per notebook |

**Agent conventions (baked into the tool docstring):**

- **Repo tags**: entries involving a repo MUST carry a `repo:{name}` tag
  (e.g. `tags=["repo:vla-mcp"]`) so the diary is filterable per repo —
  "what happened in calibre-mcp" is a tag query.
- **`decision` category**: spec/architecture choices that changed direction
  ("user said why not sqlite -> storage moved to SQLite").
- **`metrics`**: structured gate evidence as JSON — `{"tests_passed": 51,
  "build_ok": true}` — data, not prose.

Agent guidance in docstring: "Log dev work at the end of every session: which
repos were fixed, which tools were installed, and any bloopers."

### 3.4 News diary — aiwatcher source

- Reuse config: `VLA_AIWATCHER_BASE_URL` (existing field `aiwatcher_base_url`).
- Pull: `GET {base}/api/items?hours=24&limit=50` (aiwatcher REST, same host as
  the existing `push_fleet_event`).
- **Abridging**: aiwatcher already produces digest summaries on items; the news
  entry stores the top 10 items as `- [title](url): summary` lines. v1 does
  **not** add an LLM dependency to vla-mcp.
- Entry: `category="digest"`, `title="News digest 2026-08-06"`, `body=abridged markdown`.
- Unreachable aiwatcher → explicit error (no fake digest): `success: false`,
  `error_type: "upstream_unreachable"`, recovery hint (start aiwatcher-mcp :10946).
- No scheduler in v1 — digest created on demand (MCP op, REST button).

### 3.5 Webapp

- **New page** `/notebooks` (route in `App.tsx`, sidebar entry in `AppLayout.tsx`
  with `BookOpen` icon, between Pipeline and Fleet).
- Page layout: three tabs (Personal / Dev / News), each with:
  - Entry composer (title + body textarea + category select for dev)
  - Entry list (reverse-chron, markdown body, delete button)
  - News tab: "Pull today's digest" button calling
    `POST /api/v1/notebooks/news/digest`
- **Dashboard (medium prominence)**: below the KPI cards, a "Notebooks" row of
  three compact cards (one per notebook) showing: name, latest entry title +
  snippet, entry count, and a link to `/notebooks`. `data-testid` on each card
  (`notebook-personal`, `notebook-dev`, `notebook-news`) and on the dashboard
  section (`dashboard-notebooks`).
- Dark theme, existing styling conventions (gray-900 cards, violet accents).

## 4. Non-goals (v1)

- No auth / multi-user
- No file/photo attachments
- No scheduled digest job (manual trigger only)
- No fleet-repo auto-scraping for dev entries (agents log explicitly)
- No LLM summarization inside vla-mcp (aiwatcher's digests are the abridger)

## 5. Files touched

| File | Change |
|------|--------|
| `src/vla_mcp/engine/notebook_store.py` | **new** — JSON store |
| `src/vla_mcp/tools/diary.py` | **new** — `vla_diary` MCP tool |
| `src/vla_mcp/tools/__init__.py` | import diary (currently empty) |
| `src/vla_mcp/server.py` | register `vla_diary` |
| `src/vla_mcp/web.py` | notebook REST routes |
| `src/vla_mcp/integrations/aiwatcher.py` | add `fetch_fleet_items()` (pull) |
| `webapp/src/pages/NotebooksPage.tsx` | **new** |
| `webapp/src/pages/Dashboard.tsx` | Notebooks cards section |
| `webapp/src/App.tsx` | route `/notebooks` |
| `webapp/src/components/AppLayout.tsx` | sidebar entry |
| `webapp/src/lib/api.ts` | typed helpers (if pattern requires) |
| `tests/test_notebook_store.py` + `tests/test_diary_tool.py` | **new** |
| `docs/TOOLS.md`, `README.md` | document `vla_diary` + notebooks |

## 6. Acceptance checklist

- [ ] `vla_diary` registers; `list` shows the 3 notebooks; `log` writes to dev
- [ ] POST /api/v1/notebooks/dev/entries persists and appears in GET
- [ ] News digest pulls real aiwatcher items; unreachable → structured error
- [ ] Dashboard shows 3 notebook cards with latest snippet; links work
- [ ] `/notebooks` page: all 3 tabs functional, composer saves, delete works
- [ ] `ruff check` + `pyright` + `pytest` green
- [ ] `just cua-webapp-test` nav walk includes Notebooks page

## 7. Decisions (2026-08-06)

| # | Question | Decision |
|---|----------|----------|
| 1 | `author` field on `log`? | **Yes** — optional, default `agent:opencode`; REST defaults `sandra` |
| 2 | Dashboard snippet length? | **140 chars** — the cards show the latest entry's title + first ~140 chars of body (question was about preview length; 140 is the standard card snippet) |
| 3 | Delete protection | **Yes** — MCP `delete` requires `confirm=True`; REST delete is instant (UI has its own confirm) |
| 4 | Storage backend | **SQLite** (single table, WAL) — see §3.1 |
| 5 | Agent ideas folded in | `decision` category, `repo:{name}` tag convention, `metrics` field — see §3.3 |
