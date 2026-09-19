import { test, expect, type Page, type TestInfo } from "@playwright/test";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname } from "node:path";
import { createHash } from "node:crypto";
import {
  emptyState,
  exportText,
  parseImport,
  applyReview,
  JSON_FILE_BYTES,
  type StudyState,
} from "../../src/study";
import {
  fixtureNote,
  fixtureLessons,
  fixtureAt,
  noteState,
} from "../study-fixtures";
import { ready, nav, stored, shot } from "./helpers";
const lesson = "dbxfe-m01-l01",
  why = `${lesson}-why`,
  understand = `${lesson}-understand`;
async function saveEvidence(
  info: TestInfo,
  name: string,
  options: { body: string; contentType: string },
) {
  const path = info.outputPath(name);
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, options.body);
  await info.attach(name, { path, contentType: options.contentType });
}
async function upload(page: Page, raw: string, name = "synthetic.json") {
  await page.getByLabel("Study data file").setInputFiles({
    name,
    mimeType: "application/json",
    buffer: Buffer.from(raw),
  });
}
async function merge(page: Page) {
  await page.getByRole("button", { name: "Merge import", exact: true }).click();
  await expect(
    page.getByText("Import committed.", { exact: false }),
  ).toBeVisible();
}
async function enterNote(page: Page, section: string, text: string) {
  await nav(page, `#/lesson/${lesson}/${section}`);
  await page
    .locator(`#${section}`)
    .getByText("Notes for this section", { exact: true })
    .click();
  await page.locator(`#${section}`).getByLabel("Your lesson note").fill(text);
  await expect
    .poll(async () => (await stored(page)).notes[`note-${section}`]?.text)
    .toBe(text);
  await expect
    .poll(async () => (await stored(page)).resume?.sectionId)
    .toBe(section);
}
async function downloaded(page: Page, button: string) {
  const promise = page.waitForEvent("download");
  await page.getByRole("button", { name: button, exact: true }).click();
  const download = await promise;
  return {
    raw: await readFile((await download.path())!, "utf8"),
    name: download.suggestedFilename(),
  };
}
async function seed(page: Page, state: StudyState) {
  await page.evaluate(
    (s) =>
      new Promise<void>((resolve, reject) => {
        const r = indexedDB.open("spicybrain-study-v2", 2);
        r.onsuccess = () => {
          const db = r.result,
            tx = db.transaction("study", "readwrite");
          tx.objectStore("study").put(s, "root");
          tx.oncomplete = () => {
            db.close();
            resolve();
          };
          tx.onabort = () => reject(tx.error);
        };
      }),
    state,
  );
  await page.reload();
}
const digest = (s: StudyState) =>
  createHash("sha256")
    .update(
      JSON.stringify(s, (_key, value) =>
        value && typeof value === "object" && !Array.isArray(value)
          ? Object.fromEntries(
              Object.entries(value).sort(([a], [b]) => a.localeCompare(b)),
            )
          : value,
      ),
    )
    .digest("hex");

test("P1 native two-tab merge, refreshed preview, conflicts, history, empty backup and rollback", async ({
  page,
  context,
  browserName,
}, info) => {
  await ready(page, "/#/settings");
  const incoming = emptyState();
  const n = fixtureNote(2, "Incoming note from backup");
  incoming.notes[n.id] = n;
  await upload(page, exportText(incoming));
  await expect(
    page.getByRole("heading", { name: "Import preview" }),
  ).toBeVisible();
  const b = await context.newPage();
  await ready(b, "/#/settings");
  await enterNote(b, why, "Saved in native tab B after tab A preview");
  await nav(b, "#/practice/dbxfe-m02-scenario");
  await b
    .getByRole("textbox", { name: "Your response", exact: true })
    .fill("Native tab B saved practice draft");
  await expect
    .poll(async () => Object.values((await stored(b)).drafts)[0]?.text)
    .toBe("Native tab B saved practice draft");
  await nav(b, "#/review");
  await b.getByLabel("Choose lessons").selectOption("all");
  await b.getByRole("button", { name: "Introduce new cards" }).click();
  await b.getByRole("button", { name: "Reveal answer", exact: true }).click();
  await b.getByRole("button", { name: "Good", exact: true }).click();
  await expect
    .poll(async () => Object.keys((await stored(b)).reviews).length)
    .toBe(1);
  const savedB = await stored(b);
  await page.getByRole("button", { name: "Merge import", exact: true }).click();
  await expect(
    page.getByText("Study data changed since this preview.", { exact: false }),
  ).toBeVisible();
  expect(await stored(page)).toEqual(savedB);
  await shot(page, "correction-01-refreshed-preview");
  await merge(page);
  await page.reload();
  const merged = await stored(page);
  expect(merged.notes[`note-${why}`].text).toContain("native tab B");
  expect(merged.notes[n.id]).toEqual(n);
  expect(merged.drafts).toEqual(savedB.drafts);
  expect(merged.reviews).toEqual(savedB.reviews);
  expect(merged.schedules).toEqual(savedB.schedules);
  const conflict = emptyState();
  conflict.notes[`note-${why}`] = {
    ...merged.notes[`note-${why}`],
    text: "Conflicting imported note",
    updatedAt: "2099-01-01T00:00:00.000Z",
  };
  const d = Object.values(merged.drafts)[0];
  conflict.drafts[d.id] = {
    ...d,
    text: "Conflicting imported draft",
    updatedAt: "2099-01-01T00:00:00.000Z",
  };
  await upload(page, exportText(conflict));
  await expect(
    page.getByText("2 conflicting note/draft texts.", { exact: false }),
  ).toBeVisible();
  await merge(page);
  const conflicted = await stored(page);
  expect(Object.values(conflicted.notes).map((n) => n.text)).toEqual(
    expect.arrayContaining([
      "Saved in native tab B after tab A preview",
      "Conflicting imported note",
    ]),
  );
  expect(Object.values(conflicted.drafts).map((n) => n.text)).toEqual(
    expect.arrayContaining([
      "Native tab B saved practice draft",
      "Conflicting imported draft",
    ]),
  );
  await nav(page, "#/notebook");
  await expect(
    page
      .getByLabel("Your lesson note")
      .filter({ hasText: "Conflicting imported note" }),
  ).toHaveCount(1);
  await shot(page, "correction-02-preserved-conflicts");
  await nav(page, "#/settings");
  await upload(page, exportText(emptyState()));
  await merge(page);
  expect(await stored(page)).toEqual(conflicted);
  await upload(page, exportText(incoming));
  await page.evaluate(() => {
    const original = IDBObjectStore.prototype.put;
    IDBObjectStore.prototype.put = function (value, key) {
      const request = original.call(this, value, key);
      this.transaction.abort();
      return request;
    };
  });
  await page.getByRole("button", { name: "Merge import", exact: true }).click();
  await expect(
    page.getByText("Import could not be committed", { exact: false }),
  ).toBeVisible();
  expect(await stored(page)).toEqual(conflicted);
  await page.reload();
  expect(await stored(page)).toEqual(conflicted);
  const afterFailure = await stored(page);
  // Destructive replacement also has to reconfirm after a different tab saves.
  await upload(page, exportText(emptyState()));
  await page.getByLabel("Import method").selectOption("replace");
  await page
    .getByLabel("I understand that replacement removes my current study data.")
    .check();
  await enterNote(b, understand, "Saved after destructive replacement preview");
  await nav(b, "#/settings");
  const beforeReplace = await stored(b);
  await page.getByRole("button", { name: "Confirm replacement" }).click();
  await expect(
    page.getByText("Study data changed since this preview.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Confirm replacement" }),
  ).toBeDisabled();
  expect(await stored(page)).toEqual(beforeReplace);
  await saveEvidence(info, "native-concurrent-preservation.json", {
    body: JSON.stringify(
      {
        synthetic: true,
        browser: browserName,
        date: new Date().toISOString(),
        view: page.viewportSize(),
        preservedNotes: Object.keys(beforeReplace.notes),
        drafts: Object.keys(beforeReplace.drafts),
        reviewIds: Object.keys(beforeReplace.reviews),
        beforeFailureDigest: digest(conflicted),
        afterFailureDigest: digest(afterFailure),
        staleReplacePreserved: true,
      },
      null,
      2,
    ),
    contentType: "application/json",
  });
});

test("P2 actual >5 MB export, fresh-context import and recovery preserve all text and study records", async ({
  page,
  browser,
}, info) => {
  const base = noteState();
  let state = applyReview(
    base,
    fixtureLessons[0].cards[0],
    "dbxfe",
    "Good",
    "large-review",
    fixtureAt,
  );
  const position = {
    courseId: "dbxfe",
    lessonId: lesson,
    sectionId: why,
    offset: 0,
    updatedAt: fixtureAt,
  };
  state = {
    ...state,
    resume: position,
    positions: { [lesson]: position },
    drafts: {
      "draft-dbxfe-m02-scenario": {
        id: "draft-dbxfe-m02-scenario",
        courseId: "dbxfe",
        targetId: "dbxfe-m02-scenario",
        text: "Large backup practice draft 界 🚗",
        createdAt: fixtureAt,
        updatedAt: fixtureAt,
      },
    },
  };
  await ready(page, "/#/settings");
  await seed(page, state);
  const backup = await downloaded(page, "Export all study data");
  expect(Buffer.byteLength(backup.raw)).toBeGreaterThan(5_000_000);
  expect(parseImport(backup.raw)).toEqual(state);
  const context = await browser.newContext();
  const restored = await context.newPage();
  await ready(restored, "http://127.0.0.1:4183/#/settings");
  await upload(restored, backup.raw);
  await merge(restored);
  expect(await stored(restored)).toEqual(state);
  await restored.reload();
  expect(await stored(restored)).toEqual(state);
  await shot(restored, "correction-03-large-backup-restored");
  await nav(restored, "#/");
  await expect(restored.getByRole("link", { name: /Resume/ })).toBeVisible();
  await nav(restored, `#/lesson/${lesson}/${why}`);
  await restored
    .locator(`#${why}`)
    .getByText("Notes for this section", { exact: true })
    .click();
  await expect(
    restored.locator(`#${why}`).getByLabel("Your lesson note"),
  ).toHaveValue(state.notes[`note-${why}`].text);
  await nav(restored, "#/practice/dbxfe-m02-scenario");
  await expect(
    restored.getByRole("textbox", { name: "Your response", exact: true }),
  ).toHaveValue("Large backup practice draft 界 🚗");
  expect((await stored(restored)).reviews).toEqual(state.reviews);
  expect((await stored(restored)).schedules).toEqual(state.schedules);
  // Native write failure followed by a real recovery download (>5 MB) and restore.
  await restored.evaluate(() => {
    IDBObjectStore.prototype.put = function () {
      throw new DOMException("Synthetic quota", "QuotaExceededError");
    };
  });
  await restored
    .getByRole("textbox", { name: "Your response", exact: true })
    .fill("Unsaved large recovery final text 界 🚗");
  await expect(restored.getByRole("alert")).toContainText("Not saved");
  const recovery = await downloaded(restored, "Download recovery data");
  expect(Buffer.byteLength(recovery.raw)).toBeGreaterThan(5_000_000);
  const recovered = parseImport(recovery.raw);
  expect(recovered.drafts["draft-dbxfe-m02-scenario"].text).toBe(
    "Unsaved large recovery final text 界 🚗",
  );
  expect(recovered.notes).toEqual(state.notes);
  expect(recovered.reviews).toEqual(state.reviews);
  expect(recovered.schedules).toEqual(state.schedules);
  const fresh = await browser.newContext(),
    target = await fresh.newPage();
  await ready(target, "http://127.0.0.1:4183/#/settings");
  await upload(target, recovery.raw);
  await merge(target);
  expect(await stored(target)).toEqual(recovered);
  await saveEvidence(info, "large-backup-preservation.json", {
    body: JSON.stringify(
      {
        synthetic: true,
        date: new Date().toISOString(),
        exportBytes: Buffer.byteLength(backup.raw),
        notes: 51,
        sourceDigest: digest(state),
        restoredDigest: digest(parseImport(backup.raw)),
        recoveryBytes: Buffer.byteLength(recovery.raw),
        recoveryDigest: digest(recovered),
        finalRestoredDigest: digest(await stored(target)),
        browserVersion: browser.version(),
      },
      null,
      2,
    ),
    contentType: "application/json",
  });
  await context.close();
  await fresh.close();
});

test("P2 native framed legacy backup, compatibility reader, growth limit and invalid oversized input", async ({
  page,
  browser,
}, info) => {
  test.setTimeout(90000);
  const legacy = noteState(210, "界".repeat(35000));
  await ready(page, "/#/settings");
  await seed(page, legacy);
  await expect(
    page.getByText("This preserved collection exceeds", { exact: false }),
  ).toBeVisible();
  const backup = await downloaded(page, "Export all study data");
  expect(backup.name).toMatch(/\.jsonl$/);
  expect(Buffer.byteLength(backup.raw)).toBeGreaterThan(JSON_FILE_BYTES);
  const context = await browser.newContext(),
    other = await context.newPage();
  await ready(other, "http://127.0.0.1:4183/#/settings");
  await upload(other, backup.raw, "synthetic.jsonl");
  await merge(other);
  expect(digest(await stored(other))).toBe(digest(legacy));
  await shot(other, "correction-04-legacy-restored");
  const bad =
    '{"format":"SpicyBrain framed backup v1","parts":1,"bytes":1}\n' +
    "x".repeat(1_000_001);
  await upload(other, bad, "bad.jsonl");
  await expect(
    other.getByText("This file is invalid, too large", { exact: false }),
  ).toBeVisible();
  expect(digest(await stored(other))).toBe(digest(legacy));
  // Compatibility restores old monolithic files larger than the bounded default reader.
  const oldRaw = JSON.stringify({
    format: "SpicyBrain study data",
    exportedAt: fixtureAt,
    state: legacy,
  });
  await upload(other, oldRaw);
  await expect(
    other.getByRole("heading", { name: "Import preview" }),
  ).toHaveCount(0);
  expect(digest(await stored(other))).toBe(digest(legacy));
  await other.getByRole("button", { name: "Open older large backup" }).click();
  await merge(other);
  expect(digest(await stored(other))).toBe(digest(legacy));
  await page.getByLabel("New cards per introduction").selectOption("10");
  await expect(page.getByRole("alert")).toContainText(
    "16 MB active-data budget",
  );
  expect((await stored(page)).settings.newLimit).toBe(3);
  const recovery = await downloaded(page, "Download recovery data");
  const recovered = parseImport(recovery.raw);
  expect(recovered.settings.newLimit).toBe(10);
  expect(digest({ ...recovered, settings: legacy.settings })).toBe(
    digest(legacy),
  );
  await saveEvidence(info, "framed-legacy-preservation.json", {
    body: JSON.stringify(
      {
        synthetic: true,
        bytes: Buffer.byteLength(backup.raw),
        filename: backup.name,
        sourceDigest: digest(legacy),
        restoredDigest: digest(await stored(other)),
        legacyCompatibility: true,
        growthRejected: true,
        recoveryRestorable: true,
        browserVersion: browser.version(),
      },
      null,
      2,
    ),
    contentType: "application/json",
  });
  await context.close();
});
