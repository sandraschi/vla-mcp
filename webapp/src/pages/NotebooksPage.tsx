import { useCallback, useEffect, useState } from "react";
import { apiDelete, apiGet, apiPost } from "../lib/api";
import { BookOpen, Newspaper, NotebookPen, RefreshCw, Trash2 } from "lucide-react";

type Entry = {
  id: string;
  notebook: string;
  category: string;
  title: string;
  body: string;
  author: string;
  tags: string[];
  metrics: Record<string, unknown>;
  created_at: string;
};

type EntriesResp = { success: boolean; entries: Entry[]; total: number; has_more: boolean };

const NOTEBOOKS = [
  { name: "personal", label: "Personal", icon: BookOpen, hint: "Your own diary — free-form." },
  { name: "dev", label: "Dev Diary", icon: NotebookPen, hint: "Repo fixes, tools installed, bloopers." },
  { name: "news", label: "News", icon: Newspaper, hint: "Abridged daily digest from aiwatcher." },
] as const;

const CATEGORIES = ["repo_fix", "tool_install", "blooper", "decision", "note"] as const;

export default function NotebooksPage() {
  const [active, setActive] = useState<(typeof NOTEBOOKS)[number]["name"]>("personal");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [total, setTotal] = useState(0);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [category, setCategory] = useState<string>("note");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (notebook: string) => {
    try {
      const resp = await apiGet<EntriesResp>(`/api/v1/notebooks/${notebook}/entries?limit=50`);
      setEntries(resp.entries ?? []);
      setTotal(resp.total ?? 0);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load entries");
    }
  }, []);

  useEffect(() => {
    setError(null);
    refresh(active);
  }, [active, refresh]);

  const submit = async () => {
    if (!title.trim() || !body.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await apiPost(`/api/v1/notebooks/${active}/entries`, {
        title: title.trim(),
        body: body.trim(),
        category: active === "dev" ? category : "note",
      });
      setTitle("");
      setBody("");
      setCategory("note");
      await refresh(active);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save entry");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string) => {
    try {
      await apiDelete(`/api/v1/notebooks/${active}/entries/${id}`);
      await refresh(active);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete entry");
    }
  };

  const pullDigest = async () => {
    setBusy(true);
    setError(null);
    try {
      await apiPost("/api/v1/notebooks/news/digest");
      await refresh("news");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to pull digest");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-testid="notebooks-page">
      <h1 className="text-2xl font-bold mb-2">Notebooks</h1>
      <p className="text-gray-400 text-sm mb-6">
        Personal diary · dev diary (AI-logged) · abridged daily news digest
      </p>

      <div className="flex gap-2 mb-6">
        {NOTEBOOKS.map(({ name, label, icon: Icon }) => (
          <button
            key={name}
            type="button"
            data-testid={`notebook-tab-${name}`}
            onClick={() => setActive(name)}
            className={`flex items-center gap-2 px-4 py-2 rounded text-sm transition ${
              active === name
                ? "bg-violet-900/40 text-violet-300 border border-violet-800"
                : "bg-gray-900 border border-gray-800 text-gray-400 hover:text-gray-200"
            }`}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-950/40 border border-red-900 text-red-300 text-sm rounded-lg p-3 mb-4">
          {error}
        </div>
      )}

      {active === "news" && (
        <button
          type="button"
          data-testid="news-pull-digest"
          onClick={pullDigest}
          disabled={busy}
          className="flex items-center gap-2 px-4 py-2 rounded text-sm bg-violet-700 hover:bg-violet-600 disabled:opacity-50 mb-6"
        >
          <RefreshCw size={14} className={busy ? "animate-spin" : ""} />
          Pull today's digest (aiwatcher)
        </button>
      )}

      {active !== "news" && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-6">
          <h2 className="text-sm font-semibold text-gray-300 mb-3">New entry</h2>
          {active === "dev" && (
            <div className="mb-3 flex gap-2">
              {CATEGORIES.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setCategory(c)}
                  className={`text-xs px-2 py-1 rounded ${
                    category === c ? "bg-violet-900/40 text-violet-200" : "bg-gray-800 text-gray-500 hover:text-gray-300"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
          )}
          <input
            data-testid="notebook-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title"
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm mb-2 outline-none focus:border-violet-600"
          />
          <textarea
            data-testid="notebook-body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="What happened?"
            rows={5}
            className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm mb-3 outline-none focus:border-violet-600 resize-y"
          />
          <button
            type="button"
            data-testid="notebook-save"
            onClick={submit}
            disabled={busy || !title.trim() || !body.trim()}
            className="px-4 py-2 rounded text-sm bg-violet-700 hover:bg-violet-600 disabled:opacity-50"
          >
            Save entry
          </button>
        </div>
      )}

      <div className="space-y-3" data-testid="notebook-entries">
        {entries.length === 0 && (
          <p className="text-sm text-gray-500">
            {active === "news" ? "No digests yet — pull one above." : "No entries yet."}
          </p>
        )}
        {entries.map((entry) => (
          <div key={entry.id} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-start justify-between gap-2 mb-1">
              <div>
                <span className="text-sm font-semibold text-gray-100">{entry.title}</span>
                {entry.category && entry.category !== "note" && (
                  <span className="ml-2 text-xs px-2 py-0.5 rounded bg-violet-900/40 text-violet-300">
                    {entry.category}
                  </span>
                )}
              </div>
              <button
                type="button"
                data-testid={`notebook-delete-${entry.id}`}
                onClick={() => remove(entry.id)}
                className="text-gray-600 hover:text-red-400 transition shrink-0"
                title="Delete"
              >
                <Trash2 size={14} />
              </button>
            </div>
            <p className="text-sm text-gray-400 whitespace-pre-wrap">{entry.body}</p>
            <div className="mt-2 text-xs text-gray-600 flex flex-wrap gap-x-3 gap-y-1">
              <span>{new Date(entry.created_at).toLocaleString()}</span>
              <span>{entry.author}</span>
              {entry.tags?.length > 0 && <span>{entry.tags.join(", ")}</span>}
              {entry.metrics && Object.keys(entry.metrics).length > 0 && (
                <span className="flex gap-1.5">
                  {Object.entries(entry.metrics).map(([k, v]) => (
                    <span key={k} className="px-1.5 py-0.5 rounded bg-gray-800 text-gray-500 font-mono">
                      {k}: {String(v)}
                    </span>
                  ))}
                </span>
              )}
            </div>
          </div>
        ))}
        {total > entries.length && (
          <p className="text-xs text-gray-600">+{total - entries.length} older entries (limit 500)</p>
        )}
      </div>
    </div>
  );
}
