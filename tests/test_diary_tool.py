"""vla_diary MCP tool tests."""

from __future__ import annotations

import json

import pytest

from vla_mcp.server import mcp


def _text(result) -> dict:
    payload = result[0] if isinstance(result, (list, tuple)) else result
    raw = payload.text if hasattr(payload, "text") else (payload.content or [None])[0].text
    return json.loads(raw)


@pytest.mark.asyncio
async def test_diary_status(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    result = _text(await mcp.call_tool("vla_diary", {"operation": "status"}))
    assert result["success"] is True
    assert result["counts"] == {"personal": 0, "dev": 0, "news": 0}


@pytest.mark.asyncio
async def test_diary_log_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    result = _text(
        await mcp.call_tool(
            "vla_diary",
            {
                "operation": "log",
                "notebook": "dev",
                "category": "blooper",
                "title": "deleted the wrong branch",
                "body": "recovered via reflog",
                "tags": ["repo:git-mcp", "git"],
                "metrics": {"recovered": True, "time_lost_min": 5},
            },
        )
    )
    assert result["success"] is True
    assert result["entry"]["author"] == "agent:opencode"
    assert result["entry"]["category"] == "blooper"
    assert result["entry"]["tags"] == ["repo:git-mcp", "git"]
    assert result["entry"]["metrics"] == {"recovered": True, "time_lost_min": 5}

    listing = _text(await mcp.call_tool("vla_diary", {"operation": "list", "notebook": "dev"}))
    assert listing["total"] == 1
    assert listing["entries"][0]["title"] == "deleted the wrong branch"

    filtered = _text(await mcp.call_tool("vla_diary", {"operation": "list", "notebook": "dev", "category": "repo_fix"}))
    assert filtered["total"] == 0


@pytest.mark.asyncio
async def test_diary_delete_requires_confirm(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    created = _text(
        await mcp.call_tool(
            "vla_diary",
            {"operation": "log", "notebook": "dev", "title": "t", "body": "b"},
        )
    )
    entry_id = created["entry"]["id"]
    denied = _text(await mcp.call_tool("vla_diary", {"operation": "delete", "notebook": "dev", "entry_id": entry_id}))
    assert denied["success"] is False
    assert denied["error_type"] == "confirmation_required"

    deleted = _text(
        await mcp.call_tool(
            "vla_diary", {"operation": "delete", "notebook": "dev", "entry_id": entry_id, "confirm": True}
        )
    )
    assert deleted["success"] is True
    assert deleted["deleted"] == entry_id


@pytest.mark.asyncio
async def test_diary_news_not_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    monkeypatch.setenv("VLA_AIWATCHER_BASE_URL", "")
    result = _text(await mcp.call_tool("vla_diary", {"operation": "news"}))
    assert result["success"] is False
    assert result["error_type"] == "not_configured"
    assert "recovery_options" in result


@pytest.mark.asyncio
async def test_diary_rejects_news_log(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    result = _text(
        await mcp.call_tool("vla_diary", {"operation": "log", "notebook": "news", "title": "t", "body": "b"})
    )
    assert result["success"] is False
    assert result["error_type"] == "validation"
