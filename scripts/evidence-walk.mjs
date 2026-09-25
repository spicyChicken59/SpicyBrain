// Reproducible screenshot walk over a served production build (fresh profile,
// synthetic state only). Usage:
//   node scripts/evidence-walk.mjs --base http://127.0.0.1:4183/ --out <dir> [--routes routes.json] [--label text]
// Routes file: [{"name": "...", "hash": "#/..."}]. Defaults cover the main journey.
import { chromium } from "playwright";
import process from "node:process";
import console from "node:console";
import { writeFileSync, mkdirSync, readFileSync } from "node:fs";
const arg = (name, fallback) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
};
const base = arg("--base", "http://127.0.0.1:4183/"),
  out = arg("--out", "test-results/evidence-walk"),
  label = arg("--label", ""),
  routesFile = arg("--routes", "");
const routes = routesFile
  ? JSON.parse(readFileSync(routesFile, "utf8"))
  : [
      { name: "today", hash: "#/" },
      { name: "courses", hash: "#/courses" },
      { name: "course-map", hash: "#/course/dbxfe" },
      { name: "deck", hash: "#/module/dbxfe-delta/dbxfe-delta-folder" },
      {
        name: "handbook",
        hash: "#/module/dbxfe-delta/dbxfe-delta-folder?view=handbook",
      },
      {
        name: "cards",
        hash: "#/module/dbxfe-delta/dbxfe-delta-folder?view=cards",
      },
      { name: "lesson", hash: "#/lesson/dbxfe-m03-l02" },
      { name: "practice", hash: "#/practice" },
      { name: "review", hash: "#/review" },
      { name: "notebook", hash: "#/notebook" },
      { name: "search", hash: "#/search" },
      { name: "settings", hash: "#/settings" },
    ];
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});
const shots = [];
for (const [width, height, tag] of [
  [1440, 900, "desktop"],
  [1280, 800, "laptop"],
  [820, 1180, "tablet"],
  [390, 844, "phone"],
  [320, 568, "narrow"],
]) {
  for (const theme of ["dark", "light"]) {
    const context = await browser.newContext({
      viewport: { width, height },
      colorScheme: theme,
    });
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    for (const route of routes) {
      await page.goto(base + route.hash);
      await page.waitForSelector("main h1", { timeout: 20000 });
      await page.waitForTimeout(350);
      const overflow = await page.evaluate(
        () =>
          globalThis.document.documentElement.scrollWidth -
          globalThis.innerWidth,
      );
      const file = `${route.name}-${tag}-${theme}.png`;
      await page.screenshot({ path: `${out}/${file}`, fullPage: false });
      shots.push({
        file,
        route: route.hash,
        width,
        height,
        theme,
        overflow,
        h1: (await page.locator("main h1").first().innerText()).slice(0, 80),
      });
    }
    shots.push({ context: `${tag}-${theme}`, pageErrors: errors });
    await context.close();
  }
}
await browser.close();
writeFileSync(
  `${out}/manifest.json`,
  JSON.stringify(
    {
      capturedAt: new Date().toISOString(),
      label,
      base,
      browser: "Chromium via Playwright",
      note: "Fresh profile per context; synthetic state only.",
      shots,
    },
    null,
    2,
  ) + "\n",
);
console.log(
  "captured",
  shots.filter((s) => s.file).length,
  "screenshots into",
  out,
);
