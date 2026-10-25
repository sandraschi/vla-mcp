# Fleet pre-commit Biome gate (webapp TS/TSX). Called by .pre-commit-config.yaml.
$ErrorActionPreference = "Stop"

$webapp = Join-Path $PSScriptRoot "..\webapp"
if (-not (Test-Path (Join-Path $webapp "package.json"))) { exit 0 }

Push-Location $webapp
try {
	if (Test-Path "bun.lock") {
		bunx @biomejs/biome check src 2>$null
		if ($LASTEXITCODE -ne 0) { npx @biomejs/biome check src }
	} else {
		npx @biomejs/biome check src
	}
	exit $LASTEXITCODE
} finally {
	Pop-Location
}
