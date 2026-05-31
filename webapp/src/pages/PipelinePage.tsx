import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../lib/api";

export default function PipelinePage() {
  const [describe, setDescribe] = useState<Record<string, unknown> | null>(null);
  const [lastRun, setLastRun] = useState<Record<string, unknown> | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [live, setLive] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiGet("/api/v1/pipeline/last").then(setLastRun).catch(() => setLastRun(null));
    apiPost("/api/v1/control/vla_pipeline", { operation: "describe" })
      .then(setDescribe)
      .catch(console.error);
  }, []);

  const runPipeline = () => {
    setBusy(true);
    apiPost(
      "/api/v1/pipeline/run",
      { live, include_failures: true, fallback_simulate: true },
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

  const runSimulated = () => {
    setLive(false);
    setBusy(true);
    apiPost("/api/v1/pipeline/run", { live: false, include_failures: true }, { confirm: true })
      .then(setResult)
      .catch(console.error)
      .finally(() => setBusy(false));
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">E2E Pipeline</h1>
      <p className="text-gray-400 text-sm mb-6">
        worldlabs → yahboom → ingest → export_numpy → DMuon dry_run (provenance under logs/pipeline/)
      </p>

      <div className="flex flex-wrap gap-2 mb-6">
        <button
          type="button"
          disabled={busy}
          onClick={runSimulated}
          className="px-4 py-2 bg-violet-700 hover:bg-violet-600 disabled:opacity-50 rounded text-sm"
        >
          Run simulated (CI-safe)
        </button>
        <label className="flex items-center gap-2 text-sm text-gray-400 px-2">
          <input type="checkbox" checked={live} onChange={(e) => setLive(e.target.checked)} />
          Live fleet probes
        </label>
        <button
          type="button"
          disabled={busy}
          onClick={runPipeline}
          className="px-4 py-2 bg-emerald-800 hover:bg-emerald-700 disabled:opacity-50 rounded text-sm"
        >
          Run {live ? "live" : "simulated"}
        </button>
      </div>

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

      {lastRun?.run && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="font-semibold mb-2">Last run</h2>
          <pre className="text-xs text-gray-400 overflow-x-auto">{JSON.stringify(lastRun.run, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
