import { expect, test } from "@playwright/test";

test("dashboard loads with hero, KPIs, and onboarding cue", async ({
	page,
}) => {
	await page.goto("/");
	await expect(page.getByTestId("dashboard-hero")).toBeVisible();
	await expect(
		page.getByRole("heading", { name: "Vision-Language-Action bridge" }),
	).toBeVisible();
	// KPI cards: Server / Version / Episodes / Tools
	await expect(page.getByText("Server", { exact: true }).first()).toBeVisible();
	// Under-hero onboarding cue (MOCK until a local LLM is detected;
	// waits out the /api/llm/discover provider probes)
	await expect(page.getByTestId("onboarding-cue")).toBeVisible({
		timeout: 20_000,
	});
});

test("backend health is reachable through the vite proxy", async ({
	request,
}) => {
	const res = await request.get("/api/v1/status");
	expect(res.ok()).toBeTruthy();
	const body = await res.json();
	expect(body.server).toBe("vla-mcp");
});

test("nav walk: chat, skills, help, and inbox pages render", async ({ page }) => {
	await page.goto("/chat");
	await expect(page.getByTestId("chat-page")).toBeVisible();
	await page.goto("/skills");
	await expect(page.getByTestId("skills-page")).toBeVisible();
	await page.goto("/help");
	await expect(page.getByTestId("help-page")).toBeVisible();
	await page.getByRole("button", { name: "FAQ" }).click();
	await expect(
		page.getByText("Why does this exist if no robot has been trained?"),
	).toBeVisible();
	await page.getByRole("button", { name: "Models" }).click();
	await expect(
		page.getByText("Wall-OSS-0.5", { exact: true }).first(),
	).toBeVisible();
	await expect(page.getByText("DMuon", { exact: true }).first()).toBeVisible();
	await page.goto("/inbox");
	await expect(page.getByTestId("inbox-page")).toBeVisible();
	await expect(page.getByTestId("search-inbox")).toBeVisible();
});
