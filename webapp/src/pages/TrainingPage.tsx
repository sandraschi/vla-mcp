import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../lib/api";

export default function TrainingPage() {
  const [jobs, setJobs] = useState<Record<string, unknown> | null>(null);
  const [dryRun, setDryRun] = useState<Record<string, unknown> | null>(null);

  const refresh = () => apiGet("/api/v1/training/jobs").then(setJobs).catch(console.error);

  useEffect(() => {
    refresh();
  }, []);

  const previewLaunch = () => {
    apiPost("/api/v1/control/vla_training", {
      operation: "launch_co_train",
      dry_run: true,
      dataset_shard: "train_001",
    })
      .then(setDryRun)
      .catch(console.error);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Training</h1>
      <p className="text-gray-400 text-sm mb-6">DMuon gradient-bridged co-training jobs</p>

      <button
        type="button"
        onClick={previewLaunch}
        className="mb-4 px-4 py-2 bg-violet-700 hover:bg-violet-600 rounded text-sm"
      >
        Preview launch (dry run)
      </button>

      {dryRun && (
        <pre className="bg-gray-900 border border-gray-800 rounded p-4 text-xs overflow-x-auto mb-4">
          {JSON.stringify(dryRun, null, 2)}
        </pre>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <h2 className="font-semibold mb-2">Jobs</h2>
        <pre className="text-xs text-gray-400 overflow-x-auto">{JSON.stringify(jobs, null, 2)}</pre>
      </div>
    </div>
  );
}
