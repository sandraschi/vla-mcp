# Claude Code context — vla-mcp

Same as [AGENTS.md](AGENTS.md). FastMCP 3.2 VLA bridge for wall-x (Wall-OSS-0.5, WALL-WM, DMuon).

Ports: backend **11024**, frontend **11025**.

Key tools: `vla_status`, `vla_weights`, `vla_dataset` (segment_telemetry), `vla_training` (launch_co_train needs confirm=True), `vla_fleet` (call_peer).

Set `VLA_WALL_X_ROOT` to wall-x clone before GPU work.
