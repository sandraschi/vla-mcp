set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

export NAME := "VLA-MCP"
export DESC := "Vision-Language-Action bridge: Wall-OSS-0.5, WALL-WM, DMuon"
export VER := "0.3.0"
export PORT := "11024"
export HOST := "127.0.0.1"

default:
    @just --list

bootstrap:
    uv sync --extra dev; uv run pre-commit install; Set-Location '{{justfile_directory()}}\webapp'; if (Get-Command bun -ErrorAction SilentlyContinue) { bun install } else { cmd /c npm install }

serve port=PORT:
    uv run uvicorn vla_mcp.server:app --host {{HOST}} --port {{port}}

stdio:
    uv run python -m vla_mcp.server --stdio

web:
    Set-Location '{{justfile_directory()}}\webapp'; if (Get-Command bun -ErrorAction SilentlyContinue) { bun run dev } else { npm run dev }

test:
    uv run pytest tests -q

e2e:
    Set-Location '{{justfile_directory()}}\webapp'; npm run e2e

gates-green:
    just lint; just test

# Local full gate (Actions is repo-disabled like private repos: fleet standard
# ships the CI file but gates run here). Mirrors .github/workflows/ci.yml.
ci:
    uv run ruff check src tests
    uv run ruff format src tests --check
    uv run pyright src
    uv run pytest tests -q
    Set-Location '{{justfile_directory()}}\webapp'; npm ci; npm run biome:ci; npm run check; npm run build

lint:
    uv run ruff check src tests

fmt:
    uv run ruff format src tests

fix:
    uv run ruff check src tests --fix
    uv run ruff format src tests

health:
    Invoke-RestMethod -Uri "http://127.0.0.1:11024/api/v1/status"

demo:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File '{{justfile_directory()}}\webapp\start.ps1' -Demo

# Bootstrap: install dev deps + pre-commit hook
