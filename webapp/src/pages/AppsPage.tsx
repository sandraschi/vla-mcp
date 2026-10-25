import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../lib/api";

type FleetApp = {
	name: string;
	role: string;
	backend_url?: string;
	frontend_url?: string;
	reachable: boolean;
	experimental: boolean;
};

function AppCard({ app }: { app: FleetApp }) {
	const link = app.frontend_url ?? app.backend_url;
	return (
		<div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
			<div className="flex items-center gap-2 text-sm font-medium text-gray-100">
				<span
					className={`inline-block w-2 h-2 rounded-full ${app.reachable ? "bg-green-500" : "bg-gray-600"}`}
				/>
				{app.name}
			</div>
			<div className="text-sm text-gray-400 mt-1">{app.role}</div>
			{link && (
				<a
					href={link}
					target="_blank"
					rel="noreferrer"
					className="text-sm text-violet-400 hover:text-violet-300 font-mono truncate block mt-1"
				>
					{link}
				</a>
			)}
			<div className="text-sm text-gray-400 mt-1">
				{app.reachable ? "reachable" : "offline"}
			</div>
		</div>
	);
}

export default function AppsPage() {
	const [apps, setApps] = useState<FleetApp[]>([]);
	const [experimental, setExperimental] = useState<FleetApp[]>([]);
	const [query, setQuery] = useState("");
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	function load() {
		setLoading(true);
		setError(null);
		apiGet<{ apps: FleetApp[]; experimental: FleetApp[] }>("/api/fleet/apps")
			.then((d) => {
				setApps(d.apps ?? []);
				setExperimental(d.experimental ?? []);
			})
			.catch((e) => setError(e instanceof Error ? e.message : "load failed"))
			.finally(() => setLoading(false));
	}

	useEffect(load, []);

	const filtered = useMemo(() => {
		const q = query.trim().toLowerCase();
		const keep = (a: FleetApp[]) =>
			q
				? a.filter(
						(x) =>
							x.name.toLowerCase().includes(q) ||
							x.role.toLowerCase().includes(q),
					)
				: a;
		return { apps: keep(apps), experimental: keep(experimental) };
	}, [apps, experimental, query]);

	if (loading)
		return <div className="text-sm text-gray-400">Loading fleet apps…</div>;

	return (
		<div data-testid="apps-page">
			<h1 className="text-2xl font-bold mb-1">Apps Hub</h1>
			<p className="text-gray-400 text-sm mb-4">
				Known fleet apps first; anything else lands in Experimental.
			</p>
			<input
				data-testid="search-apps"
				value={query}
				onChange={(e) => setQuery(e.target.value)}
				placeholder="Search apps…"
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
			{!error &&
				filtered.apps.length === 0 &&
				filtered.experimental.length === 0 && (
					<div className="text-sm text-gray-400">
						No apps match. The fleet bridge may be unconfigured.
					</div>
				)}
			{filtered.apps.length > 0 && (
				<>
					<h2 className="text-lg font-semibold mb-2">Fleet apps</h2>
					<div className="grid gap-3 md:grid-cols-3 mb-6">
						{filtered.apps.map((a) => (
							<AppCard key={a.name} app={a} />
						))}
					</div>
				</>
			)}
			{filtered.experimental.length > 0 && (
				<>
					<h2 className="text-lg font-semibold mb-2">Experimental</h2>
					<div className="grid gap-3 md:grid-cols-3">
						{filtered.experimental.map((a) => (
							<AppCard key={a.name} app={a} />
						))}
					</div>
				</>
			)}
		</div>
	);
}
