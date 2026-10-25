import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../lib/api";

export default function ToolsPage() {
	const [tools, setTools] = useState<string[]>([]);
	const [query, setQuery] = useState("");
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	function load() {
		setLoading(true);
		setError(null);
		apiGet<{ tools?: string[] }>("/api/v1/tools")
			.then((d) => setTools(d.tools ?? []))
			.catch((e) => setError(e instanceof Error ? e.message : "load failed"))
			.finally(() => setLoading(false));
	}

	useEffect(load, []);

	const visible = useMemo(() => {
		const q = query.trim().toLowerCase();
		const rows = [...tools].sort();
		return q ? rows.filter((t) => t.toLowerCase().includes(q)) : rows;
	}, [tools, query]);

	if (loading)
		return <div className="text-sm text-gray-400">Loading tools…</div>;

	return (
		<div data-testid="tools-page">
			<h1 className="text-2xl font-bold mb-2">Tools</h1>
			<p className="text-gray-400 text-sm mb-4">
				{tools.length} portmanteau MCP tools
			</p>
			{error && (
				<div className="text-sm text-red-400 mb-4">
					{error}{" "}
					<button onClick={load} className="underline">
						Retry
					</button>
				</div>
			)}
			<input
				data-testid="search-tools"
				value={query}
				onChange={(e) => setQuery(e.target.value)}
				placeholder="Search tools…"
				className="w-full max-w-md bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100 mb-3"
			/>
			{!error && visible.length === 0 && (
				<div className="text-sm text-gray-400">No tools match.</div>
			)}
			<div className="grid grid-cols-2 md:grid-cols-3 gap-2">
				{visible.map((t) => (
					<code
						key={t}
						className="text-sm bg-gray-900 border border-gray-800 px-2 py-2 rounded text-violet-200"
					>
						{t}
					</code>
				))}
			</div>
			<div className="text-sm text-gray-400 mt-2">
				{visible.length} of {tools.length} tools
			</div>
		</div>
	);
}
