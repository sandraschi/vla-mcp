import { create } from "zustand";

// Global LLM provider/model state (WEBAPP_SOTA_STANDARDS.md s.VI).
// Persisted to localStorage under llm_provider / llm_model.

type LlmState = {
	provider: string;
	model: string;
	detected: string[];
	gpuNote: string;
	setProvider: (provider: string) => void;
	setModel: (model: string) => void;
	setDetected: (detected: string[]) => void;
	setGpuNote: (note: string) => void;
};

function read(key: string, fallback: string): string {
	try {
		return localStorage.getItem(key) ?? fallback;
	} catch {
		return fallback;
	}
}

function write(key: string, value: string): void {
	try {
		localStorage.setItem(key, value);
	} catch {
		// private mode - keep in memory
	}
}

export const useLlm = create<LlmState>()((set) => ({
	provider: read("llm_provider", "ollama"),
	model: read("llm_model", ""),
	detected: [],
	gpuNote: "",
	setProvider: (provider) =>
		set(() => {
			write("llm_provider", provider);
			return { provider };
		}),
	setModel: (model) =>
		set(() => {
			write("llm_model", model);
			return { model };
		}),
	setDetected: (detected) => set(() => ({ detected })),
	setGpuNote: (gpuNote) => set(() => ({ gpuNote })),
}));
