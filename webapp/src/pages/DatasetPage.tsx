import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

type Episode = { id: string; source: string; events: string[] };

export default function DatasetPage() {
  const [data, setData] = useState<{ items?: Episode[]; total?: number } | null>(null);

  useEffect(() => {
    apiGet("/api/v1/dataset/episodes").then(setData).catch(console.error);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Dataset</h1>
      <p className="text-gray-400 text-sm mb-6">Event-joint episodes for WALL-WM / DMuon export</p>
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <p className="text-sm text-gray-400 mb-4">Total episodes: {data?.total ?? 0}</p>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {(data?.items ?? []).map((ep) => (
            <div key={ep.id} className="border border-gray-800 rounded p-3 text-sm">
              <code className="text-violet-300">{ep.id}</code>
              <span className="text-gray-500 ml-2">{ep.source}</span>
              <div className="mt-1 flex flex-wrap gap-1">
                {ep.events?.map((e) => (
                  <span key={e} className="text-xs bg-gray-800 px-1.5 py-0.5 rounded">
                    {e}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
