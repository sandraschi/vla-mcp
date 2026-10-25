import { useCallback, useEffect, useState } from "react";
import { apiGet } from "../lib/api";

type LogRow = { ts: string; level: string; logger: string; message: string };

const LEVELS = ["", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];

export default function LoggerModal({ onClose }: { onClose: () => void }) {
	const [logs, setLogs] = useState<LogRow[]>([]);
	const [level, setLevel] = useState("");
	const [query, setQuery] = useState("");
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	const fetchLogs = useCallback((lv: string, q: string) => {
		setLoading(true);
		setError(null);
		const params = new URLSearchParams({ limit: "200" });
		if (lv) params.set("level", lv);
		if (q) params.set("q", q);
		apiGet<{ logs?: LogRow[] }>(`/api/logs?${params.toString()}`)
			.then((d) => setLogs(d.logs ?? []))
			.catch((e) => setError(e instanceof Error ? e.message : "load failed"))
			.finally(() => setLoading(false));
	}, []);

	function load() {
		fetchLogs(level, query.trim());
	}

	useEffect(() => {
		fetchLogs(level, "");
	}, [level, fetchLogs]);
	useEffect(() => {
		const handler = (e: KeyboardEvent) => {
			if (e.key === "Escape") onClose();
		};
		window.addEventListener("keydown", handler);
		return () => window.removeEventListener("keydown", handler);
	}, [onClose]);

	function exportTxt() {
		const blob = new Blob(
			[
				logs
					.map((l) => `${l.ts} ${l.level} ${l.logger}: ${l.message}`)
					.join("\n"),
			],
			{ type: "text/plain" },
		);
		const a = document.createElement("a");
		a.href = URL.createObjectURL(blob);
		a.download = "vla-logs.txt";
		a.click();
		URL.revokeObjectURL(a.href);
	}

	return (
		<div
			data-testid="logger-modal"
			role="button"
			tabIndex={0}
			onClick={onClose}
			onKeyDown={(e) => {
				if (e.key === "Escape" || e.key === "Enter") onClose();
			}}
			className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
		>
			<div
				className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-3xl max-h-[80vh] flex flex-col p-4"
				onClick={(e) => e.stopPropagation()}
				onKeyDown={(e) => e.stopPropagation()}
				role="presentation"
			>
				<div className="flex items-center gap-2 mb-3">
					<h2 className="text-lg font-semibold">Server logs</h2>
					<select
						data-testid="logger-level"
						value={level}
						onChange={(e) => setLevel(e.target.value)}
						className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-100"
					>
						{LEVELS.map((l) => (
							<option key={l} value={l}>
								{l || "all levels"}
							</option>
						))}
					</select>
					<input
						data-testid="logger-search"
						value={query}
						onChange={(e) => setQuery(e.target.value)}
						onKeyDown={(e) => e.key === "Enter" && load()}
						placeholder="Search logs…"
						className="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-100"
					/>
					<button
						data-testid="logger-export"
						onClick={exportTxt}
						disabled={logs.length === 0}
						className="text-sm px-2 py-1 rounded bg-gray-800 text-gray-200 disabled:opacity-40"
					>
						Export
					</button>
					<button
						data-testid="logger-close"
						onClick={onClose}
						className="text-sm px-2 py-1 rounded bg-gray-800 text-gray-200"
					>
						Close
					</button>
				</div>
				{loading && <div className="text-sm text-gray-400">Loading logs…</div>}
				{error && (
					<div className="text-sm text-red-400 mb-2">
						{error}{" "}
						<button onClick={load} className="underline">
							Retry
						</button>
					</div>
				)}
				{!loading && !error && logs.length === 0 && (
					<div className="text-sm text-gray-400">
						No log records yet — use the app and refresh.
					</div>
				)}
				<pre className="bg-gray-950 border border-gray-800 rounded p-3 text-sm text-gray-200 overflow-auto flex-1 whitespace-pre-wrap">
					{logs
						.map((l) => `${l.ts} ${l.level} ${l.logger}: ${l.message}`)
						.join("\n")}
				</pre>
				<div className="text-sm text-gray-400 mt-2">
					{logs.length} records (newest first)
				</div>
			</div>
		</div>
	);
}
