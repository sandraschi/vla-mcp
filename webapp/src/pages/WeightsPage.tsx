import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../lib/api";

type Model = {
	key: string;
	repo_id: string;
	downloaded: boolean;
	local_path: string;
};

export default function WeightsPage() {
	const [models, setModels] = useState<Model[]>([]);
	const [filter, setFilter] = useState<"all" | "downloaded" | "missing">("all");
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	function load() {
		setLoading(true);
		setError(null);
		apiGet<{ weights?: { models?: Model[] } }>("/api/v1/status")
			.then((s) => {
				setModels(s.weights?.models ?? []);
			})
			.catch((e) => setError(e instanceof Error ? e.message : "load failed"))
			.finally(() => setLoading(false));
	}

	useEffect(load, []);

	const visible = useMemo(() => {
		const rows = [...models].sort((a, b) => a.key.localeCompare(b.key));
		if (filter === "downloaded") return rows.filter((m) => m.downloaded);
		if (filter === "missing") return rows.filter((m) => !m.downloaded);
		return rows;
	}, [models, filter]);

	if (loading)
		return <div className="text-sm text-gray-400">Loading weights…</div>;

	return (
		<div data-testid="weights-page">
			<h1 className="text-2xl font-bold mb-2">Weights</h1>
			<p className="text-gray-400 text-sm mb-4">
				Hugging Face Wall-OSS-0.5 and WALL-WM checkpoints
			</p>
			{error && (
				<div className="text-sm text-red-400 mb-4">
					{error}{" "}
					<button onClick={load} className="underline">
						Retry
					</button>
				</div>
			)}
			<div className="flex items-center gap-2 mb-3">
				{(["all", "downloaded", "missing"] as const).map((f) => (
					<button
						key={f}
						data-testid={`weights-filter-${f}`}
						onClick={() => setFilter(f)}
						className={`text-sm px-2 py-1 rounded border ${
							filter === f
								? "border-violet-600 text-violet-300"
								: "border-gray-700 text-gray-300"
						}`}
					>
						{f}
					</button>
				))}
				<span data-testid="weights-count" className="text-sm text-gray-400">
					{visible.length} of {models.length} models
				</span>
			</div>
			{!error && visible.length === 0 && (
				<div className="text-sm text-gray-400">
					No weights registered — check{" "}
					<code className="text-violet-300">
						vla_weights(operation="list_models")
					</code>
					.
				</div>
			)}
			<div className="space-y-3">
				{visible.map((m) => (
					<div
						key={m.key}
						className="bg-gray-900 border border-gray-800 rounded-lg p-4"
					>
						<div className="font-medium text-violet-300">{m.key}</div>
						<div className="text-sm text-gray-300">{m.repo_id}</div>
						<div className="text-sm text-gray-400 mt-1 font-mono">
							{m.local_path}
						</div>
						<div className="text-sm mt-2 text-gray-200">
							{m.downloaded
								? "Downloaded"
								: "Not cached — use vla_weights download"}
						</div>
					</div>
				))}
			</div>
		</div>
	);
}
