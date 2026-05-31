import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../lib/api";
import EventTimeline from "../components/EventTimeline";

interface Segment {
  index: number;
  timestamp: number;
  event: string;
}

function readSegments(run: Record<string, unknown> | null | undefined): Segment[] {
  if (!run) return [];
  const segs = run.segments;
  return Array.isArray(segs) ? (segs as Segment[]) : [];
}

function readDuration(run: Record<string, unknown> | null | undefined): number {
  if (!run) return 0;
  const d = run.event_duration;
  return typeof d === "number" ? d : 0;
}

export default function PipelinePage() {
  const [describe, setDescribe] = useState<Record<string, unknown> | null>(null);
  const [lastRun, setLastRun] = useState<Record<string, unknown> | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [live, setLive] = useState(false);
  const [busy, setBusy] = useState(false);
  const [worldPrompt, setWorldPrompt] = useState(
    "cluttered indoor room with a table, chairs, and scattered objects",
  );
  const [world, setWorld] = useState<Record<string, unknown> | null>(null);
  const [worldBusy, setWorldBusy] = useState(false);

  useEffect(() => {
    apiGet("/api/v1/pipeline/last").then(setLastRun).catch(() => setLastRun(null));
    apiPost("/api/v1/control/vla_pipeline", { operation: "describe" })
      .then(setDescribe)
      .catch(console.error);
  }, []);

  const run = (useLive: boolean) => {
    setLive(useLive);
    setBusy(true);
    apiPost(
      "/api/v1/pipeline/run",
      { live: useLive, include_failures: true, fallback_simulate: true },
      { confirm: true },
    )
      .then((r) => {
        setResult(r);
        return apiGet("/api/v1/pipeline/last");
      })
      .then(setLastRun)
      .catch(console.error)
      .finally(() => setBusy(false));
  };

  const generateWorld = () => {
    setWorldBusy(true);
    setWorld(null);
    apiPost(
      "/api/v1/control/vla_world",
      { operation: "generate", prompt: worldPrompt },
      { confirm: true },
    )
      .then(setWorld)
      .catch((e) => setWorld({ success: false, error: String(e) }))
      .finally(() => setWorldBusy(false));
  };

  const resultRun = result;
  const lastRunData = (lastRun?.run as Record<string, unknown> | undefined) ?? null;
  const shownSegments = readSegments(resultRun).length ? resultRun : lastRunData;
  const segments = readSegments(shownSegments);
  const duration = readDuration(shownSegments);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">E2E Pipeline</h1>
      <p className="text-gray-400 text-sm mb-6">
        worldlabs → yahboom → ingest → export_numpy → DMuon dry_run (provenance under logs/pipeline/)
      </p>

      <div className="flex flex-wrap gap-2 mb-6 items-center">
        <button
          type="button"
          disabled={busy}
          onClick={() => run(false)}
          className="px-4 py-2 bg-violet-700 hover:bg-violet-600 disabled:opacity-50 rounded text-sm"
        >
          {busy && !live ? "Running…" : "Run simulated (CI-safe)"}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => run(true)}
          className="px-4 py-2 bg-emerald-800 hover:bg-emerald-700 disabled:opacity-50 rounded text-sm"
        >
          {busy && live ? "Running…" : "Run live (fleet probes)"}
        </button>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-4">
        <h2 className="font-semibold mb-2">3D room (worldlabs)</h2>
        <div className="flex flex-wrap gap-2 items-center">
          <input
            type="text"
            value={worldPrompt}
            onChange={(e) => setWorldPrompt(e.target.value)}
            className="flex-1 min-w-[18rem] bg-gray-950 border border-gray-700 rounded px-2 py-1.5 text-sm"
          />
          <button
            type="button"
            disabled={worldBusy}
            onClick={generateWorld}
            className="px-4 py-2 bg-sky-800 hover:bg-sky-700 disabled:opacity-50 rounded text-sm"
          >
            {worldBusy ? "Generating…" : "Generate 3D room"}
          </button>
        </div>
        {world && (
          <div className="mt-3 text-sm">
            {world.success && world.viewer_url ? (
              <a
                href={String(world.viewer_url)}
                target="_blank"
                rel="noreferrer"
                className="text-sky-400 underline"
              >
                Open Marble viewer →
              </a>
            ) : (
              <p className="text-amber-400">
                {String(world.error ?? "No viewer URL returned — check worldlabs-mcp is running.")}
              </p>
            )}
            <pre className="bg-gray-950 border border-gray-800 rounded p-3 text-xs overflow-x-auto mt-2">
              {JSON.stringify(world, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {segments.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-4">
          <EventTimeline
            segments={segments}
            duration={duration}
            title="Event-joint segmentation"
          />
        </div>
      )}

      {describe && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-4">
          <h2 className="font-semibold mb-2">Pipeline</h2>
          <p className="text-sm text-gray-400">{String(describe.pipeline ?? "")}</p>
        </div>
      )}

      {result && (
        <pre className="bg-gray-900 border border-gray-800 rounded p-4 text-xs overflow-x-auto mb-4">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}

      {lastRunData && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="font-semibold mb-2">Last run</h2>
          <pre className="text-xs text-gray-400 overflow-x-auto">{JSON.stringify(lastRunData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
