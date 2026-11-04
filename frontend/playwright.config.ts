import { defineConfig } from "@playwright/test";

/**
 * Playwright E2E configuration — IndicAST Clinical Studio.
 *
 * Uses the system-installed Chrome (channel: "chrome") so no browser
 * download is required. Both the FastAPI backend (:8000) and the Vite dev
 * server (:5173) are started automatically.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  retries: 0,
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "python -m uvicorn backend.app.main:app --port 8000",
      url: "http://localhost:8000/health",
      cwd: "..",
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: "npm run dev -- --strictPort",
      url: "http://localhost:5173",
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
  projects: [
    {
      name: "chrome",
      use: {
        // @ts-expect-error — channel is a LaunchOptions member exposed in use
        channel: "chrome",
      },
    },
  ],
});
