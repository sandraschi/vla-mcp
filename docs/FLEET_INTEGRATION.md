# Fleet integration — robotics stack

vla-mcp bridges **Wall-OSS, WALL-WM, DMuon, X-VLA** with the local robotics fleet: worldlabs-mcp, robotics-mcp, yahboom-mcp, avatarops, and **aiwatcher-mcp** for intelligence surfacing.

## Ports

| Role | Port |
|------|------|
| Backend API + MCP HTTP | **11024** |
| Vite webapp | **11025** |

## Fleet peers (HTTP)

| Peer | Default URL | Role |
|------|-------------|------|
| worldlabs-mcp | `http://127.0.0.1:10865` | 3D room / multiview sim |
| robotics-mcp | `http://127.0.0.1:10706` | ROS2 / fleet dashboard |
| yahboom-mcp | `http://127.0.0.1:10892` | Raspbot car demos |
| avatarops | `http://127.0.0.1:10793` | VRoid episodes |

Env: `VLA_WORLDLABS_MCP_URL`, `VLA_ROBOTICS_MCP_URL`, `VLA_YAHBOOM_MCP_URL`, `VLA_AVATAR_MCP_URL`.

Alias `robotics` → **robotics-mcp** (10706). Yahboom is separate for Boomy live loops.

## aiwatcher cross-talk

When a pipeline run succeeds, vla-mcp can notify aiwatcher:

```
POST http://127.0.0.1:10946/api/fleet/ingest
source: vla-mcp-pipeline
```

| Variable | Default | Meaning |
|----------|---------|---------|
| `VLA_AIWATCHER_BASE_URL` | — | `http://127.0.0.1:10946` |
| `VLA_AIWATCHER_PUSH_ENABLED` | `1` | Toggle ingest |
| `VLA_AIWATCHER_API_KEY` | — | Match `AIWATCHER_API_KEY` if auth enabled |

Items surface in **VLA & Spatial AI** and **Robotics** interest bundles (feed pattern `Fleet Events`).

## Pipeline liveness

```
GET http://127.0.0.1:11024/api/pipeline/liveness
GET http://127.0.0.1:11024/api/health
```

Reports: last pipeline provenance age, peer reachability, aiwatcher health.

Probed by aiwatcher `pipeline/liveness`, meta-mcp, and fleet-agent supervisors.

## fleet-agent

Registered as `vla` in `FLEET_SERVERS`:

```
http://127.0.0.1:11024/mcp
```

Key tools: `vla_pipeline`, `vla_weights`, `vla_fleet`, `vla_agentic_workflow`.

## arxiv code-hunt link

arxiv-mcp code-hunt pushes VLA-titled paper drops (Wall-OSS, X-VLA, LeRobot, …) to the same aiwatcher ingest endpoint. Complementary: arxiv finds papers; vla-mcp runs the fleet loop.

## MCP help

Call `vla_help()` for topic index, or `vla_help(topic="fleet_integration")` for this document in-chat.

## Typical agent workflow

1. `vla_fleet(operation="bridge_status")` — which peers are up?
2. `vla_pipeline(operation="run", live=False)` — simulated ingest + export + DMuon dry-run
3. `vla_pipeline(operation="last_run")` — provenance path under `VLA_DATASET_ROOT/logs/pipeline/`
4. Check aiwatcher Dashboard for `[vla-pipeline]` fleet event (if push enabled)
