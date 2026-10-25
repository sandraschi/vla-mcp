/// <reference types="vite/client" />

// Same-origin relative by default (vite proxy); absolute backend URL only
// behind a Tauri gate — an absolute LAN URL from a non-localhost tab dies on CORS.
const _w = window as unknown as Record<string, unknown>;
const _isTauri = "__TAURI__" in _w || "__TAURI_INTERNALS__" in _w;
const API_BASE =
	import.meta.env.DEV || !_isTauri ? "" : "http://127.0.0.1:11024";

export type ApiOptions = {
	confirm?: boolean;
	/** Abort the request after this many ms (default 30s). Prevents pages
	hanging forever on a stalled backend/supervisor probe. */
	timeoutMs?: number;
};

const DEFAULT_TIMEOUT_MS = 30_000;

function withTimeout(timeoutMs: number) {
	const ctrl = new AbortController();
	const timer = window.setTimeout(() => ctrl.abort(), timeoutMs);
	return {
		signal: ctrl.signal,
		done: () => window.clearTimeout(timer),
	};
}

export async function apiGet<T = Record<string, unknown>>(
	path: string,
	options?: ApiOptions,
): Promise<T> {
	const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
	const t = withTimeout(timeoutMs);
	try {
		const res = await fetch(`${API_BASE}${path}`, { signal: t.signal });
		if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
		return res.json() as Promise<T>;
	} catch (e) {
		if (e instanceof DOMException && e.name === "AbortError")
			throw new Error(
				`request timed out after ${Math.round(timeoutMs / 1000)}s (${path})`,
			);
		throw e;
	} finally {
		t.done();
	}
}

export async function apiPost<T = Record<string, unknown>>(
	path: string,
	body?: unknown,
	options?: ApiOptions,
): Promise<T> {
	const headers: Record<string, string> = {
		"Content-Type": "application/json",
	};
	if (options?.confirm) {
		headers["X-VLA-Confirm"] = "1";
	}
	const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
	const t = withTimeout(timeoutMs);
	try {
		const res = await fetch(`${API_BASE}${path}`, {
			method: "POST",
			headers,
			body: body ? JSON.stringify(body) : undefined,
			signal: t.signal,
		});
		if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
		return res.json() as Promise<T>;
	} catch (e) {
		if (e instanceof DOMException && e.name === "AbortError")
			throw new Error(
				`request timed out after ${Math.round(timeoutMs / 1000)}s (${path})`,
			);
		throw e;
	} finally {
		t.done();
	}
}

export async function apiDelete<T = Record<string, unknown>>(
	path: string,
	options?: ApiOptions,
): Promise<T> {
	const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;
	const t = withTimeout(timeoutMs);
	try {
		const res = await fetch(`${API_BASE}${path}`, {
			method: "DELETE",
			signal: t.signal,
		});
		if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
		return res.json() as Promise<T>;
	} catch (e) {
		if (e instanceof DOMException && e.name === "AbortError")
			throw new Error(
				`request timed out after ${Math.round(timeoutMs / 1000)}s (${path})`,
			);
		throw e;
	} finally {
		t.done();
	}
}
