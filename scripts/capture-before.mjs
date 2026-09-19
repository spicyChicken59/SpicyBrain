// Public-safe before-interface evidence; run before changing the learner views.
import { spawn } from "node:child_process";
import process from "node:process";
import { setTimeout } from "node:timers";
import { mkdir, writeFile, readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { chromium } from "playwright";
const server = spawn(process.execPath, ["scripts/serve.mjs"], {
  windowsHide: true,
  stdio: "ignore",
});
let browser;
try {
  for (let i = 0; i < 50; i++) {
    try {
      if ((await globalThis.fetch("http://127.0.0.1:4183/")).ok) break;
    } catch {
      /* server starting */
    }
    await new Promise((r) => setTimeout(r, 100));
  }
  browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
  });
  await mkdir("docs/evidence/study-hub", { recursive: true });
  await page.goto("http://127.0.0.1:4183/");
  await page.locator("main h1").waitFor();
  await page.screenshot({
    path: "docs/evidence/study-hub/before-today-desktop.png",
  });
  await page.goto("http://127.0.0.1:4183/#/lesson/dbxfe-m04-l01");
  await page.locator(".reader").waitFor();
  await page.screenshot({
    path: "docs/evidence/study-hub/before-reader-desktop.png",
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:4183/");
  await page.locator("main h1").waitFor();
  await page.screenshot({
    path: "docs/evidence/study-hub/before-today-mobile.png",
  });
  await writeFile(
    "docs/evidence/study-hub/before.json",
    JSON.stringify(
      {
        at: new Date().toISOString(),
        base: "a3e858937ef72b0f7a6a474650def0b7b9e8ab23",
        browser: browser.version(),
        evidence:
          "Real loopback production browser; baseline interface before hub changes. Build verification recognizes CRLF text; static server supports Windows paths; study schema migration is present but empty state is used.",
        appSha256: createHash("sha256")
          .update(await readFile("src/App.tsx"))
          .digest("hex"),
        readerSha256: createHash("sha256")
          .update(await readFile("src/reader.tsx"))
          .digest("hex"),
      },
      null,
      2,
    ),
  );
} finally {
  await browser?.close();
  server.kill();
}
