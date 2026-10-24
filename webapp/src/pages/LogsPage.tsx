import { useCallback, useEffect, useState } from "react";
import { apiGet } from "../lib/api";

type Job = { job_id?: string; id?: string; status?: string };

export default function LogsPage() {
	const [jobs, setJobs] = useState<Job[]>([]);
	const [selected, setSelected] = useState("");
	const [log, setLog] = useState("");
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	const loadJobs = useCallback(() => {
		setLoading(true);
		setError(null);
		apiGet<{ jobs?: Job[] }>("/api/v1/training/jobs")
			.then((d) => {
				const list = d.jobs ?? [];
				setJobs(list);
				const first = list[0];
				const id = first ? String(first.job_id ?? first.id ?? "") : "";
				setSelected((prev) => (prev === "" ? id : prev));
			})
			.catch((e) => setError(e instanceof Error ? e.message : "load failed"))
			.finally(() => setLoading(false));
	}, []);

	const loadLog = useCallback(() => {
		if (!selected) return;
		apiGet<{ text?: string; log?: string }>(
			`/api/v1/training/jobs/${selected}/log`,
		)
			.then((d) => setLog(String(d.text ?? d.log ?? "")))
			.catch((e) =>
				setError(e instanceof Error ? e.message : "log load failed"),
			);
	}, [selected]);

	useEffect(() => {
		loadJobs();
	}, [loadJobs]);
	useEffect(() => {
		loadLog();
	}, [loadLog]);

	if (loading)
		return <div className="text-sm text-gray-400">Loading jobs…</div>;

	return (
		<div data-testid="logs-page">
			<h1 className="text-2xl font-bold mb-1">Logs</h1>
			<p className="text-gray-400 text-sm mb-4">DMuon training job logs.</p>
			{error && (
				<div className="text-sm text-red-400 mb-4">
					{error}{" "}
					<button onClick={loadJobs} className="underline">
						Retry
					</button>
				</div>
			)}
			{jobs.length === 0 && !error && (
				<div className="text-sm text-gray-500">
					No training jobs yet. Start one from the{" "}
					<span className="text-violet-400">Training</span> page.
				</div>
			)}
			{jobs.length > 0 && (
				<>
					<div className="flex items-center gap-2 mb-3">
						<select
							data-testid="log-job-select"
							value={selected}
							onChange={(e) => setSelected(e.target.value)}
							className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-gray-100"
						>
							{jobs.map((j) => {
								const id = String(j.job_id ?? j.id ?? "");
								return (
									<option key={id} value={id}>
										{id} {j.status ? `(${j.status})` : ""}
									</option>
								);
							})}
						</select>
						<button
							data-testid="log-refresh"
							onClick={loadLog}
							className="text-xs px-2 py-1 rounded bg-gray-800 text-gray-200"
						>
							Refresh
						</button>
					</div>
					<pre className="bg-gray-950 border border-gray-800 rounded p-3 text-xs text-gray-300 overflow-x-auto max-h-[60vh] overflow-y-auto whitespace-pre-wrap">
						{log || "(empty log)"}
					</pre>
				</>
			)}
		</div>
	);
}
