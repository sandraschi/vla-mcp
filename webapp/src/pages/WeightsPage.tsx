import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

type Model = { key: string; repo_id: string; downloaded: boolean; local_path: string };

export default function WeightsPage() {
  const [models, setModels] = useState<Model[]>([]);

  useEffect(() => {
    apiGet<{ models?: Model[] }>("/api/v1/status")
      .then((s) => {
        const w = s.weights as { models?: Model[] } | undefined;
        setModels(w?.models ?? []);
      })
      .catch(console.error);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Weights</h1>
      <p className="text-gray-400 text-sm mb-6">Hugging Face Wall-OSS-0.5 and WALL-WM checkpoints</p>
      <div className="space-y-3">
        {models.map((m) => (
          <div key={m.key} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="font-medium text-violet-300">{m.key}</div>
            <div className="text-sm text-gray-400">{m.repo_id}</div>
            <div className="text-xs text-gray-500 mt-1 font-mono">{m.local_path}</div>
            <div className="text-xs mt-2">{m.downloaded ? "Downloaded" : "Not cached — use vla_weights download"}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
