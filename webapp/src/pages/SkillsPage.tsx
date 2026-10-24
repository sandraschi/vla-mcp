import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

type Skill = {
	uri: string;
	name: string;
	description: string;
	content?: string;
};

export default function SkillsPage() {
	const [skills, setSkills] = useState<Skill[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	function load() {
		setLoading(true);
		setError(null);
		apiGet<{ skills: Skill[] }>("/api/skills")
			.then((d) => setSkills(d.skills ?? []))
			.catch((e) => setError(e instanceof Error ? e.message : "load failed"))
			.finally(() => setLoading(false));
	}

	useEffect(load, []);

	if (loading)
		return <div className="text-sm text-gray-400">Loading skills…</div>;

	return (
		<div data-testid="skills-page">
			<h1 className="text-2xl font-bold mb-1">Skills</h1>
			<p className="text-gray-400 text-sm mb-4">
				Domain skills the Chat page loads as its system preprompt.
			</p>
			{error && (
				<div className="text-sm text-red-400 mb-4">
					{error}{" "}
					<button onClick={load} className="underline">
						Retry
					</button>
				</div>
			)}
			{!error && skills.length === 0 && (
				<div className="text-sm text-gray-500">No skills registered.</div>
			)}
			<div className="space-y-3">
				{skills.map((s) => (
					<div
						key={s.uri}
						className="bg-gray-900 border border-gray-800 rounded-lg p-4"
					>
						<div className="text-sm font-medium text-gray-100">{s.name}</div>
						<div className="text-xs text-violet-300 font-mono mt-0.5">
							{s.uri}
						</div>
						<div className="text-sm text-gray-400 mt-1">{s.description}</div>
						{s.content && (
							<pre className="bg-gray-950 border border-gray-800 rounded p-3 text-xs text-gray-300 overflow-x-auto mt-2 max-h-64 overflow-y-auto whitespace-pre-wrap">
								{s.content.slice(0, 4000)}
							</pre>
						)}
					</div>
				))}
			</div>
		</div>
	);
}
