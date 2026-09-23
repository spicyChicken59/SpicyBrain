// Visual-state review over a served production build (fresh profile per
// context, synthetic state only). For every registered module, every beat and
// every state of the beat's dominant visual, the review opens the beat, selects
// the state and records what actually rendered: the state title shown, node,
// relationship and table-row counts against the authored state, page
// horizontal overflow, and clipped teaching text (an element whose content is
// wider than its box while overflow is hidden, or text extending past the
// figure). Bounded tables scroll on purpose and are not counted as clipping.
// It also runs axe on the first beat of each module in every context.
//
// Usage:
//   node scripts/visual-review.mjs --base http://127.0.0.1:4183/ --out <dir>
//        [--course dbxfe] [--modules id,id] [--shots none|sample|all]
//        [--contexts desktop-dark,phone-light,...]
// Writes <out>/visual-review.json; screenshots of the visual figure go to
// <out>/shots/ (sample: first state of each visual at desktop-dark and the
// last state at phone-light; all: every state in every context).
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import process from "node:process";
import console from "node:console";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const arg = (name, fallback) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
};
const base = arg("--base", "http://127.0.0.1:4183/"),
  out = arg("--out", "test-results/visual-review"),
  courseId = arg("--course", "dbxfe"),
  onlyModules = arg("--modules", ""),
  shots = arg("--shots", "sample"),
  onlyContexts = arg("--contexts", "");
const allContexts = [
  { name: "desktop-dark", width: 1440, height: 900, theme: "dark" },
  { name: "desktop-light", width: 1440, height: 900, theme: "light" },
  { name: "phone-dark", width: 390, height: 844, theme: "dark" },
  { name: "phone-light", width: 390, height: 844, theme: "light" },
  { name: "narrow-light", width: 320, height: 568, theme: "light" },
];
const contexts = onlyContexts
  ? allContexts.filter((c) => onlyContexts.split(",").includes(c.name))
  : allContexts;
const course = JSON.parse(
  readFileSync(`content/courses/${courseId}/course.json`, "utf8"),
);
// A module map entry is either inline ({id, ...}) or a package reference
// ({file: "modules/<id>.json"}) whose module.id is the module's id.
const moduleIds = course.modules
  .map(
    (m) =>
      m.id ??
      JSON.parse(readFileSync(`content/courses/${courseId}/${m.file}`, "utf8"))
        .module.id,
  )
  .filter((id) => !onlyModules || onlyModules.split(",").includes(id));
const modules = moduleIds.map((id) =>
  JSON.parse(readFileSync(`content/teaching/${courseId}/${id}.json`, "utf8")),
);
mkdirSync(`${out}/shots`, { recursive: true });

const browser = await chromium.launch({
  executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});
const records = [];
const axe = [];
const errors = [];
const started = new Date().toISOString();
for (const ctx of contexts) {
  const context = await browser.newContext({
    viewport: { width: ctx.width, height: ctx.height },
    colorScheme: ctx.theme,
  });
  const page = await context.newPage();
  page.on("pageerror", (e) =>
    errors.push({ context: ctx.name, message: e.message }),
  );
  for (const m of modules) {
    const visuals = new Map(m.visuals.map((v) => [v.id, v]));
    for (const [beatIndex, beat] of m.beats.entries()) {
      const visual = visuals.get(beat.visualId);
      await page.goto(`${base}#/module/${m.moduleId}/${beat.id}`);
      const figure = page.locator("main .teaching-visual").first();
      await figure.waitFor({ timeout: 20000 });
      if (beatIndex === 0) {
        const result = await new AxeBuilder({ page }).analyze();
        axe.push({
          context: ctx.name,
          module: m.moduleId,
          route: `#/module/${m.moduleId}/${beat.id}`,
          violations: result.violations.map((v) => ({
            id: v.id,
            impact: v.impact,
            nodes: v.nodes.length,
          })),
        });
      }
      for (const [stateIndex, state] of visual.states.entries()) {
        if (visual.states.length > 1)
          await figure
            .locator(".visual-stages .stage-button")
            .nth(stateIndex)
            .click();
        await page.waitForTimeout(60);
        const seen = await figure.evaluate((fig) => {
          const scene = fig.querySelector(".visual-scene");
          const box = fig.getBoundingClientRect();
          const clipped = [];
          for (const el of scene.querySelectorAll("*")) {
            // Screen-reader-only text is clipped by design; bounded tables
            // scroll on purpose.
            if (el.closest(".sc-sr-only, .teaching-table")) continue;
            const style = globalThis.getComputedStyle(el);
            const hidden = ["hidden", "clip"].includes(style.overflowX);
            const r = el.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) continue;
            if (hidden && el.scrollWidth > el.clientWidth + 1)
              clipped.push(
                `${el.tagName.toLowerCase()}.${el.className}: ${el.textContent.trim().slice(0, 60)}`,
              );
            else if (
              !el.children.length &&
              el.textContent.trim() &&
              (r.right > box.right + 1 || r.left < box.left - 1)
            )
              clipped.push(
                `outside figure: ${el.textContent.trim().slice(0, 60)}`,
              );
          }
          const tables = [...scene.querySelectorAll(".teaching-table")];
          return {
            scrollingTables: tables.filter(
              (t) => t.scrollWidth > t.clientWidth + 1,
            ).length,
            tableHints: scene.querySelectorAll(".table-scroll-hint").length,
            title:
              scene.querySelector(".visual-stage-description strong")
                ?.textContent ?? "",
            nodes: scene.querySelectorAll(".visual-node").length,
            connections: scene.querySelectorAll(".visual-connections > li")
              .length,
            rows: scene.querySelectorAll("tbody tr").length,
            pressed:
              fig.querySelector('.stage-button[aria-pressed="true"]')
                ?.textContent ?? null,
            clipped,
            overflow:
              globalThis.document.documentElement.scrollWidth -
              globalThis.innerWidth,
          };
        });
        const expected = {
          nodes: state.nodes.length,
          connections: state.connections.length,
          rows: state.table ? state.table.rows.length : 0,
        };
        const problems = [];
        if (seen.title !== state.title) problems.push("state title differs");
        for (const k of ["nodes", "connections", "rows"])
          if (seen[k] !== expected[k])
            problems.push(`${k}: rendered ${seen[k]}, authored ${expected[k]}`);
        if (seen.overflow > 0)
          problems.push(`page overflows by ${seen.overflow}px`);
        if (seen.clipped.length) problems.push("clipped text");
        if (seen.scrollingTables > seen.tableHints)
          problems.push("a sideways-scrolling table has no scroll hint");
        const shot =
          shots === "all" ||
          (shots === "sample" &&
            ((ctx.name === "desktop-dark" && stateIndex === 0) ||
              (ctx.name === "phone-light" &&
                stateIndex === visual.states.length - 1)));
        let file = null;
        if (shot) {
          file = `shots/${m.moduleId}--${beat.id}--${state.id}--${ctx.name}.png`;
          await figure.screenshot({ path: `${out}/${file}` });
        }
        records.push({
          context: ctx.name,
          module: m.moduleId,
          beat: beat.id,
          visual: visual.id,
          kind: visual.kind,
          state: state.id,
          rendered: {
            nodes: seen.nodes,
            connections: seen.connections,
            rows: seen.rows,
          },
          overflow: seen.overflow,
          scrollingTables: seen.scrollingTables,
          clipped: seen.clipped,
          ok: problems.length === 0,
          problems,
          ...(file ? { file } : {}),
        });
      }
    }
  }
  await context.close();
}
await browser.close();
const failing = records.filter((r) => !r.ok);
const axeFailing = axe.filter((a) => a.violations.length);
const report = {
  startedAt: started,
  finishedAt: new Date().toISOString(),
  base,
  course: courseId,
  browser: `Chromium ${browser.version()} via Playwright`,
  note: "Fresh profile per context; synthetic state only. Counts compare the rendered state with the authored state; clipping excludes bounded scrolling tables. This is rendered-DOM evidence, not a human judgement that a diagram teaches well.",
  contexts,
  totals: {
    modules: modules.length,
    beats: modules.reduce((n, m) => n + m.beats.length, 0),
    stateRenders: records.length,
    failingStateRenders: failing.length,
    axePages: axe.length,
    axePagesWithViolations: axeFailing.length,
    pageErrors: errors.length,
  },
  failing,
  axe,
  pageErrors: errors,
  records,
};
writeFileSync(
  `${out}/visual-review.json`,
  JSON.stringify(report, null, 1) + "\n",
);
console.log(JSON.stringify(report.totals));
process.exitCode = failing.length || axeFailing.length || errors.length ? 1 : 0;
