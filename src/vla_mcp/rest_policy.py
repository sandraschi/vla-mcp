"""REST control policy for the VLA webapp."""

from __future__ import annotations

from typing import Any

# Tools that cannot be invoked via generic REST (need MCP Context).
REST_BLOCKED_TOOLS = frozenset({"vla_agentic_workflow"})

# Operations that mutate external state; require X-VLA-Confirm: 1 header.
REST_MUTATING: dict[str, frozenset[str]] = {
    "vla_weights": frozenset({"download"}),
    "vla_training": frozenset({"launch_co_train", "stop_job"}),
    "vla_fleet": frozenset({"call_peer"}),
    "vla_dataset": frozenset(
        {"ingest_episode", "segment_telemetry", "export_shard", "export_numpy_shard"}
    ),
    "vla_xvla": frozenset({"peft_prepare"}),
    "vla_world": frozenset({"generate"}),
    "vla_pipeline": frozenset({"run"}),
}


def rest_control_allowed(
    tool_name: str,
    body: dict[str, Any],
    *,
    confirm_header: str | None,
) -> tuple[bool, str | None]:
    if tool_name in REST_BLOCKED_TOOLS:
        return False, f"{tool_name} requires MCP host Context"
    op = body.get("operation")
    if not op:
        return True, None
    mutating = REST_MUTATING.get(tool_name, frozenset())
    if op not in mutating:
        return True, None
    if tool_name == "vla_training" and op == "launch_co_train" and body.get("dry_run"):
        return True, None
    if tool_name == "vla_xvla" and op == "peft_prepare" and not body.get("write"):
        return True, None
    if confirm_header == "1":
        return True, None
    return False, "Mutating REST call requires header X-VLA-Confirm: 1"
