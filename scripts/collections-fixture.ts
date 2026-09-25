/**
 * Course-collections proof (`npm run test:collections`).
 *
 * Copies the project into an isolated temporary directory, adds the
 * synthetic `hearth` course from tests/fixtures/collections/content (tracks,
 * routes, labs, field guides, a case analysis, a crosswalk entry, a module
 * package file and two capstones), builds the production bundle, serves it
 * and drives Chromium through every collection view. The fixture adds only
 * content inputs; removing it restores the release catalog, and the engine
 * files are compared before and after (`runtimeSourceChanges: []`).
 */
import {
  cp,
  mkdir,
  mkdtemp,
  readdir,
  readFile,
  rm,
  symlink,
  writeFile,
} from "node:fs/promises";
import { join, resolve, extname, sep } from "node:path";
import { tmpdir } from "node:os";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import { chromium, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { buildContent, loadCourses, root } from "./content.ts";
import { noOverflow, stored } from "../tests/browser/helpers.ts";
import type { Course } from "../src/content-schema.ts";

const fixture = join(root, "tests/fixtures/collections/content");
const temp = await mkdtemp(join(tmpdir(), "spicybrain-collections-"));
const tempBase = resolve(tmpdir());
if (!resolve(temp).startsWith(tempBase + sep + "spicybrain-collections-"))
  throw Error("Unsafe collections-test directory");
async function removeTemporaryTree(target: string) {
  const absolute = resolve(target);
  if (absolute !== resolve(temp) && !absolute.startsWith(resolve(temp) + sep))
    throw Error("Cleanup escaped collections-test directory");
  await rm(absolute, { recursive: true, force: true });
}
async function manifest(
  folder: string,
  prefix = "",
): Promise<Record<string, string>> {
  const out: Record<string, string> = {};
  for (const f of await readdir(folder, { withFileTypes: true })) {
    const relative = prefix + f.name;
    if (
      [
        "node_modules",
        ".git",
        "dist",
        "dist-nested",
        "test-results",
        "playwright-report",
      ].includes(f.name)
    )
      continue;
    if (f.isDirectory())
      Object.assign(out, await manifest(join(folder, f.name), relative + "/"));
    else
      out[relative] = createHash("sha256")
        .update(await readFile(join(folder, f.name)))
        .digest("hex");
  }
  return out;
}
const diff = (a: Record<string, string>, b: Record<string, string>) =>
  [...new Set([...Object.keys(a), ...Object.keys(b)])]
    .sort()
    .filter((k) => a[k] !== b[k])
    .map((path) => ({ path, before: a[path] ?? null, after: b[path] ?? null }));
const build = async () => {
  const courses = await buildContent(join(temp, "content"), temp);
  execFileSync(
    process.execPath,
    [join(root, "node_modules/vite/bin/vite.js"), "build"],
    {
      cwd: temp,
      env: { ...process.env, APP_BASE: "./", APP_OUT: "dist" },
      stdio: "pipe",
    },
  );
  return courses;
};
const mime: Record<string, string> = {
  ".html": "text/html",
  ".js": "application/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".json": "application/json",
  ".zip": "application/zip",
};
const requests: string[] = [];
const server = createServer(async (req, res) => {
  try {
    const path = decodeURIComponent(new URL(req.url!, "http://local").pathname),
      base = resolve(temp, "dist"),
      file = resolve(
        base,
        "." + path + (path.endsWith("/") ? "index.html" : ""),
      );
    if (!file.startsWith(base + sep)) throw Error();
    requests.push(path);
    res.setHeader(
      "Content-Type",
      mime[extname(file)] || "application/octet-stream",
    );
    res.setHeader("Cache-Control", "no-store");
    res.end(await readFile(file));
  } catch {
    res.statusCode = 404;
    res.end("Not found");
  }
});
const evidence = join(root, "test-results/evidence");
const assertions: string[] = [];
const pass = (claim: string) => {
  assertions.push(claim);
  console.log(`ok - ${claim}`);
};
let browser: Awaited<ReturnType<typeof chromium.launch>> | undefined;
try {
  for (const path of [
    "src",
    "content",
    "public",
    "index.html",
    "vite.config.ts",
    "package.json",
    "tsconfig.json",
  ])
    await cp(join(root, path), join(temp, path), { recursive: true });
  await symlink(
    join(root, "node_modules"),
    join(temp, "node_modules"),
    process.platform === "win32" ? "junction" : "dir",
  );
  const before = await manifest(temp);
  const baselineCourseIds = (await loadCourses(join(temp, "content"))).map(
    (c) => c.id,
  );
  await cp(fixture, join(temp, "content"), { recursive: true });
  const addition = diff(before, await manifest(temp));
  expect(addition.length).toBeGreaterThan(0);
  expect(addition.every((f) => f.path.startsWith("content/"))).toBe(true);
  pass("The fixture adds only content inputs");
  const catalog = await build();
  expect(catalog.map((c) => c.id)).toEqual(
    [...baselineCourseIds, "hearth"].sort(),
  );
  const hearth: Course = catalog.find((c) => c.id === "hearth")!;
  expect(hearth.tracks).toHaveLength(2);
  expect(hearth.routes).toHaveLength(2);
  expect(hearth.labs).toHaveLength(2);
  expect(hearth.guides).toHaveLength(2);
  expect(hearth.cases).toHaveLength(1);
  expect(hearth.crosswalk).toHaveLength(1);
  expect(hearth.scenarios.filter((s) => s.isCapstone)).toHaveLength(2);
  pass(
    "Discovery: 3 modules (one from a module package), 2 tracks, 2 routes, 2 labs, 2 guides, 1 case, 1 crosswalk row, 2 capstones",
  );
  await new Promise<void>((r) => server.listen(0, "127.0.0.1", r));
  const address = server.address();
  if (!address || typeof address === "string") throw Error("No port");
  const url = `http://127.0.0.1:${address.port}`;
  browser = await chromium.launch({
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    acceptDownloads: true,
  });
  const page = await context.newPage();
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const go = async (hash: string) => {
    await page.goto(url + "/" + hash);
    await expect(page.locator("main h1")).toBeVisible();
  };
  const nav = async (hash: string) => {
    await page.evaluate((h) => {
      location.hash = h;
    }, hash);
    await expect(page.locator("main h1")).toBeVisible();
  };
  const moduleRequests = () =>
    requests.filter((p) => /\/teaching\/hearth-hearth-m0\d\.json$/.test(p));
  const shot = async (name: string) => {
    await mkdir(evidence, { recursive: true });
    await page.screenshot({
      path: join(evidence, `collections-${name}.png`),
      animations: "disabled",
    });
  };

  // Course card counts.
  await go("#/courses");
  const card = page
    .locator(".teacher-course-card")
    .filter({ hasText: hearth.title });
  await expect(card.getByText("3 modules", { exact: true })).toBeVisible();
  await expect(
    card.getByText("2 tracks · 2 labs · 2 field guides", { exact: true }),
  ).toBeVisible();
  pass("Course card shows module, track, lab and guide counts");

  // Course map grouped by track, routes and the collections strip.
  requests.length = 0;
  await card.click();
  await expect(page).toHaveURL(/#\/course\/hearth$/);
  await expect(page.locator("main h1")).toBeFocused();
  for (const track of hearth.tracks!) {
    const section = page.locator(".academy-track").filter({
      has: page.getByRole("heading", { level: 2, name: track.title }),
    });
    await expect(section.getByText(track.summary)).toBeVisible();
    await expect(section.locator(".teacher-module-map>li")).toHaveCount(
      track.moduleIds.length,
    );
    await expect(
      section.getByRole("link", { name: "Handbook for this track" }),
    ).toHaveAttribute("href", `#/handbook/hearth?track=${track.id}`);
  }
  await expect(page.locator(".teacher-module-map>li")).toHaveCount(3);
  expect(
    await page.locator(".teacher-module-map .module-index").allTextContents(),
  ).toEqual(["01", "02", "03"]);
  await expect(page.locator(".teacher-module-map h3")).toHaveCount(3);
  await expect(page.locator(".teacher-module-map .module-open")).toHaveCount(3);
  const m02Item = page
    .locator(".teacher-module-map>li")
    .filter({ hasText: "Hydration and dough strength" });
  await expect(m02Item.locator(".academy-builds-on")).toContainText(
    "Builds on: Starter and fermentation",
  );
  await expect(
    m02Item
      .locator(".academy-builds-on")
      .getByRole("link", { name: "Starter and fermentation" }),
  ).toHaveAttribute("href", "#/module/hearth-m01");
  await expect(m02Item).toContainText("2 teaching beats · 0 marked complete");
  const essential = page.locator(".academy-route--essential");
  await expect(
    essential.getByRole("heading", {
      level: 2,
      name: "Your first reliable loaf",
    }),
  ).toBeVisible();
  expect(
    await essential.locator(".academy-route-steps a").allTextContents(),
  ).toEqual([
    "Starter and fermentation",
    "Hydration and dough strength",
    "Oven spring and crust",
  ]);
  await expect(
    essential.getByRole("link", { name: "Start this route →" }),
  ).toHaveAttribute("href", "#/module/hearth-m01");
  const deeper = page.locator(".academy-other-routes");
  await expect(deeper.locator("summary")).toHaveText("Deeper routes (1)");
  await deeper.locator("summary").click();
  expect(
    await deeper.locator(".academy-route-steps a").allTextContents(),
  ).toEqual(["Oven spring and crust", "Hydration and dough strength"]);
  const also = page.getByRole("navigation", { name: "Also in this course" });
  for (const [name, href] of [
    ["2 labs", "#/course/hearth/labs"],
    ["2 field guides", "#/course/hearth/guides"],
    ["1 case analysis", "#/course/hearth/cases"],
    ["2 capstones", "#/practice"],
    ["Learning crosswalk", "#/course/hearth/crosswalk"],
    ["Course handbook", "#/handbook/hearth"],
  ])
    await expect(also.getByRole("link", { name, exact: true })).toHaveAttribute(
      "href",
      href,
    );
  await page.waitForTimeout(300);
  expect(moduleRequests()).toEqual([]);
  await shot("course-map");
  pass(
    "Course map groups modules under track headings with global numbering, prerequisite suggestions, the essential route, deeper routes and the collections strip; it loads no module file",
  );

  // Lab shelf.
  await also.getByRole("link", { name: "2 labs", exact: true }).click();
  await expect(page.locator("main h1")).toHaveText("Labs");
  await expect(page.locator("main h1")).toBeFocused();
  await expect(page).toHaveTitle("Labs · SpicyBrain");
  const legend = page.locator(".academy-legend");
  await expect(legend.locator("dt")).toHaveText([
    "Locally executed",
    "Tabletop",
  ]);
  await expect(page.locator("main")).not.toContainText(/verified/i);
  await expect(
    page.getByRole("heading", { level: 2, name: "Locally executed · 1 lab" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { level: 2, name: "Tabletop · 1 lab" }),
  ).toBeVisible();
  const hydrationLab = hearth.labs!.find((l) => l.downloadId)!;
  const hydrationCard = page
    .locator(".academy-card")
    .filter({ hasText: hydrationLab.title });
  for (const text of [
    hydrationLab.summary,
    hydrationLab.outcome,
    hydrationLab.environment,
    hydrationLab.evidence,
  ])
    await expect(hydrationCard).toContainText(text);
  await expect(
    hydrationCard.getByRole("link", { name: "Hydration and dough strength" }),
  ).toHaveAttribute("href", "#/module/hearth-m02");
  const download = hearth.downloads!.find(
    (d) => d.id === hydrationLab.downloadId,
  )!;
  const downloadLink = hydrationCard.getByRole("link", {
    name: download.title,
  });
  await expect(downloadLink).toHaveAttribute(
    "href",
    `./content-downloads/${download.path}`,
  );
  const downloadEvent = page.waitForEvent("download");
  await downloadLink.click();
  const saved = await (await downloadEvent).path();
  expect(
    createHash("sha256")
      .update(await readFile(saved!))
      .digest("hex"),
  ).toBe(download.sha256);
  await expect(
    page
      .locator(".academy-card")
      .filter({ hasText: "Plan a bake schedule on paper" })
      .locator("a[download]"),
  ).toHaveCount(0);
  await shot("lab-shelf");
  pass(
    "Lab shelf groups labs by execution class with a plain-language legend (no 'verified' wording), per-lab metadata, module links and a hash-matching download",
  );

  // Lab page, lazy body, then a failed body load with Retry.
  await hydrationCard.getByRole("link", { name: hydrationLab.title }).click();
  await expect(page.locator("main h1")).toHaveText(hydrationLab.title);
  await expect(page.locator("main h1")).toBeFocused();
  await expect(
    page.getByRole("heading", { level: 3, name: "What you will do" }),
  ).toBeVisible();
  await expect(
    page
      .locator("section")
      .filter({
        has: page.getByRole("heading", { level: 2, name: "Related modules" }),
      })
      .getByRole("link", { name: "Hydration and dough strength" }),
  ).toBeVisible();
  await page.route("**/teaching/bodies/hearth-lab-schedule.json", (r) =>
    r.abort(),
  );
  await nav("#/course/hearth/labs/hearth-lab-schedule");
  await expect(page.getByRole("alert")).toContainText(
    "This lab could not load",
  );
  await expect(page.getByText("Pen and paper or a text editor.")).toBeVisible();
  await page.unroute("**/teaching/bodies/hearth-lab-schedule.json");
  await page.getByRole("button", { name: "Retry lab", exact: true }).click();
  await expect(
    page.getByRole("heading", { level: 3, name: "Worked schedule" }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  pass(
    "Lab page renders metadata from the catalog, its lazy body, related modules, and recovers from a failed body load through Retry",
  );

  // Explained fallbacks.
  for (const [hash, title, link] of [
    [
      "#/course/hearth/labs/missing-lab",
      "This lab is not in the current course.",
      "Browse the lab shelf",
    ],
    [
      "#/course/hearth/guides/missing-guide",
      "This field guide is not in the current course.",
      "Browse the field guides",
    ],
    [
      "#/course/hearth/cases/missing-case",
      "This case analysis is not in the current course.",
      "Browse the case analyses",
    ],
    [
      "#/course/hearth/unknown-section",
      "That part of the course is not available.",
      "Open the course map",
    ],
    ...catalog
      .filter((c) => c.id !== "hearth" && !c.labs?.length)
      .slice(0, 1)
      .map((c) => [
        `#/course/${c.id}/labs`,
        "This course has no lab shelf.",
        "Open the course map",
      ]),
  ]) {
    await nav(hash);
    await expect(page.locator("main h1")).toHaveText(title);
    await expect(
      page.getByRole("link", { name: link, exact: true }),
    ).toBeVisible();
  }
  // A section named like an inherited object key is unknown, in the page
  // and in the tab title alike.
  for (const key of ["constructor", "toString", "__proto__"]) {
    await nav(`#/course/hearth/${key}`);
    await expect(page.locator("main h1")).toHaveText(
      "That part of the course is not available.",
    );
    await expect(page).toHaveTitle("Course · SpicyBrain");
  }
  pass(
    "Unknown items, sections and absent collections show an explained fallback with a link back; an inherited object key is an unknown section in the page and the tab title",
  );

  // Field guides and the Notebook draft.
  await nav("#/course/hearth/guides");
  await expect(page.locator(".academy-card")).toHaveCount(2);
  const denseGuide = hearth.guides![0];
  await expect(
    page.locator(".academy-card").first().locator(".academy-question"),
  ).toHaveText(denseGuide.question);
  await page.getByRole("link", { name: denseGuide.title }).click();
  await expect(page.locator("main h1")).toHaveText(denseGuide.title);
  await expect(
    page.getByRole("heading", { level: 2, name: "Action" }),
  ).toBeVisible();
  // Each part is a section with its own h2 over a disclosure.
  const part = (name: string) =>
    page.locator("section.academy-guide-part").filter({
      has: page.getByRole("heading", { level: 2, name, exact: true }),
    });
  const toggle = (name: string) => part(name).locator("details");
  await expect(toggle("Worked example")).toHaveAttribute("open", "");
  await expect(toggle("Template")).not.toHaveAttribute("open", "");
  await expect(toggle("Limits")).not.toHaveAttribute("open", "");
  await expect(toggle("Limits").locator("summary")).toHaveText(
    "Show the limits",
  );
  await toggle("Limits").locator("summary").click();
  await expect(part("Limits")).toContainText("single bake is weak evidence");
  await toggle("Template").locator("summary").click();
  await part("Template")
    .getByRole("button", { name: "Draft in Notebook", exact: true })
    .click();
  const draft = part("Template").getByLabel("Your draft from this template");
  await expect(draft).toBeFocused();
  await expect(draft).toHaveValue(/The one change I will test:/);
  await draft.press("ControlOrMeta+End");
  await draft.pressSequentially("\nSynthetic guide draft line");
  const noteId = `note-${denseGuide.id}`;
  await expect
    .poll(async () => (await stored(page)).notes[noteId]?.text ?? "")
    .toContain("Synthetic guide draft line");
  const note = (await stored(page)).notes[noteId];
  expect([note.courseId, note.lessonId, note.sectionId]).toEqual([
    "hearth",
    denseGuide.lessonIds[0],
    denseGuide.id,
  ]);
  await shot("guide");
  await page.reload();
  await expect(page.locator("main h1")).toHaveText(denseGuide.title);
  expect((await stored(page)).notes[noteId].text).toContain(
    "Synthetic guide draft line",
  );
  await toggle("Template").locator("summary").click();
  await expect(part("Template")).toContainText(
    "You already have a draft from this template.",
  );
  await part("Template")
    .getByRole("button", { name: "Draft in Notebook", exact: true })
    .click();
  await expect(
    part("Template").getByLabel("Your draft from this template"),
  ).toHaveValue(/Synthetic guide draft line/);
  const planGuide = hearth.guides![1];
  expect(planGuide.lessonIds).toEqual([]);
  await nav(`#/course/hearth/guides/${planGuide.id}`);
  await toggle("Template").locator("summary").click();
  await part("Template")
    .getByRole("button", { name: "Draft in Notebook", exact: true })
    .click();
  await expect
    .poll(
      async () => (await stored(page)).notes[`note-${planGuide.id}`]?.lessonId,
    )
    .toBe(hearth.modules[0].lessons[0].id);
  await nav("#/notebook");
  const guideNote = page.locator(".notes-list > section").filter({
    hasText: `Field guide · ${denseGuide.title}`,
  });
  await expect(
    guideNote.getByRole("heading", {
      name: `Field guide · ${denseGuide.title}`,
    }),
  ).toBeVisible();
  await expect(
    guideNote.getByLabel("Your draft from this template"),
  ).toHaveValue(/Synthetic guide draft line/);
  await expect(
    guideNote.getByRole("link", { name: "Return to source →" }),
  ).toHaveAttribute("href", `#/course/hearth/guides/${denseGuide.id}`);
  await expect(page.getByText("Removed lesson · note preserved")).toHaveCount(
    0,
  );
  await nav("#/settings");
  const exportEvent = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export all study data" }).click();
  const exported = await readFile((await (await exportEvent).path())!, "utf8");
  expect(exported).toContain(noteId);
  expect(exported).toContain("Synthetic guide draft line");
  await nav("#/notebook");
  await guideNote.getByRole("link", { name: "Return to source →" }).click();
  await expect(page.locator("main h1")).toHaveText(denseGuide.title);
  pass(
    "Field guide renders Action, Worked example (open on desktop), Template and Limits; Draft in Notebook creates an ordinary note that survives reload, is exported and appears in Notebook with a return link",
  );
  // The outline, every part open: each part is an h2 and the headings in its
  // body nest under it, so a worked example's h3 and a template's h3 never
  // run together under Action.
  const outline = () =>
    page.evaluate(() => {
      for (const d of document.querySelectorAll<HTMLDetailsElement>(
        ".academy-guide details",
      ))
        d.open = true;
      return [
        ...document.querySelectorAll(".academy-guide :is(h1, h2, h3, h4)"),
      ].map((h) => `${h.tagName} ${h.textContent!.trim()}`);
    });
  for (const [guide, example, template] of [
    [denseGuide, ["H3 Worked example: a fictional Tuesday loaf"], []],
    [
      planGuide,
      ["H3 Worked example: a fictional Sunday bake"],
      ["H3 Your bake plan"],
    ],
  ] as const) {
    await nav(`#/course/hearth/guides/${guide.id}`);
    await expect(part("Limits")).toBeVisible();
    expect(await outline()).toEqual([
      `H1 ${guide.title}`,
      "H2 Action",
      "H2 Worked example",
      ...example,
      "H2 Template",
      ...template,
      "H2 Limits",
      "H2 Related modules",
    ]);
  }
  pass(
    "A guide's worked example, template and limits are each an h2 part; the headings in each body nest under their own part",
  );

  // Case analysis.
  const caseItem = hearth.cases![0];
  const source = hearth.sources.find((s) => s.id === caseItem.sourceIds[0])!;
  await nav("#/course/hearth/cases");
  await expect(page.locator(".academy-card")).toHaveCount(1);
  await page.getByRole("link", { name: caseItem.title }).click();
  await expect(page.locator("main h1")).toHaveText(caseItem.title);
  await expect(page.locator(".academy-facts").first()).toContainText(
    "The customer (customer-authored)",
  );
  const sourceLink = page.locator(".academy-sources a").first();
  await expect(sourceLink).toHaveAttribute("href", source.url);
  await expect(sourceLink).toHaveAttribute("target", "_blank");
  await expect(sourceLink).toHaveAttribute("rel", /noopener/);
  await expect(page.locator(".academy-sources")).toContainText(
    `reviewed ${source.reviewDate}`,
  );
  await expect(page.locator(".academy-sources")).toContainText(source.caveat);
  await expect(
    page.getByRole("heading", { level: 3, name: "Reading it critically" }),
  ).toBeVisible();
  await shot("case");
  pass(
    "Case analysis shows the reporter, the source with review date and caveat, its lazy body and related modules",
  );

  // Crosswalk.
  await nav("#/course/hearth/crosswalk");
  await expect(page.locator(".academy-crosswalk th[scope=col]")).toHaveText([
    "Resource",
    "Publisher",
    "Access",
    "Prerequisites",
    "Related modules",
    "Note",
  ]);
  const row = hearth.crosswalk![0];
  const external = page.locator(".academy-crosswalk tbody a").first();
  await expect(external).toHaveAttribute("href", row.url);
  await expect(external).toHaveAttribute("rel", /noopener/);
  await expect(page.locator(".academy-crosswalk")).toContainText(
    `Reviewed ${row.reviewedAt}`,
  );
  await expect(page.locator(".academy-crosswalk tbody")).toContainText(
    row.note,
  );
  pass(
    "Crosswalk renders a table with external links (rel=noopener) and related modules",
  );

  // Capstones: revision notice and data pack.
  await nav("#/practice");
  await expect(
    page
      .locator("section")
      .filter({ has: page.getByRole("heading", { name: hearth.title }) })
      .locator(".capstone-row"),
  ).toHaveCount(2);
  const revised = hearth.scenarios.find((s) => s.revisionNotice)!;
  await nav(`#/practice/${revised.id}`);
  await expect(page.locator(".academy-revision")).toContainText(
    revised.revisionNotice!,
  );
  const pack = hearth.downloads!.find((d) => d.id === revised.downloadIds![0])!;
  await expect(
    page.locator(".academy-data-pack").getByRole("link", { name: pack.title }),
  ).toHaveAttribute("href", `./content-downloads/${pack.path}`);
  await expect(
    page.getByRole("heading", { name: "The situation", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "hydration lab", exact: true }),
  ).toHaveAttribute("href", "#/course/hearth/labs/hearth-lab-hydration");
  const other = hearth.scenarios.find(
    (s) => s.isCapstone && !s.revisionNotice,
  )!;
  await nav(`#/practice/${other.id}`);
  await expect(page.locator(".academy-revision")).toHaveCount(0);
  await expect(page.locator(".academy-data-pack")).toHaveCount(0);
  pass(
    "A revised capstone shows its revision notice and data pack; an unrevised capstone shows neither",
  );

  // End of a module: next in the track and related collections; a module
  // whose text links to another module loads at runtime.
  await nav("#/module/hearth-m01/hearth-m01-proof");
  const next = page.locator(".academy-next");
  await expect(next).toContainText(
    "Next in this track: Hydration and dough strength",
  );
  await expect(
    next.getByRole("link", { name: "Hydration and dough strength" }),
  ).toHaveAttribute("href", "#/module/hearth-m02");
  await expect(next.locator("details.academy-related")).toHaveAttribute(
    "open",
    "",
  );
  await expect(next.locator("details.academy-related a")).toHaveText([
    "Lab · Plan a bake schedule on paper",
    "Field guide · Diagnose a dense loaf",
  ]);
  await nav("#/module/hearth-m02/hearth-m02-ratio?view=handbook");
  await expect(
    page.locator(
      '.module-handbook a[href="#/module/hearth-m01/hearth-m01-starter"]',
    ),
  ).toBeVisible();
  await expect(page.locator(".module-handbook .academy-next")).toContainText(
    "This is the last module in Dough and fermentation.",
  );
  await nav("#/module/hearth-m01/hearth-m01-starter");
  await expect(page.locator(".academy-next")).toHaveCount(0);
  await nav("#/module/hearth-m02/hearth-m02-strength");
  await expect(page.locator(".teaching-beat > h2")).toHaveText(
    "Match folds to hydration",
  );
  await expect(page.locator(".academy-next")).toContainText(
    "This is the last module in Dough and fermentation.",
  );
  await expect
    .poll(async () => (await stored(page)).beatResume?.beatId)
    .toBe("hearth-m02-strength");
  pass(
    "The last beat and the module handbook show the next module in the track and related labs and guides; a cross-module teaching link loads at runtime",
  );

  // Today re-entry cue, and Resume on the essential route.
  requests.length = 0;
  await nav("#/");
  const cue = page.locator(".academy-reentry");
  await expect(cue).toContainText("Track: Dough and fermentation");
  await expect(cue).toContainText(
    "Beat 2 of 2 in Hydration and dough strength",
  );
  await expect(cue).toContainText(
    "Before this: Count the starter in the ratio",
  );
  await nav("#/course/hearth");
  await expect(
    page.getByRole("link", { name: "Resume this route →" }),
  ).toHaveAttribute("href", "#/module/hearth-m02/hearth-m02-strength");
  await page.waitForTimeout(300);
  expect(moduleRequests()).toEqual([]);
  await shot("today-resumed-map");
  pass(
    "Today shows the saved beat's module, track and previous beat; the route resumes there; neither page loads a module file",
  );

  // Track handbook, from a fresh document so no module is already cached.
  await page.reload();
  await expect(page.locator("main h1")).toBeVisible();
  requests.length = 0;
  await nav("#/handbook/hearth?track=hearth-track-dough");
  await expect(page.locator(".handbook-chapter")).toHaveCount(2);
  await expect(page.locator(".academy-handbook-scope")).toHaveText(
    "Track: Dough and fermentation · 2 modules",
  );
  expect(moduleRequests().sort()).toEqual([
    "/teaching/hearth-hearth-m01.json",
    "/teaching/hearth-hearth-m02.json",
  ]);
  // The scopes are links: moving through them with the keyboard never
  // navigates or loads a module (WCAG 3.2.2); following one is a route
  // change, so focus moves to the heading.
  const scope = page.getByRole("navigation", { name: "Handbook scope" });
  const scopeLink = (name: string) =>
    scope.getByRole("link", { name, exact: true });
  await expect(scopeLink("Track: Dough and fermentation")).toHaveAttribute(
    "aria-current",
    "page",
  );
  await expect(scope.locator("[aria-current]")).toHaveCount(1);
  const historyLength = await page.evaluate(() => history.length);
  requests.length = 0;
  await scopeLink("Track: Dough and fermentation").focus();
  for (const key of ["ArrowDown", "ArrowDown", "ArrowUp", "ArrowRight"])
    await page.keyboard.press(key);
  await page.waitForTimeout(300);
  await expect(page).toHaveURL(
    /#\/handbook\/hearth\?track=hearth-track-dough$/,
  );
  expect(moduleRequests()).toEqual([]);
  expect(await page.evaluate(() => history.length)).toBe(historyLength);
  await scopeLink("Track: Oven and finish").click();
  await expect(page).toHaveURL(/#\/handbook\/hearth\?track=hearth-track-oven$/);
  await expect(page.locator(".handbook-chapter")).toHaveCount(1);
  await expect(page.locator("main h1")).toBeFocused();
  await expect(scopeLink("Track: Oven and finish")).toHaveAttribute(
    "aria-current",
    "page",
  );
  await expect(scope.locator("[aria-current]")).toHaveCount(1);
  await expect(
    page.getByRole("button", { name: "Print track handbook" }),
  ).toBeEnabled();
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));
  await page.emulateMedia({ media: "print" });
  await expect(scope).toBeHidden();
  await expect(page.locator(".handbook-chapter")).toBeVisible();
  await page.emulateMedia({ media: "screen" });
  await page.evaluate(() => window.dispatchEvent(new Event("afterprint")));
  await scopeLink("Whole course · every module").click();
  await expect(page).toHaveURL(/#\/handbook\/hearth$/);
  await expect(page.locator(".handbook-chapter")).toHaveCount(3);
  await expect(scopeLink("Whole course · every module")).toHaveAttribute(
    "aria-current",
    "page",
  );
  requests.length = 0;
  await nav("#/handbook/hearth?track=missing-track");
  await expect(page.getByRole("alert")).toContainText(
    "That track is not part of this course",
  );
  await expect(page.locator(".handbook-chapter")).toHaveCount(0);
  await page.waitForTimeout(300);
  expect(moduleRequests()).toEqual([]);
  await expect(scope.locator("[aria-current]")).toHaveCount(0);
  pass(
    "A track handbook loads only that track's modules; its scope links mark the current scope, never navigate on arrow keys and move focus when followed; print hides them; an unknown track loads nothing",
  );

  // Search entries.
  await nav("#/search");
  for (const [query, type, href] of [
    [
      "script that converts",
      "Lab",
      "#/course/hearth/labs/hearth-lab-hydration",
    ],
    [
      "single change should I test",
      "Field guide",
      "#/course/hearth/guides/hearth-guide-dense-loaf",
    ],
    [
      "calmer morning",
      "Case analysis",
      "#/course/hearth/cases/hearth-case-village-bakery",
    ],
  ]) {
    await page.getByLabel("Search courses, concepts, or notes").fill(query);
    const result = page
      .locator(".search-result")
      .filter({ hasText: `${type} · ${hearth.title}` })
      .first();
    await expect(result).toHaveAttribute("href", href);
  }
  pass(
    "Search finds labs, field guides and case analyses with links to their routes",
  );

  // Accessibility: axe in both themes, then no horizontal scroll at 390 and 320 px.
  const pages = [
    "#/courses",
    "#/course/hearth",
    "#/course/hearth/labs",
    "#/course/hearth/labs/hearth-lab-hydration",
    "#/course/hearth/guides",
    `#/course/hearth/guides/${denseGuide.id}`,
    "#/course/hearth/cases",
    `#/course/hearth/cases/${caseItem.id}`,
    "#/course/hearth/crosswalk",
    "#/course/hearth/labs/missing-lab",
    `#/practice/${revised.id}`,
    "#/module/hearth-m01/hearth-m01-proof",
    "#/handbook/hearth?track=hearth-track-dough",
    "#/",
    "#/notebook",
  ];
  const settle = async () => {
    await expect(
      page.locator("[role=status]").filter({ hasText: /Opening|Assembling/ }),
    ).toHaveCount(0);
    // A theme switch fades the page's colours for a moment (the body's
    // transition); contrast is judged once nothing is still running. A
    // finished animation that fills forwards stays listed, so ask its state.
    await page.waitForFunction(() =>
      document.getAnimations().every((a) => a.playState !== "running"),
    );
  };
  const violations: unknown[] = [];
  for (const theme of ["dark", "light"] as const) {
    await nav("#/settings");
    await page.getByLabel("Theme").selectOption(theme);
    await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
    for (const hash of pages) {
      await nav(hash);
      await settle();
      await page
        .locator("details.academy-other-routes, .academy-guide-part details")
        .evaluateAll((nodes) =>
          nodes.forEach((n) => ((n as HTMLDetailsElement).open = true)),
        );
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze();
      for (const v of results.violations)
        violations.push({
          theme,
          hash,
          id: v.id,
          nodes: v.nodes.map((n) => n.target),
        });
    }
    await nav("#/course/hearth/labs");
    await shot(`labs-${theme}`);
  }
  expect(violations).toEqual([]);
  pass(
    `axe (WCAG 2.1 A/AA) reports no violations on ${pages.length} pages in dark and light themes`,
  );
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    for (const hash of pages) {
      await nav(hash);
      await settle();
      await noOverflow(page);
    }
    await nav("#/course/hearth");
    await shot(`course-map-${width}`);
  }
  pass(`No horizontal page scroll at 390 and 320 px on ${pages.length} pages`);
  // The crosswalk on a phone: a written hint says the table scrolls, and
  // every link in it is visible while it has keyboard focus (WCAG 2.4.11):
  // nothing pinned covers it.
  for (const width of [320, 390]) {
    await page.setViewportSize({ width, height: 844 });
    await nav("#/course/hearth/crosswalk");
    await expect(
      page.getByText(
        "More columns → Scroll sideways, or focus the table and use arrow keys.",
      ),
    ).toBeVisible();
    const region = page.getByRole("region", { name: /Learning crosswalk/ });
    const links = await region.locator("a").count();
    expect(links).toBeGreaterThan(1);
    await region.focus();
    for (let i = 0; i < links; i++) {
      await page.keyboard.press("Tab");
      const focused = await page.evaluate(() => {
        const a = document.activeElement as HTMLElement;
        return {
          text: a.textContent?.trim(),
          inTable: !!a.closest(".academy-crosswalk"),
          // The top element at the centre of one of the link's boxes is the
          // link itself (or its text), not a cell drawn over it.
          visible: [...a.getClientRects()].some((r) => {
            const hit = document.elementFromPoint(
              r.left + r.width / 2,
              r.top + r.height / 2,
            );
            return !!hit && (hit === a || a.contains(hit));
          }),
        };
      });
      expect(focused, JSON.stringify(focused)).toMatchObject({
        inTable: true,
        visible: true,
      });
    }
    await shot(`crosswalk-${width}`);
  }
  pass(
    "On a phone the crosswalk says it scrolls sideways, and every link in it stays visible with keyboard focus at 320 and 390 px",
  );
  const phone = await browser.newPage({
    viewport: { width: 390, height: 844 },
  });
  await phone.goto(`${url}/#/course/hearth/guides/${denseGuide.id}`);
  await expect(
    phone.locator(".academy-guide-part details").first(),
  ).toBeVisible();
  await expect(
    phone
      .locator("section.academy-guide-part")
      .filter({
        has: phone.getByRole("heading", {
          level: 2,
          name: "Worked example",
          exact: true,
        }),
      })
      .locator("details"),
  ).not.toHaveAttribute("open", "");
  await phone.goto(`${url}/#/module/hearth-m01/hearth-m01-proof`);
  await expect(phone.locator("details.academy-related")).toBeVisible();
  await expect(phone.locator("details.academy-related")).not.toHaveAttribute(
    "open",
    "",
  );
  await phone.close();
  pass("On a phone the worked example and the related list start collapsed");
  expect(errors).toEqual([]);

  // A track whose only module has no teaching module yet: the map offers no
  // handbook for it, the module opens its lesson, and the track handbook says
  // why there is nothing to assemble instead of waiting forever.
  await removeTemporaryTree(
    join(temp, "content/teaching/hearth/hearth-m03.json"),
  );
  await build();
  await page.setViewportSize({ width: 1440, height: 1000 });
  // A new document, so the rebuilt bundle and teaching index are the ones read.
  await page.reload();
  await go("#/course/hearth");
  const trackSection = (title: string) =>
    page.locator(".academy-track").filter({
      has: page.getByRole("heading", { level: 2, name: title, exact: true }),
    });
  const ovenTrack = trackSection("Oven and finish");
  await expect(ovenTrack.locator(".academy-track-meta")).toHaveText("1 module");
  await expect(
    ovenTrack.getByRole("link", { name: "Handbook for this track" }),
  ).toHaveCount(0);
  await expect(
    trackSection("Dough and fermentation").getByRole("link", {
      name: "Handbook for this track",
    }),
  ).toBeVisible();
  await expect(
    ovenTrack.getByRole("link", { name: "Oven spring and crust", exact: true }),
  ).toHaveAttribute("href", "#/lesson/hearth-m03-l01");
  await expect(ovenTrack.locator(".module-map-meta")).toHaveText("1 lesson");
  requests.length = 0;
  await nav("#/handbook/hearth?track=hearth-track-oven");
  await expect(page.locator(".course-handbook .sc-notice")).toContainText(
    "No module in this track has a handbook chapter yet",
  );
  await expect(
    page.locator("[role=status]").filter({ hasText: /Assembling/ }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Print track handbook" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("navigation", { name: "Track handbook contents" }),
  ).toHaveCount(0);
  await expect(
    page
      .locator(".academy-handbook-lessons")
      .getByRole("link", { name: "Oven spring and crust", exact: true }),
  ).toHaveAttribute("href", "#/lesson/hearth-m03-l01");
  await settle();
  const emptyViolations = (
    await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze()
  ).violations.map((v) => v.id);
  expect(emptyViolations).toEqual([]);
  await nav("#/handbook/hearth");
  await expect(page.locator(".handbook-chapter")).toHaveCount(2);
  const contents = await page
    .getByRole("navigation", { name: "Course handbook contents" })
    .locator("a")
    .evaluateAll((links) =>
      links.map((a) => {
        const href = a.getAttribute("href")!;
        return [href, !!document.getElementById(href.slice(1))];
      }),
    );
  expect(contents).toEqual([
    ["#chapter-hearth-m01", true],
    ["#chapter-hearth-m02", true],
  ]);
  await expect(page.locator(".academy-handbook-lessons")).toContainText(
    "Oven spring and crust",
  );
  await page.waitForTimeout(300);
  expect(moduleRequests().sort()).toEqual([
    "/teaching/hearth-hearth-m01.json",
    "/teaching/hearth-hearth-m02.json",
  ]);
  expect(errors).toEqual([]);
  pass(
    "A track without a teaching module offers no track handbook; its handbook explains why nothing is assembled, and every contents link names a chapter that exists",
  );

  // Remove the fixture: the release catalog returns and no engine file changed.
  await removeTemporaryTree(join(temp, "content/courses/hearth"));
  await removeTemporaryTree(join(temp, "content/teaching/hearth"));
  await removeTemporaryTree(join(temp, "content/downloads/hearth"));
  const release = await build();
  expect(release.map((c) => c.id)).toEqual(baselineCourseIds);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.reload();
  await go("#/notebook");
  await expect(
    page.getByText("Removed lesson · note preserved", { exact: true }),
  ).toHaveCount(2);
  const runtimeChanges = diff(before, await manifest(temp)).filter(
    (f) =>
      !f.path.startsWith("src/generated/") &&
      !f.path.startsWith("public/content-assets/") &&
      !f.path.startsWith("public/content-downloads/") &&
      !f.path.startsWith("public/teaching/") &&
      !f.path.startsWith("docs/evidence/"),
  );
  expect(runtimeChanges).toEqual([]);
  pass(
    "Fixture removed: the release catalog is restored, guide drafts stay recoverable in Notebook and runtime source is unchanged",
  );
  await mkdir(evidence, { recursive: true });
  await writeFile(
    join(evidence, "collections-fixture.json"),
    JSON.stringify(
      {
        date: new Date().toISOString(),
        browser: browser.version(),
        fixture: "tests/fixtures/collections/content",
        course: {
          id: "hearth",
          modules: hearth.modules.length,
          tracks: hearth.tracks!.length,
          routes: hearth.routes!.length,
          labs: hearth.labs!.length,
          guides: hearth.guides!.length,
          cases: hearth.cases!.length,
          crosswalk: hearth.crosswalk!.length,
          capstones: hearth.scenarios.filter((s) => s.isCapstone).length,
        },
        additionDiff: addition,
        runtimeSourceChanges: runtimeChanges,
        assertions,
        result: "pass",
      },
      null,
      2,
    ) + "\n",
  );
  console.log(
    `PASS: course collections fixture (${assertions.length} checks). Evidence: test-results/evidence/collections-fixture.json`,
  );
} finally {
  await browser?.close();
  server.close();
  await removeTemporaryTree(temp);
}
