"""FastMCP 3.2 prompts and resources for vla-mcp."""

from fastmcp.prompts import Message


def register_prompts_and_resources(mcp) -> None:
    """Register @mcp.prompt and @mcp.resource handlers."""

    @mcp.resource("resource://vla/quickstart")
    def vla_quickstart() -> str:
        return """# vla-mcp Quickstart

1. vla_status - upstream clones, dataset root, fleet peers
2. vla_fleet(operation='scenario_brief') - closed-loop sim plan
3. worldlabs / robotics / avatar MCPs - generate multiview episodes
4. vla_dataset(operation='ingest_episode') - register trajectories
5. vla_training(operation='co_train_prepare') - DMuon + wall-x
6. vla_wall(operation='infer_prepare') - Wall-OSS-0.5 zero-shot exec
7. vla_world_model(operation='predict_prepare') - WALL-WM rollouts

Backend http://127.0.0.1:11024/mcp - Webapp http://127.0.0.1:11025
Upstream: https://github.com/X-Square-Robot/wall-x
Skill: skill://vla-expert/SKILL.md
"""

    @mcp.prompt()
    def vla_co_train_session() -> list[Message]:
        """Starter prompt for Wall-OSS + WALL-WM co-training."""
        return [
            Message(
                "Use vla_status and vla_fleet(scenario_brief) first. "
                "Collect failure trajectories, not just successes. "
                "Segment by events: approaching, contact, lift, slide, recovery. "
                "Export shards before DMuon co-training.",
                role="user",
            )
        ]

    @mcp.prompt()
    def vla_zero_shot_deploy() -> list[Message]:
        """Deploy Wall-OSS-0.5 on edge hardware."""
        return [
            Message(
                "Confirm VLA_WALL_X_ROOT and checkpoint. "
                "Wall-OSS uses flow-matching action supervision - avoid chunk-only velocity hacks. "
                "For smaller edge models consider X-VLA (0.9B) with PEFT.",
                role="user",
            )
        ]
