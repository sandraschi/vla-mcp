"""X-VLA 0.9B PEFT edge adapter for secondary agents (Raspbot / Boomy / Pi5)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..config import VLAConfig, get_config
from .hf_weights import HFWeightManager

XVLA_DOCS = "https://thu-air-dream.github.io/X-VLA"
XVLA_REPO = "https://github.com/THUDM/X-VLA"

EDGE_TARGETS = (
    {"id": "raspbot", "mcp": "yahboom-mcp", "notes": "Raspberry Pi 5 Yahboom Raspbot car"},
    {"id": "boomy", "mcp": "yahboom-mcp", "notes": "Yahboom Boomy / secondary edge agent"},
    {"id": "pi5_car", "mcp": "yahboom-mcp", "notes": "Generic Pi5 differential-drive stack"},
)


@dataclass
class XVLAAdapter:
    """Lightweight 0.9B flow-matching VLA with PEFT for edge deployment."""

    config: VLAConfig

    @classmethod
    def default(cls) -> XVLAAdapter:
        return cls(config=get_config())

    def upstream_resolved(self) -> Path | None:
        if not self.config.xvla_root:
            return None
        p = Path(self.config.xvla_root).expanduser().resolve()
        return p if p.is_dir() else None

    def peft_dir(self) -> Path:
        p = Path(self.config.xvla_peft_dir).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    def health(self) -> dict:
        root = self.upstream_resolved()
        adapter_path = self.config.xvla_peft_adapter
        adapter_ok = bool(adapter_path and Path(adapter_path).expanduser().is_dir())
        hf = HFWeightManager.default().local_status("x-vla")
        return {
            "model": "X-VLA-0.9B",
            "parameters": "0.9B",
            "control": "flow_matching",
            "upstream_configured": root is not None,
            "upstream_path": str(root) if root else None,
            "reference_docs": XVLA_DOCS,
            "reference_repo": XVLA_REPO,
            "hf_repo": self.config.hf_xvla_repo,
            "hf_cached": hf.get("exists") if hf.get("success") else False,
            "peft_adapter_set": adapter_path is not None,
            "peft_adapter_exists": adapter_ok,
            "peft_dir": str(self.peft_dir()),
            "edge_device": self.config.xvla_edge_device,
        }

    def list_targets(self) -> dict:
        return {
            "success": True,
            "targets": list(EDGE_TARGETS),
            "message": "Secondary edge agents suited for X-VLA PEFT (not full Wall-OSS).",
        }

    def peft_config_template(self, *, target: str = "raspbot", rank: int = 8) -> dict:
        return {
            "success": True,
            "template": {
                "base_model": self.config.hf_xvla_repo,
                "method": "lora",
                "r": rank,
                "lora_alpha": rank * 2,
                "target_modules": ["q_proj", "v_proj", "action_head"],
                "flow_matching": True,
                "edge_target": target,
                "output_dir": str(self.peft_dir() / target),
                "train": {
                    "batch_size": 4,
                    "learning_rate": 2e-4,
                    "max_steps": 2000,
                    "dataset_root": self.config.dataset_root,
                },
            },
            "message": "PEFT LoRA skeleton for X-VLA 0.9B; merge with upstream training YAML.",
        }

    def peft_prepare(self, *, target: str = "raspbot", rank: int = 8, write: bool = False) -> dict:
        root = self.upstream_resolved()
        tpl = self.peft_config_template(target=target, rank=rank)
        out_dir = self.peft_dir() / target
        out_file = out_dir / "peft_config.json"
        if write:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file.write_text(json.dumps(tpl["template"], indent=2), encoding="utf-8")
        if not root:
            return {
                **tpl,
                "success": False,
                "error": "VLA_XVLA_ROOT not configured",
                "config_path": str(out_file) if write else None,
                "recovery_options": [f"Clone {XVLA_REPO}", "Set VLA_XVLA_ROOT"],
            }
        return {
            **tpl,
            "upstream": str(root),
            "config_path": str(out_file) if write else None,
            "message": "PEFT config ready. Run upstream X-VLA fine-tune with exported shards.",
        }

    def edge_prepare(self, *, target: str = "raspbot") -> dict:
        """Deployment checklist for edge infer with optional PEFT adapter."""
        h = self.health()
        yahboom_url = self.config.yahboom_mcp_url or "http://127.0.0.1:10892"
        steps = [
            "vla_weights(operation='download', model_key='x-vla') — cache 0.9B base weights",
            f"vla_xvla(operation='peft_prepare', target='{target}', write=True) — write LoRA config",
            "Fine-tune adapter in VLA_XVLA_ROOT per upstream README (PEFT on fleet shards)",
            "vla_fleet(operation='call_peer', peer='yahboom', tool_name='robotics_system', ...)",
            f"Deploy merged adapter to edge; set VLA_XVLA_PEFT_ADAPTER; infer on {self.config.xvla_edge_device}",
        ]
        return {
            "success": True,
            "target": target,
            "model": "X-VLA-0.9B",
            "wall_oss_alternative": "Use Wall-OSS-0.5 on workstation; X-VLA on edge secondary agents",
            "health": h,
            "yahboom_mcp_url": yahboom_url,
            "steps": steps,
            "env_hints": {
                "VLA_XVLA_ROOT": self.config.xvla_root or "(unset)",
                "VLA_XVLA_PEFT_ADAPTER": self.config.xvla_peft_adapter or "(unset after train)",
                "VLA_XVLA_EDGE_DEVICE": self.config.xvla_edge_device,
            },
            "message": f"Edge PEFT path for {target} via X-VLA flow-matching VLA.",
        }

    def infer_prepare(self, *, target: str = "raspbot", task_hint: str | None = None) -> dict:
        root = self.upstream_resolved()
        if not root:
            return {
                "success": False,
                "error": "VLA_XVLA_ROOT not configured",
                "recovery_options": [f"Clone {XVLA_REPO}", "vla_wall(operation='edge_prepare')"],
            }
        adapter = self.config.xvla_peft_adapter
        return {
            "success": True,
            "message": "Run X-VLA edge inference from upstream with optional PEFT adapter.",
            "upstream": str(root),
            "target": target,
            "task_hint": task_hint,
            "base_weights": self.config.hf_xvla_repo,
            "peft_adapter": adapter,
            "device": self.config.xvla_edge_device,
        }
