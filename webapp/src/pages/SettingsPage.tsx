import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../lib/api";
import { useLlm } from "../store/llm";

type Provider = {
	id: string;
	label: string;
	detected: boolean;
	base_url: string;
};
type Cloud = { id: string; label: string; configured: boolean };

export default function SettingsPage() {
	const [providers, setProviders] = useState<Provider[]>([]);
	const [cloud, setCloud] = useState<Cloud[]>([]);
	const [models, setModels] = useState<string[]>([]);
	const [live, setLive] = useState(false);
	const provider = useLlm((s) => s.provider);
	const model = useLlm((s) => s.model);
	const setProvider = useLlm((s) => s.setProvider);
	const setModel = useLlm((s) => s.setModel);
	const setDetected = useLlm((s) => s.setDetected);
	const setGpuNote = useLlm((s) => s.setGpuNote);
	const [device, setDevice] = useState("");
	const [testResult, setTestResult] = useState<string | null>(null);
	const [testing, setTesting] = useState(false);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	function load() {
		setLoading(true);
		setError(null);
		Promise.all([
			apiGet<{ providers: Provider[]; cloud: Cloud[] }>("/api/llm/providers"),
			apiGet<{ server?: string; device?: string }>("/api/v1/status"),
		])
			.then(([p, s]) => {
				setProviders(p.providers);
				setCloud(p.cloud);
				setDevice(String(s.device ?? ""));
				setDetected(p.providers.filter((x) => x.detected).map((x) => x.id));
				setGpuNote(`Compute device: ${String(s.device ?? "?")}.`);
			})
			.catch((e) => setError(e instanceof Error ? e.message : "load failed"))
			.finally(() => setLoading(false));
	}

	useEffect(load, []);

	useEffect(() => {
		apiGet<{ models: string[]; live: boolean }>(
			`/api/llm/models?provider=${provider}`,
		)
			.then((d) => {
				setModels(d.models);
				setLive(d.live);
				if (d.models.length > 0 && !useLlm.getState().model)
					setModel(d.models[0]);
			})
			.catch(() => {
				setModels([]);
				setLive(false);
			});
	}, [provider, setModel]);

	function save(nextProvider: string, nextModel: string) {
		setProvider(nextProvider);
		setModel(nextModel);
	}

	async function test() {
		setTesting(true);
		setTestResult(null);
		try {
			const res = await apiPost<{ text?: string }>("/api/llm/chat", {
				provider,
				model,
				messages: [{ role: "user", content: "Reply with OK" }],
			});
			setTestResult(res.text ? `OK: ${res.text.slice(0, 120)}` : "Empty reply");
		} catch (e) {
			setTestResult(e instanceof Error ? `FAIL: ${e.message}` : "FAIL");
		} finally {
			setTesting(false);
		}
	}

	if (loading)
		return <div className="text-sm text-gray-400">Loading providers…</div>;
	if (error)
		return (
			<div className="text-sm text-red-400" data-testid="settings-page">
				{error}{" "}
				<button onClick={load} className="underline">
					Retry
				</button>
			</div>
		);

	return (
		<div data-testid="settings-page">
			<h1 className="text-2xl font-bold mb-1">Settings</h1>
			<p className="text-gray-400 text-sm mb-4">
				Local LLM providers are free. Cloud keys are configured server-side —
				never pasted here.
			</p>

			<div data-testid="llm-onboarding" className="text-sm text-gray-400 mb-4">
				{providers.some((p) => p.detected)
					? "A local provider is detected — pick it below and chat for free."
					: "No local LLM detected. Install Ollama (https://ollama.me), run `ollama pull qwen3:8b`, then Test."}
				{device && (
					<span className="ml-2 text-gray-500">Compute device: {device}.</span>
				)}
			</div>

			<div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
				{providers.map((p) => (
					<div
						key={p.id}
						data-testid={`llm-provider-card-${p.id}`}
						className={`bg-gray-900 border rounded-lg p-4 ${provider === p.id ? "border-violet-600" : "border-gray-800"}`}
					>
						<div className="flex items-center gap-2 text-sm font-medium text-gray-100 mb-1">
							<span
								className={`inline-block w-2 h-2 rounded-full ${p.detected ? "bg-green-500" : "bg-gray-600"}`}
							/>
							{p.label}
						</div>
						<div className="text-xs text-gray-500 mb-3">
							{p.detected ? "detected" : "not found"}
						</div>
						<button
							onClick={() => save(p.id, model)}
							className="text-xs px-2 py-1 rounded bg-gray-800 text-gray-200"
						>
							{provider === p.id ? "Selected" : "Select"}
						</button>
					</div>
				))}
				{cloud.map((c) => (
					<div
						key={c.id}
						data-testid={`llm-provider-card-${c.id}`}
						className="bg-gray-900 border border-gray-800 rounded-lg p-4"
					>
						<div className="flex items-center gap-2 text-sm font-medium text-gray-100 mb-1">
							<span
								className={`inline-block w-2 h-2 rounded-full ${c.configured ? "bg-green-500" : "bg-gray-600"}`}
							/>
							{c.label}
						</div>
						<div
							className="text-xs text-gray-500"
							data-testid={`llm-key-${c.id}`}
						>
							{c.configured
								? "key configured on server"
								: "no key configured (set env on server)"}
						</div>
					</div>
				))}
			</div>

			<div className="flex items-center gap-2 flex-wrap">
				<label className="text-sm text-gray-400" htmlFor="llm-provider">
					Provider
				</label>
				<select
					id="llm-provider"
					data-testid="llm-provider-select"
					value={provider}
					onChange={(e) => save(e.target.value, "")}
					className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-gray-100"
				>
					{providers.map((p) => (
						<option key={p.id} value={p.id}>
							{p.label}
						</option>
					))}
				</select>
				<label className="text-sm text-gray-400" htmlFor="llm-model">
					Model
				</label>
				<select
					id="llm-model"
					data-testid="llm-model-select"
					value={model}
					onChange={(e) => save(provider, e.target.value)}
					className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-gray-100"
				>
					{models.length === 0 && (
						<option value="">
							(no models{live ? "" : " — provider offline"})
						</option>
					)}
					{models.map((m) => (
						<option key={m} value={m}>
							{m}
						</option>
					))}
				</select>
				<button
					data-testid="llm-test-chat"
					onClick={test}
					disabled={testing}
					className="text-xs px-3 py-1 rounded bg-violet-700 text-white disabled:opacity-40"
				>
					{testing ? "Testing…" : "Test"}
				</button>
				{testResult && (
					<span className="text-xs text-gray-300">{testResult}</span>
				)}
			</div>
		</div>
	);
}
