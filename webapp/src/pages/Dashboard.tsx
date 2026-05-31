import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../lib/api";
import { Activity, Boxes, Brain, Download } from "lucide-react";

export default function Dashboard() {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [caps, setCaps] = useState<Record<string, unknown> | null>(null);
  const [tools, setTools] = useState<string[]>([]);

  useEffect(() => {
    apiGet("/api/v1/status").then(setStatus).catch(console.error);
    apiGet("/api/capabilities").then(setCaps).catch(console.error);
    apiGet<{ tools?: string[] }>("/api/v1/tools").then((d) => setTools(d.tools ?? [])).catch(console.error);
  }, []);

  const cards = [
    { label: "Server", value: String(status?.server ?? "offline"), icon: Activity },
    { label: "Version", value: String(status?.version ?? "-"), icon: Brain },
    { label: "Episodes", value: String(status?.dataset_episodes ?? 0), icon: Boxes },
    { label: "Tools", value: String(tools.length), icon: Download },
  ];

  const features = (caps?.features as Record<string, boolean>) ?? {};

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">VLA Dashboard</h1>
      <p className="text-gray-400 text-sm mb-6">
        Wall-OSS-0.5 + WALL-WM + DMuon — event-joint spatial intelligence (wall-x / WALL-E stack)
      </p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {cards.map(({ label, value, icon: Icon }) => (
          <div key={label} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-gray-400 mb-1">
              <Icon size={14} className="text-violet-400" />
              {label}
            </div>
            <div className="text-xl font-mono text-gray-100">{value}</div>
          </div>
        ))}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-4">
        <h2 className="text-lg font-semibold mb-3">Capabilities</h2>
        <div className="flex flex-wrap gap-2">
          {Object.entries(features).map(([k, v]) => (
            <span
              key={k}
              className={`text-xs px-2 py-1 rounded ${v ? "bg-violet-900/40 text-violet-200" : "bg-gray-800 text-gray-500"}`}
            >
              {k}: {v ? "on" : "off"}
            </span>
          ))}
        </div>
      </div>

      <p className="text-sm text-gray-500">
        <Link to="/pipeline" className="text-violet-400 hover:text-violet-300">
          E2E pipeline
        </Link>
        {" · "}
        <Link to="/fleet" className="text-violet-400 hover:text-violet-300">
          Fleet loop
        </Link>
        {" · "}
        <Link to="/help" className="text-violet-400 hover:text-violet-300">
          Docs
        </Link>
      </p>
    </div>
  );
}
