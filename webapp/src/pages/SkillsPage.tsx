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
				<div className="text-sm text-gray-400">No skills registered.</div>
			)}
			<div className="divide-y divide-gray-800 border-y border-gray-800">
				{skills.map((s) => (
					<details key={s.uri} className="py-3">
						<summary className="cursor-pointer">
							<span className="text-sm font-medium text-gray-100">
								{s.name}
							</span>
							<span className="block text-xs text-violet-300 font-mono mt-0.5">
								{s.uri}
							</span>
							<span className="block text-sm text-gray-400 mt-1">
								{s.description}
							</span>
						</summary>
						{s.content && (
							<pre className="mt-2 text-sm text-gray-300 whitespace-pre-wrap">
								{s.content.slice(0, 4000)}
							</pre>
						)}
					</details>
				))}
			</div>
		</div>
	);
}
