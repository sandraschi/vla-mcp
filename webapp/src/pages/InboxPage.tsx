import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../lib/api";

type Item = { kind: string; title: string; detail: string };

type LiveState =
	| { status: "pending" }
	| {
			status: "ok";
			alerts: string[];
			checks: { name: string; ok: boolean; detail?: string }[];
	  }
	| { status: "error"; message: string };

export default function InboxPage() {
	const [items, setItems] = useState<Item[]>([]);
	const [live, setLive] = useState<LiveState>({ status: "pending" });
	const [liveError, setLiveError] = useState<string | null>(null);
	const [runError, setRunError] = useState<string | null>(null);
	const [query, setQuery] = useState("");

	// The last run answers in ~0.3s; fleet probes can take seconds when peers
	// are offline. Load independently so the page paints immediately and the
	// peer rows stream in instead of blocking everything on the slowest call.
	useEffect(() => {
		let cancelled = false;
		apiGet<{
			success?: boolean;
			run_id?: string;
			summary?: Record<string, unknown>;
		}>("/api/v1/pipeline/last")
			.then((last) => {
				if (cancelled) return;
				if (last.run_id)
					setItems([
						{
							kind: "run",
							title: `Last run ${last.run_id}`,
							detail: JSON.stringify(last.summary ?? {}),
						},
					]);
			})
			.catch((e) => {
				if (!cancelled)
					setRunError(e instanceof Error ? e.message : "load failed");
			});
		apiGet<{
			alerts?: string[];
			checks?: { name: string; ok: boolean; detail?: string }[];
		}>("/api/pipeline/liveness")
			.then((d) => {
				if (cancelled) return;
				setLive({
					status: "ok",
					alerts: d.alerts ?? [],
					checks: d.checks ?? [],
				});
			})
			.catch((e) => {
				if (cancelled) return;
				setLive({ status: "error", message: "" });
				setLiveError(e instanceof Error ? e.message : "load failed");
			});
		return () => {
			cancelled = true;
		};
	}, []);

	const liveRows: Item[] = useMemo(() => {
		if (live.status !== "ok") return [];
		const rows: Item[] = [];
		for (const a of live.alerts)
			rows.push({ kind: "alert", title: a, detail: "" });
		for (const c of live.checks)
			rows.push({
				kind: c.ok ? "check-ok" : "check-fail",
				title: c.name,
				detail: c.detail ?? "",
			});
		return rows;
	}, [live]);

	const all = useMemo(() => {
		const rows = [...items, ...liveRows];
		if (rows.length === 0 && live.status === "ok")
			return [
				{
					kind: "empty",
					title: "All quiet",
					detail: "No alerts, no runs yet.",
				},
			];
		return rows;
	}, [items, liveRows, live.status]);

	const filtered = useMemo(() => {
		const q = query.trim().toLowerCase();
		const sorted = [...all].sort((a, b) => a.kind.localeCompare(b.kind));
		if (!q) return sorted;
		return sorted.filter(
			(i) =>
				i.title.toLowerCase().includes(q) || i.detail.toLowerCase().includes(q),
		);
	}, [all, query]);

	function reload() {
		setLive({ status: "pending" });
		setLiveError(null);
		setRunError(null);
		setItems([]);
		apiGet<{
			success?: boolean;
			run_id?: string;
			summary?: Record<string, unknown>;
		}>("/api/v1/pipeline/last")
			.then((last) => {
				if (last.run_id)
					setItems([
						{
							kind: "run",
							title: `Last run ${last.run_id}`,
							detail: JSON.stringify(last.summary ?? {}),
						},
					]);
			})
			.catch((e) =>
				setRunError(e instanceof Error ? e.message : "load failed"),
			);
		apiGet<{
			alerts?: string[];
			checks?: { name: string; ok: boolean; detail?: string }[];
		}>("/api/pipeline/liveness")
			.then((d) =>
				setLive({
					status: "ok",
					alerts: d.alerts ?? [],
					checks: d.checks ?? [],
				}),
			)
			.catch((e) => {
				setLive({ status: "error", message: "" });
				setLiveError(e instanceof Error ? e.message : "load failed");
			});
	}

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
			{(runError || liveError) && (
				<div className="text-sm text-red-400 mb-4">
					{[runError, liveError].filter(Boolean).join(" · ")}{" "}
					<button onClick={reload} className="underline">
						Retry
					</button>
				</div>
			)}
			{!runError &&
				!liveError &&
				filtered.length === 0 &&
				live.status === "ok" && (
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
				{live.status === "pending" && (
					<div
						data-testid="inbox-probing"
						className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-sm text-gray-400"
					>
						<span className="inline-block w-2 h-2 rounded-full bg-yellow-500 animate-pulse mr-2" />
						Probing fleet peers — rows appear as they answer…
					</div>
				)}
			</div>
			<div className="text-sm text-gray-400 mt-3">
				{filtered.length} of {all.length} items
			</div>
		</div>
	);
}
