@echo off
REM Fleet pre-commit Biome gate (webapp TS/TSX). Called by .pre-commit-config.yaml.
setlocal
if exist "%~dp0..\..\webapp\package.json" (
  pushd "%~dp0..\..\webapp"
  if exist "bun.lock" (
    bunx @biomejs/biome check src 2>nul || npx @biomejs/biome check src
  ) else (
    npx @biomejs/biome check src
  )
  popd
)
endlocal
exit /b 0
