import { defineConfig } from "@playwright/test";

export default defineConfig({
	testDir: "./e2e",
	timeout: 60_000,
	retries: 0,
	use: { baseURL: "http://127.0.0.1:11025" },
	webServer: [
		{
			command:
				"uv run uvicorn vla_mcp.server:app --host 127.0.0.1 --port 11024",
			port: 11024,
			reuseExistingServer: true,
			timeout: 60_000,
		},
		{
			command: "npm run dev -- --port 11025 --host 127.0.0.1",
			port: 11025,
			reuseExistingServer: true,
			timeout: 60_000,
		},
	],
});
