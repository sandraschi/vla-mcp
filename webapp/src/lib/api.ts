const API_BASE = import.meta.env.DEV ? "" : "http://127.0.0.1:11024";

export async function apiGet<T = Record<string, unknown>>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export async function apiPost<T = Record<string, unknown>>(
  path: string,
  body?: unknown,
  options?: { confirm?: boolean },
): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (options?.confirm) {
    headers["X-VLA-Confirm"] = "1";
  }
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}
