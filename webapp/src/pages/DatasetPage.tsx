import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../lib/api";

type Episode = { id: string; source: string; events: string[] };

const PAGE_SIZE = 20;

export default function DatasetPage() {
	const [items, setItems] = useState<Episode[]>([]);
	const [total, setTotal] = useState(0);
	const [query, setQuery] = useState("");
	const [sort, setSort] = useState<"id" | "source">("id");
	const [dir, setDir] = useState<"asc" | "desc">("asc");
	const [page, setPage] = useState(0);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	function load() {
		setLoading(true);
		setError(null);
		apiGet<{ items?: Episode[]; total?: number }>(
			"/api/v1/dataset/episodes?limit=500",
		)
			.then((d) => {
				setItems(d.items ?? []);
				setTotal(d.total ?? d.items?.length ?? 0);
			})
			.catch((e) => setError(e instanceof Error ? e.message : "load failed"))
			.finally(() => setLoading(false));
	}

	useEffect(load, []);

	const filtered = useMemo(() => {
		const q = query.trim().toLowerCase();
		const rows = q
			? items.filter(
					(e) =>
						e.id.toLowerCase().includes(q) ||
						e.source.toLowerCase().includes(q) ||
						e.events?.some((x) => x.toLowerCase().includes(q)),
				)
			: [...items];
		rows.sort((a, b) => {
			const c =
				sort === "id"
					? a.id.localeCompare(b.id)
					: a.source.localeCompare(b.source);
			return dir === "asc" ? c : -c;
		});
		return rows;
	}, [items, query, sort, dir]);

	const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
	const safePage = Math.min(page, pages - 1);
	const visible = filtered.slice(
		safePage * PAGE_SIZE,
		safePage * PAGE_SIZE + PAGE_SIZE,
	);

	if (loading)
		return <div className="text-sm text-gray-400">Loading episodes…</div>;

	return (
		<div data-testid="dataset-page">
			<h1 className="text-2xl font-bold mb-2">Dataset</h1>
			<p className="text-gray-400 text-sm mb-4">
				Event-joint episodes for WALL-WM / DMuon export
			</p>
			{error && (
				<div className="text-sm text-red-400 mb-4">
					{error}{" "}
					<button onClick={load} className="underline">
						Retry
					</button>
				</div>
			)}
			<div className="flex flex-wrap items-center gap-2 mb-3">
				<input
					data-testid="search-episodes"
					value={query}
					onChange={(e) => {
						setQuery(e.target.value);
						setPage(0);
					}}
					placeholder="Search episodes…"
					className="bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100"
				/>
				<select
					data-testid="sort-episodes"
					value={`${sort}:${dir}`}
					onChange={(e) => {
						const [s, d] = e.target.value.split(":");
						setSort(s as "id" | "source");
						setDir(d as "asc" | "desc");
					}}
					className="bg-gray-900 border border-gray-700 rounded px-2 py-2 text-sm text-gray-100"
				>
					<option value="id:asc">ID asc</option>
					<option value="id:desc">ID desc</option>
					<option value="source:asc">Source asc</option>
					<option value="source:desc">Source desc</option>
				</select>
				<span data-testid="episodes-count" className="text-sm text-gray-400">
					{filtered.length} of {total} episodes
				</span>
			</div>
			{!error && filtered.length === 0 && (
				<div className="text-sm text-gray-400">
					No episodes yet — ingest one via{" "}
					<code className="text-violet-300">
						vla_dataset(operation="ingest_episode")
					</code>
					.
				</div>
			)}
			<div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
				<div className="space-y-2 max-h-96 overflow-y-auto">
					{visible.map((ep) => (
						<div
							key={ep.id}
							className="border border-gray-800 rounded p-3 text-sm"
						>
							<code className="text-violet-300">{ep.id}</code>
							<span className="text-gray-300 ml-2 text-sm">{ep.source}</span>
							<div className="mt-1 flex flex-wrap gap-1">
								{ep.events?.map((e) => (
									<span
										key={e}
										className="text-sm bg-gray-800 px-1.5 py-0.5 rounded text-gray-200"
									>
										{e}
									</span>
								))}
							</div>
						</div>
					))}
				</div>
				{pages > 1 && (
					<div className="flex items-center gap-2 mt-3 text-sm text-gray-400">
						<button
							data-testid="episodes-prev"
							disabled={safePage === 0}
							onClick={() => setPage(safePage - 1)}
							className="px-2 py-1 rounded bg-gray-800 disabled:opacity-40"
						>
							Prev
						</button>
						<span>
							Page {safePage + 1} of {pages}
						</span>
						<button
							data-testid="episodes-next"
							disabled={safePage >= pages - 1}
							onClick={() => setPage(safePage + 1)}
							className="px-2 py-1 rounded bg-gray-800 disabled:opacity-40"
						>
							Next
						</button>
					</div>
				)}
			</div>
		</div>
	);
}
