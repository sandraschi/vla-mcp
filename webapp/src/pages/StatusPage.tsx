import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

export default function StatusPage() {
	const [status, setStatus] = useState<Record<string, unknown> | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	function load() {
		setLoading(true);
		setError(null);
		apiGet("/api/v1/status")
			.then(setStatus)
			.catch((e) => setError(e instanceof Error ? e.message : "load failed"))
			.finally(() => setLoading(false));
	}

	useEffect(load, []);

	if (loading)
		return <div className="text-sm text-gray-400">Loading status…</div>;

	return (
		<div data-testid="status-page">
			<h1 className="text-2xl font-bold mb-2">Status</h1>
			{error ? (
				<div className="text-sm text-red-400">
					{error}{" "}
					<button onClick={load} className="underline">
						Retry
					</button>
				</div>
			) : (
				<pre className="bg-gray-900 border border-gray-800 rounded p-4 text-xs overflow-x-auto text-gray-200">
					{JSON.stringify(status, null, 2)}
				</pre>
			)}
		</div>
	);
}
