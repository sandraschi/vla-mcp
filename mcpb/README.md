# vla-mcp (MCPB Bundle)

FastMCP 3.2 bridge for Vision-Language-Action: Wall-OSS-0.5, WALL-WM, DMuon co-training, and fleet simulation loops

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "vla-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "vla_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **vla_status**: vla_status
- **vla_weights**: vla_weights
- **vla_wall**: vla_wall
- **vla_xvla**: vla_xvla
- **vla_world_model**: vla_world_model
- **vla_dataset**: vla_dataset
- **vla_events**: vla_events
- **vla_training**: vla_training
- **vla_pipeline**: vla_pipeline
- **vla_fleet**: vla_fleet
- **vla_world**: vla_world
- **vla_agentic_workflow**: vla_agentic_workflow
- **vla_help**: vla_help
- **_mount_fleet_proxies_list_models**: _mount_fleet_proxies(list_models)
- **_mount_fleet_proxies_local_status**: _mount_fleet_proxies(local_status)
- **_mount_fleet_proxies_download**: _mount_fleet_proxies(download)
- **api_health**: api_health
- **api_pipeline_liveness**: api_pipeline_liveness
- **api_status**: api_status
- **api_tools**: api_tools
- **api_control**: api_control
- **api_fleet**: api_fleet
- **api_episodes**: api_episodes
- **api_jobs**: api_jobs
- **api_job_log**: api_job_log
- **api_job_log_stream**: api_job_log_stream
- **api_pipeline_last**: api_pipeline_last
- **api_pipeline_run**: api_pipeline_run
- **api_help_index**: api_help_index
- **api_help_slug**: api_help_slug
- **api_capabilities**: api_capabilities
- **well_known_manifest**: well_known_manifest
- **show_vla_status_card**: show_vla_status_card
- **show_pipeline_run_card**: show_pipeline_run_card

## Requirements

- Python 3.12+
- uv
