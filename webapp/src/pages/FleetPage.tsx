import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

type Peer = { name: string; url?: string; reachable?: boolean };

export default function FleetPage() {
  const [peers, setPeers] = useState<Peer[]>([]);

  useEffect(() => {
    apiGet<{ peers?: Peer[] }>("/api/v1/fleet")
      .then((d) => setPeers(d.peers ?? []))
      .catch(console.error);
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Fleet</h1>
      <p className="text-gray-400 text-sm mb-6">worldlabs-mcp · robotics-mcp · avatarops simulation boundary</p>
      <div className="grid gap-3 md:grid-cols-3">
        {peers.map((p) => (
          <div key={p.name} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <div className="font-medium">{p.name}</div>
            <div className="text-xs text-gray-500 font-mono truncate">{p.url}</div>
            <div className={`text-sm mt-2 ${p.reachable ? "text-emerald-400" : "text-amber-400"}`}>
              {p.reachable ? "Reachable" : "Offline"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
