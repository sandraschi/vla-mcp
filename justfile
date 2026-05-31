set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]

export NAME := "VLA-MCP"
export DESC := "Vision-Language-Action bridge: Wall-OSS-0.5, WALL-WM, DMuon"
export VER := "0.1.0"
export PORT := "11024"
export HOST := "127.0.0.1"

default:
    @powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../mcp-central-docs/scripts/just-dashboard.ps1 -Path .

bootstrap:
    uv sync --extra dev
    Set-Location '{{justfile_directory()}}\webapp'
    if (Get-Command bun -ErrorAction SilentlyContinue) { bun install } else { cmd /c npm install }

serve port=PORT:
    uv run uvicorn vla_mcp.server:app --host {{HOST}} --port {{port}}

stdio:
    uv run python -m vla_mcp.server --stdio

web:
    Set-Location '{{justfile_directory()}}\webapp'
    if (Get-Command bun -ErrorAction SilentlyContinue) { bun run dev } else { npm run dev }

test:
    uv run pytest tests -q

lint:
    uv run ruff check src tests

fix:
    uv run ruff check src tests --fix
    uv run ruff format src tests

health:
    Invoke-RestMethod -Uri "http://127.0.0.1:11024/api/v1/status"
