"""Event-joint segmentation from simulation / robot telemetry (WALL-WM style)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_EVENTS = (
    "idle",
    "approaching",
    "making_contact",
    "lifting",
    "sliding",
    "releasing",
    "colliding",
    "recovering",
)


@dataclass
class EventSegmenter:
    """Heuristic event joint tagger - replaces equilong fixed-time chunks."""

    contact_threshold: float = 0.35
    velocity_high: float = 0.8
    velocity_low: float = 0.15
    slip_variance: float = 0.25

    def segment(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        """Tag event joints from time-series telemetry samples.

        Each sample may include: timestamp, velocity, contact_force, gripper_open,
        distance_to_target, collision_flag.
        """
        if not samples:
            return {
                "success": False,
                "error": "samples list is empty",
                "error_type": "validation",
            }
        segments: list[dict[str, Any]] = []
        prev_event = "idle"
        for i, row in enumerate(samples):
            event = self._classify_sample(row, prev_event)
            if event != prev_event or i == 0:
                segments.append(
                    {
                        "index": i,
                        "timestamp": row.get("timestamp", i),
                        "event": event,
                    }
                )
                prev_event = event
        event_chain = [s["event"] for s in segments]
        return {
            "success": True,
            "segments": segments,
            "events": event_chain,
            "segment_count": len(segments),
            "message": "Event joints extracted (semantic transitions, not fixed dt chunks).",
        }

    def _classify_sample(self, row: dict[str, Any], prev: str) -> str:
        if row.get("collision_flag"):
            return "colliding"
        contact = float(row.get("contact_force", 0.0) or 0.0)
        velocity = float(row.get("velocity", 0.0) or 0.0)
        dist = row.get("distance_to_target")
        gripper = row.get("gripper_open")
        slip = float(row.get("slip_variance", 0.0) or 0.0)

        if slip >= self.slip_variance and contact > 0:
            return "recovering"
        if contact >= self.contact_threshold:
            if gripper is False or gripper == 0:
                return "releasing"
            if prev in ("making_contact", "approaching"):
                return "lifting" if velocity > self.velocity_low else "making_contact"
            return "making_contact"
        if dist is not None and float(dist) < 0.5 and velocity > self.velocity_low:
            return "approaching"
        if velocity >= self.velocity_high:
            return "sliding"
        if velocity <= self.velocity_low:
            return "idle"
        return prev if prev else "idle"

    def vocab(self) -> dict:
        return {
            "success": True,
            "events": list(DEFAULT_EVENTS),
            "count": len(DEFAULT_EVENTS),
            "message": "WALL-WM event joint vocabulary (semantic physical transitions).",
        }
