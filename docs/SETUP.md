# Setup - vla-mcp

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Optional: CUDA GPU for upstream wall-x jobs (not required for MCP smoke tests)

## Install

```powershell
Set-Location D:\Dev\repos\vla-mcp
uv sync --extra dev
```

## Upstream wall-x

```powershell
git clone https://github.com/X-Square-Robot/wall-x D:\Dev\repos\external\wall-x
$env:VLA_WALL_X_ROOT = "D:\Dev\repos\external\wall-x"
```

## Run

```powershell
# Full stack
.\start.bat

# Backend only
uv run uvicorn vla_mcp.server:app --host 127.0.0.1 --port 11024

# Stdio MCP (Cursor / Claude Desktop)
uv run python -m vla_mcp.server --stdio
```

## Fleet peer URLs

```powershell
$env:VLA_WORLDLABS_MCP_URL = "http://127.0.0.1:10865"
$env:VLA_ROBOTICS_MCP_URL = "http://127.0.0.1:10892"
$env:VLA_AVATAR_MCP_URL = "http://127.0.0.1:10793"
```

## Test

```powershell
uv run pytest tests -q
just test
```
