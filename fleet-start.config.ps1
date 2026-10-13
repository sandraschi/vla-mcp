# Per-repo fleet start config for vla-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'vla-mcp'
    BackendPort  = 11024
    FrontendPort = 11025
    HealthPath   = '/api/v1/status'
    WebRoot      = 'webapp'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'vla_mcp.server:app'
        SyncExtras    = @('dev')
        SyncOnStart  = $true
        Env           = @{ WEB_PORT = '11024' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
