import { test, expect } from "@playwright/test";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { migrateState, parseImport, type StudyState } from "../../src/study";
import { ready, nav, stored } from "./helpers";

// Preserved predecessor shape: no beat fields or showSamajh, and pathId is
// the actual schema-3 addition. All values are synthetic, never user data.
const old = JSON.parse(await readFile("tests/fixtures/study-v3.json", "utf8"));
const families = [
  "notes",
  "drafts",
  "bookmarks",
  "completions",
  "attempts",
  "reviews",
  "schedules",
  "extraPractice",
  "assessments",
  "positions",
] as const;
const digest = (value: unknown) =>
  createHash("sha256").update(JSON.stringify(value)).digest("hex");

test("Native IndexedDB2 schema3 migrates every original family, then teaching edits export and import intact", async ({
  page,
  browser,
}) => {
  expect(old.schemaVersion).toBe(3);
  for (const key of ["beatPositions", "beatResume", "beatChecks"])
    expect(old).not.toHaveProperty(key);
  expect(old.settings).not.toHaveProperty("showSamajh");
  for (const key of families)
    expect(Object.keys(old[key]).length).toBeGreaterThan(0);

  // A blank same-origin response prevents the application from opening storage
  // before the genuinely old root is installed in native IndexedDB version 2.
  await page.route("**/__native-v3-seed", (route) =>
    route.fulfill({
      contentType: "text/html",
      body: "<title>Synthetic migration seed</title>",
    }),
  );
  await page.goto("/__native-v3-seed");
  await page.evaluate(
    (root) =>
      new Promise<void>((resolve, reject) => {
        const request = indexedDB.open("spicybrain-study-v2", 2);
        request.onupgradeneeded = () =>
          request.result.createObjectStore("study");
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const db = request.result,
            tx = db.transaction("study", "readwrite");
          tx.objectStore("study").put(root, "root");
          tx.onerror = () => reject(tx.error);
          tx.oncomplete = () => {
            db.close();
            resolve();
          };
        };
      }),
    old,
  );
  expect(await stored(page)).toEqual(old);
  await ready(page, "/#/settings");
  const expected = migrateState(old);
  expect(expected).toEqual({
    ...old,
    schemaVersion: 4,
    beatPositions: {},
    beatResume: null,
    beatChecks: {},
    settings: { ...old.settings, showSamajh: true },
  });
  await expect.poll(() => stored(page)).toEqual(expected);
  const nativeVersion = await page.evaluate(
    () =>
      new Promise<number>((resolve, reject) => {
        const request = indexedDB.open("spicybrain-study-v2");
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          resolve(request.result.version);
          request.result.close();
        };
      }),
  );
  expect(nativeVersion).toBe(2);

  const beat = "dbxfe-genai-beat-context",
    question = "dbxfe-genai-check-context";
  await nav(page, `#/module/dbxfe-genai/${beat}`);
  const article = page.locator(".teaching-beat");
  await article
    .getByRole("button", { name: "2 Correct the selection", exact: true })
    .click();
  await article.getByText("Check yourself", { exact: true }).click();
  const newDraft =
    "SYNTHETIC migration check: inspect the selected manual revision.";
  await article.getByLabel("Your reasoning (saved locally)").fill(newDraft);
  await article
    .getByRole("button", { name: "Reveal model reasoning", exact: true })
    .click();
  await page.getByText("Reading options", { exact: true }).click();
  await page.getByLabel("Show Samajh analogies").uncheck();
  await expect
    .poll(async () => {
      const state = await stored(page);
      return [
        state.beatResume?.visualStateId,
        state.drafts[`draft-${question}`]?.text,
        state.beatChecks[`check-${question}`]?.revealed,
        state.settings.showSamajh,
      ];
    })
    .toEqual(["change", newDraft, true, false]);
  await nav(page, "#/settings");
  const event = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export all study data", exact: true })
    .click();
  const file = await (await event).path();
  const backup = await readFile(file!, "utf8"),
    exported = parseImport(backup);
  expect(exported).toEqual(await stored(page));
  for (const key of families) {
    if (key === "drafts")
      for (const [id, item] of Object.entries(old.drafts))
        expect(exported.drafts[id]).toEqual(item);
    else expect(exported[key]).toEqual(old[key]);
  }
  expect(exported.resume).toEqual(old.resume);
  expect(exported.beatResume?.beatId).toBe(beat);
  expect(exported.beatResume?.visualStateId).toBe("change");
  expect(exported.settings.showSamajh).toBe(false);

  const freshContext = await browser.newContext(),
    fresh = await freshContext.newPage();
  try {
    await ready(fresh, new URL("/#/settings", page.url()).href);
    const blank = await stored(fresh);
    expect(Object.keys(blank?.notes ?? {})).toHaveLength(0);
    await fresh
      .getByLabel("Study data file")
      .setInputFiles({
        name: "synthetic-schema4-after-migration.json",
        mimeType: "application/json",
        buffer: Buffer.from(backup),
      });
    await expect(
      fresh.getByRole("heading", { name: "Import preview", exact: true }),
    ).toBeVisible();
    await fresh
      .getByRole("button", { name: "Merge import", exact: true })
      .click();
    await expect(
      fresh.getByText("Import committed.", { exact: false }),
    ).toBeVisible();
    await expect.poll(() => stored(fresh)).toEqual(exported);
    const restored: StudyState = await stored(fresh);
    await mkdir("test-results/evidence", { recursive: true });
    await writeFile(
      "test-results/evidence/native-v3-teaching-migration.json",
      JSON.stringify(
        {
          browser: "Chromium",
          predecessorSchema: 3,
          nativeDatabaseVersion: nativeVersion,
          migratedSchema: 4,
          predecessorFixtureSha256: digest(old),
          migratedStateSha256: digest(expected),
          exportedStateSha256: digest(exported),
          importedStateSha256: digest(restored),
          preservedFamilies: families,
          originalResumeAndPath: old.resume,
          newBeatId: beat,
          newStage: exported.beatResume?.visualStateId,
          newCheckReveal: true,
          showSamajh: false,
          originalTimestampsPreserved: true,
          immutableAttemptAndReviewCountsUnchanged: true,
          exactImportedRootMatchesExport: true,
        },
        null,
        2,
      ) + "\n",
    );
  } finally {
    await freshContext.close();
  }
});
