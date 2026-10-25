import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../lib/api";
import { useLlm } from "../store/llm";

type ChatMsg = { role: "user" | "assistant" | "system"; content: string };

const PERSONALITIES: Record<string, string> = {
	"VLA Coach":
		"You are a VLA training coach. Prefer event-joint segmentation over equilong chunks. Always ask for failure trajectories, not just successes.",
	"Wall-x Guide":
		"You explain the X Square wall-x stack (Wall-OSS-0.5, WALL-WM, DMuon). Be concrete about checkpoints, roots, and dry-run commands.",
	"Edge Deployer":
		"You help deploy to Raspbot/Boomy edge agents. Prefer X-VLA 0.9B PEFT when the full Wall-OSS model is too heavy.",
	Skeptic:
		"You challenge VLA plans. Point out missing checkpoints, unwired peers, and confirm-gated steps the user skipped.",
};

const EXAMPLE_PROMPTS = [
	"What does my VLA stack health look like?",
	"Plan a cluttered-room data collection session",
	"How do I dry-run DMuon co-training?",
	"Wall-OSS-0.5 vs X-VLA for Raspbot — which?",
	"What are event joints and why not equilong chunks?",
	"My worldlabs peer is unreachable — what now?",
];

const STORE_KEY = "vla-chat";

export default function ChatPage() {
	const [messages, setMessages] = useState<ChatMsg[]>(() => {
		try {
			const raw = localStorage.getItem(STORE_KEY);
			return raw ? (JSON.parse(raw) as ChatMsg[]).slice(-100) : [];
		} catch {
			return [];
		}
	});
	const [input, setInput] = useState("");
	const [personality, setPersonality] = useState("VLA Coach");
	const [custom, setCustom] = useState("");
	const [skillPrompt, setSkillPrompt] = useState("");
	const provider = useLlm((s) => s.provider);
	const model = useLlm((s) => s.model);
	const setDetected = useLlm((s) => s.setDetected);
	const [providerOk, setProviderOk] = useState<boolean | null>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		apiGet<{ skills: { name: string; content?: string }[] }>("/api/skills")
			.then((d) => {
				const skill = d.skills.find((s) => s.name === "vla-expert");
				if (skill?.content) setSkillPrompt(skill.content);
			})
			.catch(() => {});
		apiGet<{ providers: { id: string; detected: boolean }[] }>(
			"/api/llm/discover",
		)
			.then((d) => {
				setDetected(d.providers.filter((p) => p.detected).map((p) => p.id));
				setProviderOk(d.providers.some((p) => p.id === provider && p.detected));
			})
			.catch(() => setProviderOk(false));
	}, [provider, setDetected]);

	useEffect(() => {
		try {
			localStorage.setItem(STORE_KEY, JSON.stringify(messages.slice(-100)));
		} catch {
			/* storage full — keep in memory */
		}
	}, [messages]);

	async function send(text?: string) {
		const content = (text ?? input).trim();
		if (!content || loading) return;
		setError(null);
		const persona =
			personality === "Custom"
				? custom || "You are a helpful VLA assistant."
				: PERSONALITIES[personality];
		const sys = `${skillPrompt}\n\n${persona}`;
		const next: ChatMsg[] = [...messages, { role: "user", content }];
		setMessages(next);
		setInput("");
		setLoading(true);
		try {
			const res = await apiPost<{ text?: string; error?: string }>(
				"/api/llm/chat",
				{
					provider,
					model,
					messages: [{ role: "system", content: sys }, ...next],
				},
			);
			setMessages([
				...next,
				{ role: "assistant", content: res.text || "(empty reply)" },
			]);
		} catch (e) {
			setError(
				e instanceof Error
					? e.message
					: "chat failed — is Ollama/LM Studio running?",
			);
		} finally {
			setLoading(false);
		}
	}

	function clear() {
		setMessages([]);
		try {
			localStorage.removeItem(STORE_KEY);
		} catch {
			/* ignore */
		}
	}

	function exportTxt() {
		const blob = new Blob(
			[
				messages
					.map((m) => `${m.role.toUpperCase()}: ${m.content}`)
					.join("\n\n"),
			],
			{ type: "text/plain" },
		);
		const a = document.createElement("a");
		a.href = URL.createObjectURL(blob);
		a.download = "vla-chat.txt";
		a.click();
		URL.revokeObjectURL(a.href);
	}

	return (
		<div data-testid="chat-page">
			<h1 className="text-2xl font-bold mb-1">Chat</h1>
			<p className="text-gray-400 text-sm mb-4">
				Skill-first VLA assistant. History persists locally (100 msg cap).
			</p>

			<div
				className="flex items-center gap-3 mb-4 flex-wrap"
				data-testid="chat-controls"
			>
				<select
					data-testid="personality-select"
					value={personality}
					onChange={(e) => setPersonality(e.target.value)}
					className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-gray-100"
				>
					{[...Object.keys(PERSONALITIES), "Custom"].map((p) => (
						<option key={p}>{p}</option>
					))}
				</select>
				{personality === "Custom" && (
					<input
						value={custom}
						onChange={(e) => setCustom(e.target.value)}
						placeholder="Custom persona…"
						className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-gray-100"
					/>
				)}
				<span className="text-sm text-gray-400">
					<span
						className={`inline-block w-2 h-2 rounded-full mr-1 ${providerOk === null ? "bg-yellow-500" : providerOk ? "bg-green-500" : "bg-red-500"}`}
					/>
					{provider}
					{model ? ` / ${model}` : " — pick a model in Settings"}
				</span>
				<button
					data-testid="chat-export"
					onClick={exportTxt}
					disabled={messages.length === 0}
					className="text-sm px-2 py-1 rounded bg-gray-800 text-gray-300 disabled:opacity-40"
				>
					Export .txt
				</button>
				<button
					data-testid="chat-clear"
					onClick={clear}
					disabled={messages.length === 0}
					className="text-sm px-2 py-1 rounded bg-gray-800 text-gray-300 disabled:opacity-40"
				>
					Clear
				</button>
			</div>

			<div className="flex flex-wrap gap-2 mb-4" data-testid="example-prompts">
				{EXAMPLE_PROMPTS.map((p) => (
					<button
						key={p}
						onClick={() => send(p)}
						className="text-sm px-2 py-1 rounded-full border border-violet-800 text-violet-300 hover:bg-violet-900/30"
					>
						{p}
					</button>
				))}
			</div>

			<div
				data-testid="chat-messages"
				className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-4 space-y-3 min-h-48 max-h-[50vh] overflow-y-auto"
			>
				{loading && <div className="text-sm text-gray-400">Thinking…</div>}
				{error && (
					<div className="text-sm text-red-400">
						{error}{" "}
						<button onClick={() => send()} className="underline">
							Retry
						</button>
					</div>
				)}
				{!loading && !error && messages.length === 0 && (
					<div className="text-sm text-gray-400">
						No messages yet — pick an example prompt above or ask about your VLA
						stack.
					</div>
				)}
				{messages.map((m, i) => (
					<div
						// biome-ignore lint/suspicious/noArrayIndexKey: append-only transcript, no reorder/delete
						key={i}
						className={m.role === "user" ? "text-right" : "text-left"}
					>
						<span
							className={`inline-block text-sm px-3 py-2 rounded-lg max-w-[85%] whitespace-pre-wrap ${
								m.role === "user"
									? "bg-violet-900/50 text-violet-100"
									: "bg-gray-800 text-gray-100"
							}`}
						>
							{m.content}
						</span>
					</div>
				))}
			</div>

			<div className="flex gap-2">
				<input
					data-testid="chat-input"
					value={input}
					onChange={(e) => setInput(e.target.value)}
					onKeyDown={(e) => e.key === "Enter" && send()}
					placeholder="Ask about Wall-OSS, DMuon, event joints…"
					className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-100"
				/>
				<button
					data-testid="chat-send"
					onClick={() => send()}
					disabled={loading || !input.trim()}
					className="px-4 py-2 rounded bg-violet-700 text-white text-sm disabled:opacity-40"
				>
					Send
				</button>
			</div>
		</div>
	);
}
