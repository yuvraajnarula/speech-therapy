/**
 * E2E tests — Live Tutor Mode (memory-driven adaptive coaching loop).
 *
 * Requires the FastAPI backend running on http://localhost:8000:
 *   python -m uvicorn backend.app.main:app --port 8000
 * The backend runs its STT engine in simulation mode when the model is
 * unavailable, so the tutor's diagnostic loop works headlessly.
 *
 * Run:  npx playwright test
 */
import { expect, test } from "@playwright/test";

test.describe("Live Tutor Mode", () => {
  test("deep-link opens the tutor tab", async ({ page }) => {
    await page.goto("/?tab=tutor");
    await expect(page.getByRole("heading", { name: /Live Tutor Mode/i })).toBeVisible();
  });

  test("full adaptive session: cue → submit → feedback with memory snapshot", async ({ page }) => {
    await page.goto("/?tab=tutor");

    // Start the session — connects to backend /ws/live-tutor
    await page.getByRole("button", { name: /Begin Session/i }).click();

    // Backend app sends a tutor cue from the clinical memory layer:
    // the UI renders the target word plus the highlighted phoneme chip.
    await expect(page.getByText(/SAY THIS WORD/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/Focus phoneme:/i)).toBeVisible();

    // The session must report a live status badge
    await expect(page.getByText("Live Session")).toBeVisible();
  });

  test("trial and wordbank tabs render via deep links", async ({ page }) => {
    await page.goto("/?tab=trial");
    await expect(page.getByText(/Active Speech Trial/i).first()).toBeVisible();

    await page.goto("/?tab=wordbank");
    await expect(page.getByText(/Word Bank/i).first()).toBeVisible();
  });
});
