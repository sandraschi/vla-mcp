"""NotebookStore CRUD, validation, cap, and REST route tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from vla_mcp.engine.notebook_store import MAX_ENTRIES_PER_NOTEBOOK, NotebookStore
from vla_mcp.server import app


def _store(tmp_path, monkeypatch) -> NotebookStore:
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    return NotebookStore.default()


def test_add_and_get_roundtrip(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    result = store.add_entry(
        "dev",
        title="fixed ruff gate",
        body="run ruff check --fix",
        category="repo_fix",
        author="agent:opencode",
        tags=["repo:vla-mcp", "ruff"],
        metrics={"tests_passed": 51, "build_ok": True},
    )
    assert result["success"] is True
    entry = result["entry"]
    assert entry["notebook"] == "dev"
    assert entry["category"] == "repo_fix"
    assert entry["author"] == "agent:opencode"
    assert entry["tags"] == ["repo:vla-mcp", "ruff"]
    assert entry["metrics"] == {"tests_passed": 51, "build_ok": True}
    fetched = store.get_entry("dev", entry["id"])
    assert fetched is not None
    assert fetched["title"] == "fixed ruff gate"
    assert fetched["metrics"]["tests_passed"] == 51


def test_decision_category(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    result = store.add_entry(
        "dev",
        title="storage switched to SQLite",
        body="user chose SQLite over JSON files",
        category="decision",
    )
    assert result["success"] is True
    assert result["entry"]["category"] == "decision"


def test_validation(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    bad_nb = store.add_entry("bogus", title="t", body="b")
    assert bad_nb["success"] is False
    assert bad_nb["error_type"] == "validation"
    no_title = store.add_entry("dev", title="", body="b")
    assert no_title["success"] is False
    long_body = store.add_entry("dev", title="t", body="x" * 20001)
    assert long_body["success"] is False


def test_delete_roundtrip(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    entry = store.add_entry("personal", title="soak", body="gartenbau")["entry"]
    assert store.delete_entry("personal", entry["id"]) is True
    assert store.get_entry("personal", entry["id"]) is None
    assert store.delete_entry("personal", entry["id"]) is False


def test_cap_500(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    for i in range(MAX_ENTRIES_PER_NOTEBOOK + 20):
        store.add_entry("dev", title=f"entry {i}", body="body")
    listing = store.list_entries("dev", limit=600)
    assert listing["total"] == MAX_ENTRIES_PER_NOTEBOOK
    titles = {e["title"] for e in listing["entries"]}
    assert "entry 0" not in titles
    assert "entry 519" in titles


def test_summaries_and_counts(tmp_path, monkeypatch):
    store = _store(tmp_path, monkeypatch)
    store.add_entry("personal", title="p1", body="b")
    store.add_entry("dev", title="d1", body="b")
    counts = store.counts()
    assert counts == {"personal": 1, "dev": 1, "news": 0}
    summaries = store.summaries()
    assert summaries["news"]["count"] == 0
    assert summaries["dev"]["latest"]["title"] == "d1"


@pytest.mark.asyncio
async def test_rest_notebook_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/notebooks")
        assert resp.status_code == 200
        assert set(resp.json()["notebooks"]) == {"personal", "dev", "news"}

        resp = await client.post(
            "/api/v1/notebooks/dev/entries",
            json={
                "title": "installed uv",
                "body": "uv sync",
                "category": "tool_install",
                "metrics": {"tool": "uv", "ok": True},
            },
        )
        assert resp.status_code == 200
        entry_id = resp.json()["entry"]["id"]
        assert resp.json()["entry"]["author"] == "sandra"
        assert resp.json()["entry"]["metrics"]["tool"] == "uv"

        resp = await client.get("/api/v1/notebooks/dev/entries")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        resp = await client.delete(f"/api/v1/notebooks/dev/entries/{entry_id}")
        assert resp.status_code == 200
        resp = await client.delete(f"/api/v1/notebooks/dev/entries/{entry_id}")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_rest_notebook_validation(tmp_path, monkeypatch):
    monkeypatch.setenv("VLA_DATASET_ROOT", str(tmp_path))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/notebooks/bogus/entries", json={"title": "t", "body": "b"})
        assert resp.status_code == 404
        resp = await client.post("/api/v1/notebooks/dev/entries", json={"title": "t", "body": ""})
        assert resp.status_code == 422
