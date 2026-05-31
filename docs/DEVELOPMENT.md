# Development

## Tools required

```powershell
winget install astral-sh.uv
winget install Git.Git
winget install OpenJS.NodeJS
winget install Casey.Just
```

## Setup

```powershell
git clone https://github.com/sandraschi/vla-mcp
Set-Location vla-mcp
uv sync --extra dev
Set-Location webapp
npm install
```

## Common tasks

```powershell
just test
just lint
just serve
just web
.\start.bat
```

## Tests

```powershell
uv run pytest tests -q
```

No GPU or wall-x clone required for smoke tests.

## Standards

Fleet norms: `D:\Dev\repos\mcp-central-docs\standards\` (FastMCP 3.2, portmanteau tools, WEBAPP_PORTS 11024/11025).

## Phase 2 modules

| Module | Role |
|--------|------|
| `engine/hf_weights.py` | HF snapshot_download |
| `engine/event_segmenter.py` | Event joint tagging |
| `engine/dmuon_runner.py` | Subprocess co-train + jobs |
| `engine/fleet_bridge.py` | REST call_peer |
