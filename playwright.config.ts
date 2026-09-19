import { defineConfig, devices } from "@playwright/test";
const local = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
export default defineConfig({
  testDir: "./tests/browser",
  timeout: 45000,
  expect: { timeout: 8000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:4183",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: "node scripts/serve.mjs",
    url: "http://127.0.0.1:4183",
    reuseExistingServer: false,
    timeout: 15000,
  },
  projects: [
    {
      name: "chromium-desktop",
      testIgnore: /webkit\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1000 },
        launchOptions: local
          ? {
              executablePath: local,
              args: ["--no-sandbox", "--disable-dev-shm-usage"],
            }
          : {},
      },
    },
    ...(process.env.SKIP_WEBKIT
      ? []
      : [
          {
            name: "webkit-mobile",
            testMatch: /webkit\.spec\.ts/,
            use: { ...devices["iPhone 13"], browserName: "webkit" as const },
          },
        ]),
  ],
});
