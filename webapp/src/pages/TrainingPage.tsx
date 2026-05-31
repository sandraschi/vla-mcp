import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiPost } from "../lib/api";

type Job = {
  id?: string;
  status?: string;
  log_path?: string;
  command?: string[];
};

export default function TrainingPage() {
  const [jobs, setJobs] = useState<{ jobs?: Job[] } | null>(null);
  const [dryRun, setDryRun] = useState<Record<string, unknown> | null>(null);
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [logText, setLogText] = useState("");

  const refresh = () => apiGet<{ jobs?: Job[] }>("/api/v1/training/jobs").then(setJobs).catch(console.error);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (!selectedJob) {
      setLogText("");
      return;
    }
    let offset = 0;
    let cancelled = false;

    const poll = async () => {
      while (!cancelled) {
        try {
          const chunk = await apiGet<{
            success?: boolean;
            text?: string;
            next_offset?: number;
            eof?: boolean;
          }>(`/api/v1/training/jobs/${selectedJob}/log?offset=${offset}`);
          if (chunk.text) {
            setLogText((prev) => prev + chunk.text);
          }
          offset = chunk.next_offset ?? offset;
          const job = jobs?.jobs?.find((j) => j.id === selectedJob);
          if (chunk.eof && job?.status !== "running") break;
        } catch {
          break;
        }
        await new Promise((r) => setTimeout(r, 1000));
      }
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, [selectedJob, jobs?.jobs]);

  const previewLaunch = () => {
    apiPost("/api/v1/control/vla_training", {
      operation: "launch_co_train",
      dry_run: true,
      dataset_shard: "train_001",
    })
      .then(setDryRun)
      .catch(console.error);
  };

  const jobList = jobs?.jobs ?? [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Training</h1>
      <p className="text-gray-400 text-sm mb-6">
        DMuon gradient-bridged co-training — jobs persist under VLA_DATASET_ROOT/logs
      </p>

      <div className="flex flex-wrap gap-2 mb-4">
        <button
          type="button"
          onClick={previewLaunch}
          className="px-4 py-2 bg-violet-700 hover:bg-violet-600 rounded text-sm"
        >
          Preview launch (dry run)
        </button>
        <Link
          to="/pipeline"
          className="px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded text-sm"
        >
          Run E2E pipeline
        </Link>
      </div>

      {dryRun && (
        <pre className="bg-gray-900 border border-gray-800 rounded p-4 text-xs overflow-x-auto mb-4">
          {JSON.stringify(dryRun, null, 2)}
        </pre>
      )}

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="font-semibold mb-2">Jobs</h2>
          {jobList.length === 0 ? (
            <p className="text-sm text-gray-500">No jobs yet. Run pipeline or launch_co_train with confirm.</p>
          ) : (
            <ul className="space-y-2">
              {jobList.map((j) => (
                <li key={j.id}>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedJob(j.id ?? null);
                      setLogText("");
                    }}
                    className={`w-full text-left px-3 py-2 rounded text-sm font-mono ${
                      selectedJob === j.id ? "bg-violet-900/40 text-violet-200" : "bg-gray-800 hover:bg-gray-750"
                    }`}
                  >
                    {j.id} · {j.status}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="font-semibold mb-2">Log tail {selectedJob ? `(${selectedJob})` : ""}</h2>
          <pre className="text-xs text-gray-400 overflow-auto max-h-96 whitespace-pre-wrap font-mono">
            {logText || (selectedJob ? "Waiting for log output…" : "Select a job")}
          </pre>
        </div>
      </div>
    </div>
  );
}
