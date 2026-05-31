# Installing vla-mcp

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| Claude Desktop / Cursor | MCP host | [claude.ai/download](https://claude.ai/download) |
| Git | Clone repo | `winget install Git.Git` |
| Python + uv | Run server | `winget install astral-sh.uv` |
| Node.js | Web dashboard | `winget install OpenJS.NodeJS` |

> Windows: use [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/). macOS: `brew install uv node git`.

## Option A — From source (recommended)

```powershell
git clone https://github.com/sandraschi/vla-mcp
Set-Location vla-mcp
uv sync --extra dev
.\start.bat
```

Open http://127.0.0.1:11025

## Option B — Claude Desktop stdio

1. Clone and `uv sync` as above.
2. Clone upstream: `git clone https://github.com/X-Square-Robot/wall-x D:\Dev\repos\external\wall-x`
3. Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vla-mcp": {
      "command": "uv",
      "args": ["--directory", "D:\\Dev\\repos\\vla-mcp", "run", "python", "-m", "vla_mcp.server", "--stdio"],
      "env": {
        "PYTHONUNBUFFERED": "1",
        "VLA_WALL_X_ROOT": "D:\\Dev\\repos\\external\\wall-x"
      }
    }
  }
}
```

4. Restart Claude Desktop.

## Option C — HTTP MCP

Start backend: `uv run uvicorn vla_mcp.server:app --host 127.0.0.1 --port 11024`

MCP endpoint: `http://127.0.0.1:11024/mcp`

## Upstream wall-x + weights

```powershell
git clone https://github.com/X-Square-Robot/wall-x D:\Dev\repos\external\wall-x
$env:VLA_WALL_X_ROOT = "D:\Dev\repos\external\wall-x"
```

Download weights via MCP tool `vla_weights(operation='download', model_key='wall-oss-0.5')` or set `VLA_HF_*_REPO` if IDs differ on Hugging Face.

## Verify installation

In Claude or Cursor:

> Call vla_status and list registered tools.

Expected: `success: true`, wall/world_model/dmuon health blocks, 9+ tools.

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).
