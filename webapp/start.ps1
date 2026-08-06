# vla-mcp webapp launcher (fleet START_SCRIPT_STANDARD)
param([switch]$Headless, [switch]$BackendOnly, [switch]$NoBrowser, [switch]$Demo)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPort = 11024
$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath

$FrontendPort = 11025
$WebRoot = $PSScriptRoot
$RepoRoot = Split-Path -Parent $WebRoot

Write-Host ""
Write-Host "VLA-MCP - Setup and Start" -ForegroundColor Cyan
Write-Host "Backend :$BackendPort   Frontend :$FrontendPort" -ForegroundColor DarkGray
Write-Host ""

Set-Location -LiteralPath $RepoRoot

$serverPy = Join-Path $RepoRoot "src\vla_mcp\server.py"
if (-not (Test-Path -LiteralPath $serverPy)) {
    Write-Host "ERROR: server.py missing." -ForegroundColor Red
    exit 1
}
if ((Get-Item -LiteralPath $serverPy).Length -lt 1024) {
    Write-Host "ERROR: server.py truncated (<1KB)." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: uv not found. Install: winget install astral-sh.uv" -ForegroundColor Red
    exit 1
}

Write-Host "[..] uv sync" -ForegroundColor Yellow
uv sync --extra dev
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[..] import smoke test" -ForegroundColor Yellow
uv run python -c "import vla_mcp.server; print('ok', vla_mcp.__version__)"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

foreach ($port in @($BackendPort, $FrontendPort)) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $conns) {
        try { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
    }
}
Start-Sleep -Milliseconds 300

if (-not $BackendOnly) {
    $webappDir = Join-Path $RepoRoot "webapp"
    if (-not (Test-Path (Join-Path $webappDir "node_modules"))) {
        Write-Host "[..] webapp npm install" -ForegroundColor Yellow
        Set-Location -LiteralPath $webappDir
        if (Get-Command bun -ErrorAction SilentlyContinue) { bun install } else { npm install }
        Set-Location -LiteralPath $RepoRoot
    }
}

Write-Host "[..] starting backend" -ForegroundColor Yellow
$backendProc = Start-Process -FilePath "uv" -ArgumentList "run","uvicorn","vla_mcp.server:app","--host","127.0.0.1","--port",$BackendPort,"--log-level","warning" -WorkingDirectory $RepoRoot -PassThru -WindowStyle Hidden

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/v1/status" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
}
if ($ready) {
    Write-Host "[ok] Backend http://127.0.0.1:$BackendPort" -ForegroundColor Green
} else {
    Write-Host "[!!] Backend did not respond" -ForegroundColor Red
    exit 1
}

if ($BackendOnly) {
    Write-Host "Backend-only mode. Press Enter to stop."
    Read-Host
    Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    exit 0
}

$viteBin = Join-Path $RepoRoot "webapp\node_modules\.bin\vite.cmd"
if (-not (Test-Path -LiteralPath $viteBin)) { $viteBin = Join-Path $RepoRoot "webapp\node_modules\.bin\vite" }

Write-Host "[..] starting frontend" -ForegroundColor Yellow
$frontendProc = Start-Process -FilePath $viteBin -WorkingDirectory (Join-Path $RepoRoot "webapp") -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 2
$url = "http://127.0.0.1:$FrontendPort"
if (-not $NoBrowser) { Start-Process $url }
Write-Host "[ok] Frontend $url" -ForegroundColor Green
Write-Host "Press Enter to stop both services."
Read-Host
Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue
