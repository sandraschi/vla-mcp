import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../lib/api";

type Item = { kind: string; title: string; detail: string };

export default function InboxPage() {
	const [items, setItems] = useState<Item[]>([]);
	const [query, setQuery] = useState("");
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	function load() {
		setLoading(true);
		setError(null);
		Promise.all([
			apiGet<{
				alerts?: string[];
				checks?: { name: string; ok: boolean; detail?: string }[];
			}>("/api/pipeline/liveness"),
			apiGet<{
				success?: boolean;
				run_id?: string;
				summary?: Record<string, unknown>;
			}>("/api/v1/pipeline/last"),
		])
			.then(([live, last]) => {
				const rows: Item[] = [];
				for (const a of live.alerts ?? [])
					rows.push({ kind: "alert", title: a, detail: "" });
				for (const c of live.checks ?? [])
					rows.push({
						kind: c.ok ? "check-ok" : "check-fail",
						title: c.name,
						detail: c.detail ?? "",
					});
				if (last.run_id)
					rows.push({
						kind: "run",
						title: `Last run ${last.run_id}`,
						detail: JSON.stringify(last.summary ?? {}),
					});
				if (rows.length === 0)
					rows.push({
						kind: "empty",
						title: "All quiet",
						detail: "No alerts, no runs yet.",
					});
				setItems(rows);
			})
			.catch((e) => setError(e instanceof Error ? e.message : "load failed"))
			.finally(() => setLoading(false));
	}

	useEffect(load, []);

	const filtered = useMemo(() => {
		const q = query.trim().toLowerCase();
		const sorted = [...items].sort((a, b) => a.kind.localeCompare(b.kind));
		if (!q) return sorted;
		return sorted.filter(
			(i) =>
				i.title.toLowerCase().includes(q) || i.detail.toLowerCase().includes(q),
		);
	}, [items, query]);

	if (loading)
		return <div className="text-sm text-gray-400">Loading inbox…</div>;

	return (
		<div data-testid="inbox-page">
			<h1 className="text-2xl font-bold mb-1">Inbox</h1>
			<p className="text-gray-400 text-sm mb-4">
				Pipeline alerts, loop checks, and the last run — newest signal first.
			</p>
			<input
				data-testid="search-inbox"
				value={query}
				onChange={(e) => setQuery(e.target.value)}
				placeholder="Search inbox…"
				className="w-full max-w-md bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 mb-4"
			/>
			{error && (
				<div className="text-sm text-red-400 mb-4">
					{error}{" "}
					<button onClick={load} className="underline">
						Retry
					</button>
				</div>
			)}
			{!error && filtered.length === 0 && (
				<div className="text-sm text-gray-400">
					No items match “{query}”.{" "}
					<button onClick={() => setQuery("")} className="underline">
						Clear search
					</button>
				</div>
			)}
			<div className="space-y-2">
				{filtered.map((i) => (
					<div
						key={`${i.kind}:${i.title}`}
						className="bg-gray-900 border border-gray-800 rounded-lg p-3"
					>
						<div className="flex items-center gap-2 text-sm">
							<span
								className={`text-sm px-2 py-0.5 rounded ${
									i.kind === "alert" || i.kind === "check-fail"
										? "bg-red-900/40 text-red-300"
										: i.kind === "check-ok"
											? "bg-green-900/40 text-green-300"
											: "bg-violet-900/40 text-violet-300"
								}`}
							>
								{i.kind}
							</span>
							<span className="text-gray-100">{i.title}</span>
						</div>
						{i.detail && (
							<div className="text-sm text-gray-400 mt-1 break-words">
								{i.detail}
							</div>
						)}
					</div>
				))}
			</div>
			<div className="text-sm text-gray-400 mt-3">
				{filtered.length} of {items.length} items
			</div>
		</div>
	);
}
