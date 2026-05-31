# Root delegate - canonical launcher is webapp/start.ps1
param([switch]$Headless, [switch]$BackendOnly, [switch]$NoBrowser, [switch]$Demo)

& (Join-Path $PSScriptRoot "webapp\start.ps1") @PSBoundParameters
exit $LASTEXITCODE
