// Same-origin forward, rollback and return check for a release candidate.
//
// Usage:
//   node --import tsx scripts/release-rollback-check.ts \
//     --base-dist <dir> --candidate-dist <dir> [--out docs/academy/evidence/rollback.json]
//     [--new-module dbxfe-azure] [--guide guide-fg01-discovery-brief]
//
// One loopback origin serves the released build (base) and then the candidate
// from the same port, and one persistent browser profile keeps the learner's
// IndexedDB across the switches, exactly as a same-origin publication or a
// rollback of website files would. The steps:
//   1. base: a learner's existing data (lesson note, bookmark, completion,
//      a checked answer);
//   2. candidate: that data is read unchanged; new material adds a beat note
//      on a new module, a beat completion and, when guides are published, a
//      field-guide draft;
//   3. base again (rollback): the old client opens the same records without an
//      error, shows the new-material notes as preserved, and adds its own edit;
//   4. candidate again (return): every record from all three steps is intact
//      and the new-material notes are attached to their material again.
// Synthetic data only; no network beyond loopback.
import { createServer } from "node:http";
import { mkdtemp, readFile, writeFile, rm, mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve, extname, sep, dirname } from "node:path";
import process from "node:process";
import { chromium, expect, type Page } from "@playwright/test";
import { stored } from "../tests/browser/helpers.ts";
import type { StudyState } from "../src/study.ts";

const arg = (name: string, fallback?: string) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : fallback;
};
const baseDist = resolve(arg("--base-dist")!),
  candidateDist = resolve(arg("--candidate-dist")!),
  out = arg("--out", "docs/academy/evidence/rollback.json")!,
  newModule = arg("--new-module", "dbxfe-azure")!,
  guideId = arg("--guide", "guide-fg01-discovery-brief")!;
let root = baseDist;
const mime: Record<string, string> = {
  ".html": "text/html",
  ".js": "application/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".json": "application/json",
};
const server = createServer(async (req, res) => {
  try {
    const path = decodeURIComponent(new URL(req.url!, "http://l").pathname),
      file = resolve(
        root,
        "." + path + (path.endsWith("/") ? "index.html" : ""),
      );
    if (!file.startsWith(root + sep)) throw Error();
    res.setHeader(
      "Content-Type",
      mime[extname(file)] ?? "application/octet-stream",
    );
    res.setHeader("Cache-Control", "no-store");
    res.end(await readFile(file));
  } catch {
    res.statusCode = 404;
    res.end("Not found");
  }
});
await new Promise<void>((r) => server.listen(0, "127.0.0.1", r));
const address = server.address();
if (!address || typeof address === "string") throw Error("No port");
const origin = `http://127.0.0.1:${address.port}`;
const profile = await mkdtemp(join(tmpdir(), "spicybrain-rollback-"));
const context = await chromium.launchPersistentContext(profile, {
  executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
  viewport: { width: 1440, height: 1000 },
});
const steps: { step: string; checks: string[] }[] = [];
const families = [
  "notes",
  "bookmarks",
  "completions",
  "attempts",
  "reviews",
  "schedules",
  "assessments",
] as const;
const contains = (outer: StudyState, inner: StudyState) => {
  for (const f of families)
    for (const [k, v] of Object.entries(inner[f] ?? {}))
      expect((outer[f] as Record<string, unknown>)[k], `${f}.${k}`).toEqual(v);
};
// A hash-only navigation stays in the same document, so every step first
// leaves the origin: the build now being served is the one that loads.
const go = async (page: Page, hash: string) => {
  await page.goto("about:blank");
  await page.goto(`${origin}/${hash}`);
  await expect(page.locator("main h1")).toBeVisible();
};
// Every edit is queued as its own write, so a snapshot or a navigation taken
// while "Saving…" shows can see (or lose) a half-typed draft. Settle waits
// until no save is pending and two reads a moment apart agree.
const settle = async (page: Page) => {
  await expect.poll(async () => (await stored(page))?.schemaVersion).toBe(4);
  for (const text of ["Unsaved · keep this tab open", "Saving…"])
    await expect(page.getByText(text, { exact: true })).toHaveCount(0);
  await expect
    .poll(async () => {
      const first = JSON.stringify(await stored(page));
      await page.waitForTimeout(250);
      return first === JSON.stringify(await stored(page));
    })
    .toBe(true);
};
const noteSaved = (page: Page, ending: string) =>
  expect
    .poll(async () =>
      Object.values((await stored(page)).notes).some((n) =>
        n.text.trimEnd().endsWith(ending),
      ),
    )
    .toBe(true);
try {
  const page = context.pages()[0] ?? (await context.newPage());
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));

  // 1. The released build: a learner's existing data.
  root = baseDist;
  const lid = "dbxfe-m01-l01";
  await go(page, `#/lesson/${lid}`);
  const section = page.locator("section[id]").first();
  const sid = (await section.getAttribute("id"))!;
  await section.getByText("Notes for this section", { exact: true }).click();
  await section
    .getByLabel("Your lesson note")
    .fill("Synthetic note written in the released build");
  await noteSaved(page, "Synthetic note written in the released build");
  await section
    .getByRole("button", { name: "Bookmark section", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Mark lesson complete", exact: true })
    .click();
  const check = page.locator(".knowledge-check").first();
  await check.locator("input[type=radio]").first().check();
  await check
    .getByRole("button", { name: "Check answer", exact: true })
    .click();
  await settle(page);
  const s0 = await stored(page);
  expect(s0.notes[`note-${sid}`] ?? Object.values(s0.notes)[0]).toBeTruthy();
  steps.push({
    step: "base: existing learner data",
    checks: [
      `${Object.keys(s0.notes).length} note(s), ${Object.keys(s0.bookmarks).length} bookmark(s), ${Object.keys(s0.completions).length} completion(s), ${Object.keys(s0.attempts).length} attempt(s)`,
    ],
  });

  // 2. The candidate on the same origin and profile.
  root = candidateDist;
  await go(page, "#/");
  const s1a = await stored(page);
  contains(s1a, s0);
  const teaching = JSON.parse(
    await readFile(
      join(candidateDist, "teaching", `dbxfe-${newModule}.json`),
      "utf8",
    ),
  ) as { beats: { id: string }[] };
  const firstBeat = teaching.beats[0].id;
  await go(page, `#/module/${newModule}/${firstBeat}`);
  await page.locator(".beat-notes > summary").click();
  await page
    .locator(".beat-notes")
    .getByLabel("Your lesson note")
    .fill("Synthetic beat note on new material");
  await page
    .getByRole("button", { name: "Mark this beat complete", exact: true })
    .click();
  // The guide is required unless `--guide none` says the candidate has no
  // guides: counting its parts before the lazy body renders would silently
  // skip the draft.
  let guideTitle = "";
  const guidePublished = guideId !== "none";
  if (guidePublished) {
    await go(page, `#/course/dbxfe/guides/${guideId}`);
    await expect(
      page.locator("section.academy-guide-part").first(),
    ).toBeVisible();
    guideTitle = (await page.locator("main h1").textContent())!.trim();
    const template = page.locator("section.academy-guide-part").filter({
      has: page.getByRole("heading", {
        level: 2,
        name: "Template",
        exact: true,
      }),
    });
    await template.locator("summary").click();
    await template
      .getByRole("button", { name: "Draft in Notebook", exact: true })
      .click();
    const draft = template.getByLabel("Your draft from this template");
    await draft.press("ControlOrMeta+End");
    await draft.pressSequentially("\nSynthetic guide draft");
    await noteSaved(page, "Synthetic guide draft");
  }
  await noteSaved(page, "Synthetic beat note on new material");
  await settle(page);
  const s1 = await stored(page);
  contains(s1, s0);
  const newNotes = Object.keys(s1.notes).filter((k) => !(k in s0.notes));
  expect(newNotes.length).toBe(guidePublished ? 2 : 1);
  steps.push({
    step: "candidate: data read unchanged; new material recorded",
    checks: [
      "every record from step 1 unchanged",
      `${newNotes.length} new note(s): ${newNotes.join(", ")}`,
      "beat completion on new material",
    ],
  });

  // 3. Rollback: the released build opens the same records.
  root = baseDist;
  await go(page, "#/notebook");
  await expect(page.getByRole("alert")).toHaveCount(0);
  const s2a = await stored(page);
  contains(s2a, s1);
  // The released build names a note's lesson when it still has that lesson
  // (its search index lists every lesson it knows) and says "Removed lesson"
  // otherwise; either way the section is new to it and marked unavailable.
  const baseLessons = new Set(
    (
      JSON.parse(
        await readFile(join(baseDist, "teaching", "search.json"), "utf8"),
      ) as { href: string }[]
    ).flatMap((e) => /^#\/lesson\/([^/?]+)/.exec(e.href)?.slice(1) ?? []),
  );
  const removedLesson = newNotes.filter(
    (k) => !baseLessons.has(s1.notes[k].lessonId),
  ).length;
  await expect(
    page.getByText("Removed lesson · note preserved", { exact: true }),
  ).toHaveCount(removedLesson);
  await expect(
    page.getByText("The original section is unavailable.", { exact: true }),
  ).toHaveCount(newNotes.length);
  // Each note is shown in full in the released build's note editor.
  const shown = await page
    .locator("main textarea")
    .evaluateAll((els) => els.map((e) => (e as HTMLTextAreaElement).value));
  for (const k of newNotes) expect(shown).toContain(s1.notes[k].text);
  await go(page, "#/lesson/dbxfe-m02-l01");
  const s2section = page.locator("section[id]").first();
  await s2section.getByText("Notes for this section", { exact: true }).click();
  await s2section
    .getByLabel("Your lesson note")
    .fill("Synthetic note written after the rollback");
  await noteSaved(page, "Synthetic note written after the rollback");
  await settle(page);
  const s2 = await stored(page);
  contains(s2, s1);
  steps.push({
    step: "rollback: released build reads the candidate's records",
    checks: [
      "no alert and no page error",
      "every record from step 2 unchanged",
      `${newNotes.length} new-material note(s) listed with their section marked unavailable (${removedLesson} under "Removed lesson", ${newNotes.length - removedLesson} under their retained lesson)`,
      "an edit made in the released build",
    ],
  });

  // 4. Return: the candidate again.
  root = candidateDist;
  await go(page, "#/notebook");
  const s3 = await stored(page);
  contains(s3, s2);
  if (guidePublished)
    await expect(
      page.getByRole("heading", { name: `Field guide · ${guideTitle}` }),
    ).toBeVisible();
  await go(page, `#/module/${newModule}/${firstBeat}`);
  await page.locator(".beat-notes > summary").click();
  await expect(
    page.locator(".beat-notes").getByLabel("Your lesson note"),
  ).toHaveValue("Synthetic beat note on new material");
  steps.push({
    step: "return: candidate again",
    checks: [
      "every record from all steps intact",
      guidePublished
        ? "guide draft attached to its guide again"
        : "no guides published in this candidate",
      "beat note shown on its beat again",
    ],
  });
  expect(errors).toEqual([]);
  await mkdir(dirname(out), { recursive: true });
  await writeFile(
    out,
    JSON.stringify(
      {
        date: new Date().toISOString(),
        browser:
          context.browser()?.version() ?? "chromium (persistent context)",
        procedure:
          "One loopback origin, one persistent profile: released build, candidate, released build, candidate.",
        baseDist: arg("--base-label", baseDist),
        candidateDist: arg("--candidate-label", candidateDist),
        schemaVersion: s3.schemaVersion,
        steps,
        result: "pass",
      },
      null,
      2,
    ) + "\n",
  );
  console.log(
    `PASS: same-origin forward, rollback and return. Evidence: ${out}`,
  );
} finally {
  await context.close();
  server.close();
  await rm(profile, { recursive: true, force: true });
}
