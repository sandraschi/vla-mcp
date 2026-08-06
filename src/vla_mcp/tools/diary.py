"""vla_diary — three notebooks: personal, dev (agent-logged), news (aiwatcher digest)."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from fastmcp import FastMCP

from ..engine.notebook_store import NOTEBOOKS, NotebookStore
from ..integrations.aiwatcher import fetch_fleet_items


def _abridge_item(item: dict[str, Any]) -> str:
    title = (item.get("title") or "untitled").strip()
    summary = (item.get("summary") or item.get("description") or "").strip()
    url = (item.get("url") or "").strip()
    line = f"- **{title}**"
    if summary:
        line += f": {summary[:220]}"
    if url:
        line += f" ({url})"
    return line


async def _build_digest() -> dict[str, Any]:
    result = await fetch_fleet_items(hours=24, limit=50)
    if not result.get("success"):
        return result
    items = result.get("items") or []
    if not items:
        return {
            "success": True,
            "count": 0,
            "message": "aiwatcher returned no items in the last 24h — no digest saved.",
        }
    top = items[:10]
    body = "\n".join(_abridge_item(i) for i in top)
    store = NotebookStore.default()
    title = f"News digest {date.today().isoformat()}"
    saved = store.add_entry(
        "news",
        title=title,
        body=body,
        category="digest",
        author="aiwatcher",
        tags=["news", "digest"],
    )
    if not saved.get("success"):
        return saved
    return {
        "success": True,
        "count": len(top),
        "digest_title": title,
        "entry": saved["entry"],
        "message": f"News digest saved with {len(top)} items from aiwatcher.",
    }


def register_diary_tool(mcp: FastMCP, all_tools: dict[str, Any]) -> None:
    """Register the vla_diary portmanteau."""

    @mcp.tool()
    async def vla_diary(
        operation: Literal["log", "list", "get", "delete", "news", "status"],
        notebook: str = "dev",
        category: str | None = None,
        title: str | None = None,
        body: str | None = None,
        author: str | None = None,
        tags: list[str] | None = None,
        metrics: dict[str, Any] | None = None,
        entry_id: str | None = None,
        confirm: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """VLA_DIARY - Three persistent notebooks: personal diary, dev diary, news diary.

        [RATIONALE]
        Consolidates all diary operations into one portmanteau so agents can
        log dev work and users can read personal/news entries without a dozen
        tools. The dev diary is the session-end memento: which repos were
        fixed, which tools were installed, and which bloopers happened.

        Operations:
        - log: write an entry. notebook dev (default) or personal. category:
          repo_fix, tool_install, blooper, decision, note. author defaults to
          agent:opencode for MCP calls. Agents MUST call this at session end.
        - list: recent entries (limit/offset, optional category filter).
        - get: one entry by entry_id.
        - delete: remove an entry (requires confirm=True).
        - news: pull the last 24h from aiwatcher /api/items and save an
          abridged digest entry to the news notebook.
        - status: entry counts per notebook.

        Tagging convention (MANDATORY for agents):
        - Always include a "repo:{name}" tag when the entry involves a repo
          (e.g. tags=["repo:vla-mcp"]). This makes the diary filterable per
          repo: "what happened in calibre-mcp" is a tag query.
        - Use category "decision" for spec/architecture choices that changed
          direction ("user said why not sqlite -> storage moved to SQLite").
        - Use category "blooper" for near-misses and gate failures, and put
          the fix in the body.

        metrics:
        - Structured gate evidence as JSON, e.g. {"tests_passed": 51,
          "build_ok": true, "gates": ["ruff", "tsc"]}. Data, not prose.

        ## Return Format
        {"success": bool, "message": str, "entries"?: [...], "entry"?: {...},
         "counts"?: {...}, "error"?: str, "error_type"?: str}

        ## Examples
        vla_diary(operation="log", notebook="dev", category="repo_fix",
                  title="fixed ruff gate in vla-mcp", body="...",
                  tags=["repo:vla-mcp", "ruff"], metrics={"tests_passed": 51})
        vla_diary(operation="log", category="decision",
                  title="notebooks storage switched to SQLite",
                  body="user chose SQLite over JSON files", tags=["repo:vla-mcp"])
        vla_diary(operation="log", category="blooper",
                  title="deleted the wrong branch", body="recovered via reflog")
        vla_diary(operation="news")
        vla_diary(operation="delete", entry_id="...", confirm=True)

        Notes:
        - delete is destructive - confirm=True is required
        - news needs VLA_AIWATCHER_BASE_URL configured
        """
        store = NotebookStore.default()

        if operation == "status":
            counts = store.counts()
            return {
                "success": True,
                "counts": counts,
                "notebooks": list(NOTEBOOKS),
                "message": "Notebook entry counts.",
            }

        if operation == "news":
            return await _build_digest()

        if operation == "list":
            if notebook not in NOTEBOOKS:
                return {"success": False, "error": f"notebook must be one of {NOTEBOOKS}", "error_type": "validation"}
            result = store.list_entries(notebook, limit=limit, offset=offset, category=category)
            return {
                "success": True,
                "notebook": notebook,
                "entries": result["entries"],
                "total": result["total"],
                "has_more": result["has_more"],
                "message": f"{result['total']} entries in {notebook} diary.",
            }

        if operation == "get":
            if not entry_id:
                return {"success": False, "error": "entry_id required for get", "error_type": "validation"}
            entry = store.get_entry(notebook, entry_id)
            if entry is None:
                return {"success": False, "error": "entry not found", "error_type": "not_found"}
            return {"success": True, "entry": entry, "message": "Diary entry."}

        if operation == "delete":
            if not entry_id:
                return {"success": False, "error": "entry_id required for delete", "error_type": "validation"}
            if not confirm:
                return {
                    "success": False,
                    "error": "delete requires confirm=True",
                    "error_type": "confirmation_required",
                    "recovery_options": ["Re-call with confirm=True to delete"],
                }
            deleted = store.delete_entry(notebook, entry_id)
            if not deleted:
                return {"success": False, "error": "entry not found", "error_type": "not_found"}
            return {"success": True, "deleted": entry_id, "message": "Diary entry deleted."}

        if operation == "log":
            if notebook not in NOTEBOOKS:
                return {"success": False, "error": f"notebook must be one of {NOTEBOOKS}", "error_type": "validation"}
            if notebook == "news":
                return {
                    "success": False,
                    "error": "news entries are digest-generated via operation=news",
                    "error_type": "validation",
                }
            if not title or not body:
                return {"success": False, "error": "title and body required for log", "error_type": "validation"}
            who = (author or "agent:opencode").strip() or "agent:opencode"
            return store.add_entry(
                notebook,
                title=title,
                body=body,
                category=category or "note",
                author=who,
                tags=tags,
                metrics=metrics,
            )

        return {
            "success": False,
            "error": f"Unknown operation: {operation}",
            "recovery_options": ["log", "list", "get", "delete", "news", "status"],
        }

    all_tools["vla_diary"] = vla_diary
