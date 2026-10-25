import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

type Peer = { name: string; url?: string; reachable?: boolean };

export default function FleetPage() {
	const [peers, setPeers] = useState<Peer[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	function load() {
		setLoading(true);
		setError(null);
		apiGet<{ peers?: Peer[] }>("/api/v1/fleet")
			.then((d) => setPeers(d.peers ?? []))
			.catch((e) => setError(e instanceof Error ? e.message : "load failed"))
			.finally(() => setLoading(false));
	}

	useEffect(load, []);

	if (loading)
		return <div className="text-sm text-gray-400">Probing fleet peers…</div>;

	return (
		<div data-testid="fleet-page">
			<h1 className="text-2xl font-bold mb-2">Fleet</h1>
			<p className="text-gray-400 text-sm mb-6">
				worldlabs-mcp · yahboom-mcp · avatarops simulation boundary
			</p>
			{error && (
				<div className="text-sm text-red-400 mb-4">
					{error}{" "}
					<button onClick={load} className="underline">
						Retry
					</button>
				</div>
			)}
			{!error && peers.length === 0 && (
				<div className="text-sm text-gray-400">No peers configured.</div>
			)}
			<div className="grid gap-3 md:grid-cols-3">
				{peers.map((p) => (
					<div
						key={p.name}
						className="bg-gray-900 border border-gray-800 rounded-lg p-4"
					>
						<div className="font-medium text-gray-100">{p.name}</div>
						<div className="text-sm text-gray-400 font-mono truncate">
							{p.url}
						</div>
						<div
							className={`text-sm mt-2 ${p.reachable ? "text-emerald-400" : "text-amber-400"}`}
						>
							{p.reachable ? "Reachable" : "Offline"}
						</div>
					</div>
				))}
			</div>
		</div>
	);
}
