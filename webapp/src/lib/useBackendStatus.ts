import { useCallback, useEffect, useRef, useState } from "react";
import { apiGet } from "./api";

export type BackendState = "connecting" | "connected" | "error";

function isTauri(): boolean {
	const w = window as unknown as Record<string, unknown>;
	return "__TAURI__" in w || "__TAURI_INTERNALS__" in w;
}

// Listens for the native sidecar's backend-status Tauri event and falls back
// to HTTP polling. Restart invokes the sidecar's start_backend command
// (Tauri only); in a dev browser it re-probes the health endpoint.
export function useBackendStatus() {
	const [state, setState] = useState<BackendState>("connecting");
	const [lastError, setLastError] = useState("");
	const tauriError = useRef(false);

	const poll = useCallback(async () => {
		try {
			await apiGet("/api/v1/status");
			if (!tauriError.current) setState("connected");
		} catch {
			if (!tauriError.current) {
				setState("error");
				setLastError("backend unreachable");
			}
		}
	}, []);

	useEffect(() => {
		let cancelled = false;
		let unlisten: (() => void) | undefined;
		(async () => {
			if (isTauri()) {
				try {
					const { listen } = await import("@tauri-apps/api/event");
					if (cancelled) return;
					unlisten = await listen<string>("backend-status", (event) => {
						if (cancelled) return;
						if (event.payload === "ready") {
							tauriError.current = false;
							setLastError("");
							setState("connected");
						} else if (event.payload?.startsWith("error:")) {
							tauriError.current = true;
							setLastError(event.payload);
							setState("error");
						}
					});
				} catch {
					// not under Tauri - HTTP polling covers it
				}
			}
		})();
		void poll();
		const timer = window.setInterval(() => void poll(), 15000);
		return () => {
			cancelled = true;
			window.clearInterval(timer);
			if (unlisten) unlisten();
		};
	}, [poll]);

	const restart = useCallback(async () => {
		setState("connecting");
		if (isTauri()) {
			try {
				const { invoke } = await import("@tauri-apps/api/core");
				tauriError.current = false;
				setLastError("");
				await invoke("start_backend");
			} catch (e) {
				tauriError.current = true;
				setLastError(e instanceof Error ? e.message : "restart failed");
				setState("error");
				return;
			}
		}
		await poll();
	}, [poll]);

	return { state, lastError, restart, isTauri: isTauri() };
}
