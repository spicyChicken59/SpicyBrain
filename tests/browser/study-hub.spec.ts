import { test, expect } from "@playwright/test";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import type { Course, LearningPath } from "../../src/content-schema";
import { emptyState, migrateState, parseImport } from "../../src/study";
import { ready, nav, stored, noOverflow, shot } from "./helpers";
const paths = JSON.parse(
  await readFile("src/generated/paths.json", "utf8"),
) as LearningPath[];
const courses = JSON.parse(
  await readFile("src/generated/catalog.json", "utf8"),
) as Course[];
const path = paths.find((p) => p.defaultStart)!;
const lessons = courses.flatMap((c) => c.modules.flatMap((m) => m.lessons));
const sequence = path.groups.flatMap((g) => g.lessonIds);

test("Study hub: fresh learner, optional bridge, worked topic, solution, download and accessible responsive views", async ({
  page,
}) => {
  await ready(page);
  await expect(
    page.getByRole("navigation", { name: "Main navigation" }).getByRole("link"),
  ).toHaveText(["Today", "Learn", "Review", "Notebook"]);
  await expect(page.getByRole("heading", { name: path.title })).toBeVisible();
  await shot(page, "hub-today-desktop");
  await page.getByRole("link", { name: "Explore this path" }).click();
  await expect(
    page.getByRole("heading", { name: "Starting assumptions" }),
  ).toBeVisible();
  await expect(page.locator(".course-map ol > li")).toHaveCount(10);
  await expect(page.locator(".bridge")).toHaveCount(2);
  await shot(page, "hub-roadmap-desktop");
  const bridge = path.optionalBridges[0];
  await page.locator(".bridge").first().getByRole("link").click();
  await expect(page).toHaveURL(new RegExp(`path=${path.id}`));
  await expect(page.locator(".reader-context")).toContainText(path.title);
  await expect
    .poll(async () => (await stored(page))?.resume?.lessonId)
    .toBe(bridge.lessonId);
  await expect
    .poll(
      async () => Object.keys((await stored(page))?.completions ?? {}).length,
    )
    .toBe(0);
  await page.locator(".lesson-pagination a").last().click();
  await expect(page).toHaveURL(new RegExp(bridge.beforeLessonIds[0]));
  expect(Object.keys((await stored(page)).completions)).toHaveLength(0);
  const topic = lessons.find((l) => l.id === sequence[0])!;
  await nav(page, `#/lesson/${topic.id}?path=${path.id}`);
  await expect(page.locator(".lesson-outcomes")).toContainText(
    topic.objectives[0],
  );
  await expect(page.locator(".knowledge-check")).toHaveCount(
    topic.questions.length,
  );
  const solution = page
    .getByText("Reveal explained solution", { exact: true })
    .first();
  await expect(solution.locator("..")).not.toHaveAttribute("open", "");
  await solution.click();
  await expect(solution.locator("..")).toHaveAttribute("open", "");
  expect(Object.keys((await stored(page)).completions)).toHaveLength(0);
  await shot(page, "hub-reader-solution-desktop");
  const withDownload = lessons.find((l) => l.downloadIds?.length)!;
  await nav(page, `#/lesson/${withDownload.id}?path=${path.id}`);
  const downloadEvent = page.waitForEvent("download");
  await page.locator(".lesson-downloads a").first().click();
  const download = await downloadEvent;
  expect(download.suggestedFilename()).toMatch(/\.zip$/);
  expect(await download.failure()).toBeNull();
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await page.emulateMedia({ reducedMotion: "reduce", colorScheme: "dark" });
    for (const route of [
      "#/",
      `#/path/${path.id}`,
      "#/learn/topics",
      "#/learn/playbooks",
      `#/lesson/${sequence[0]}?path=${path.id}`,
    ]) {
      await nav(page, route);
      await noOverflow(page);
      if (width === 390 && (route === "#/" || route.startsWith("#/path/"))) {
        await page.evaluate(() => window.scrollTo(0, 0));
        await shot(
          page,
          route === "#/" ? "hub-today-mobile" : "hub-roadmap-mobile",
        );
      }
    }
    await shot(page, `hub-reader-${width}`);
  }
  await page.setViewportSize({ width: 320, height: 844 });
  await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
  await nav(page, `#/path/${path.id}`);
  await noOverflow(page);
  await shot(page, "hub-roadmap-large-text-320");
});

test("Canonical topics: two paths, direct fallback, reload, history, search and playbook detours preserve context", async ({
  page,
}) => {
  const shared = sequence.find((id) =>
    paths.some(
      (p) => p.id !== path.id && p.groups.some((g) => g.lessonIds.includes(id)),
    ),
  )!;
  expect(shared).toBeTruthy();
  const other = paths.find(
    (p) =>
      p.id !== path.id && p.groups.some((g) => g.lessonIds.includes(shared)),
  )!;
  const topic = lessons.find((l) => l.id === shared)!;
  const section = topic.sections[1].id;
  await ready(page, `/#/lesson/${shared}/${section}?path=${path.id}`);
  await expect
    .poll(async () => (await stored(page))?.resume?.pathId)
    .toBe(path.id);
  const tools = page.locator(`#${section} .section-tools`);
  await tools.getByText("Notes for this section", { exact: true }).click();
  await tools
    .getByLabel("Your lesson note")
    .fill("SYNTHETIC shared canonical topic note");
  await nav(page, `#/lesson/${shared}/${section}?path=${other.id}`);
  await expect(
    page.locator(`#${section}`).getByLabel("Your lesson note"),
  ).toHaveValue("SYNTHETIC shared canonical topic note");
  await expect(page.locator(".reader-context")).toContainText(other.title);
  await expect(page.locator(".knowledge-check")).toHaveCount(
    topic.questions.length,
  );
  await page.reload();
  await expect(page.locator(".reader-context")).toContainText(other.title);
  await expect
    .poll(async () => (await stored(page))?.resume?.pathId)
    .toBe(other.id);
  await page.getByRole("link", { name: "Search", exact: true }).click();
  await page.getByLabel("Search courses, concepts, or notes").fill(topic.title);
  await page.locator(".search-result").first().click();
  await expect(page.locator(".detour-return a")).toHaveAttribute(
    "href",
    `#/lesson/${shared}/${section}?path=${other.id}`,
  );
  await page.reload();
  await page.locator(".detour-return a").click();
  await expect(page.locator(".reader-context")).toContainText(other.title);
  await page.getByRole("link", { name: "Related task references" }).click();
  await page.locator(".playbook a").first().click();
  await expect(page.locator(".detour-return a")).toBeVisible();
  expect((await stored(page)).resume?.pathId).toBe(other.id);
  await page.locator(".detour-return a").click();
  await page.goBack();
  await expect(page.locator(".detour-return a")).toBeVisible();
  await page.goForward();
  await expect(page.locator(".reader-context")).toContainText(other.title);
  const origin = (await stored(page)).resume!;
  const originLink = `#/lesson/${shared}/${origin.sectionId}?path=${other.id}`;
  await nav(page, `#/lesson/${shared}/${topic.sections[3].id}?from=${encodeURIComponent(originLink)}`);
  // Let the 150ms initial position capture and 300ms scroll debounce both run.
  await page.waitForTimeout(400);
  expect((await stored(page)).resume).toEqual(expect.objectContaining({ courseId: origin.courseId, lessonId: origin.lessonId, sectionId: origin.sectionId, pathId: origin.pathId }));
  expect((await stored(page)).positions[shared].sectionId).toBe(origin.sectionId);
  await page.locator(".detour-return a").click();
  await expect(page).toHaveURL(new RegExp(origin.sectionId));
  await nav(page, `#/lesson/${shared}`);
  await expect(page.locator(".reader-context")).toContainText(
    "Direct topic visit",
  );
  const links = await page
    .locator(".lesson-pagination a")
    .evaluateAll((elements) => elements.map((e) => e.getAttribute("href")));
  expect(links.every((h) => !h?.includes("?path="))).toBe(true);
  await nav(page, `#/lesson/${shared}?path=removed-path`);
  await expect(page.locator(".reader-context")).toContainText(
    "unavailable or does not contain",
  );
  await expect
    .poll(async () => (await stored(page))?.resume?.pathId)
    .toBe("removed-path");
  await nav(page, "#/");
  await expect(
    page.getByText("Your saved roadmap is unavailable.", { exact: false }),
  ).toBeVisible();
  expect(
    Object.values((await stored(page)).notes).filter(
      (n) => n.text === "SYNTHETIC shared canonical topic note",
    ),
  ).toHaveLength(1);
});

test("Native baseline v2 and actual v2-format backup migrate without losing any record family", async ({
  page,
  browser,
}) => {
  const old = JSON.parse(
    await readFile("tests/fixtures/study-v2.json", "utf8"),
  );
  await ready(page);
  await page.evaluate(async (value) => {
    await new Promise<void>((resolve, reject) => {
      const r = indexedDB.open("spicybrain-study-v2", 2);
      r.onerror = () => reject(r.error);
      r.onsuccess = () => {
        const db = r.result;
        const tx = db.transaction("study", "readwrite");
        tx.objectStore("study").put(value, "root");
        tx.oncomplete = () => {
          db.close();
          resolve();
        };
      };
    });
  }, old);
  await page.reload();
  await expect(
    page.getByRole("link", { name: "Resume learning" }),
  ).toBeVisible();
  expect(await stored(page)).toEqual(migrateState(old));
  await page.getByRole("link", { name: "Resume learning" }).click();
  await expect(
    page.getByText("You completed version 1.0.0.", { exact: false }),
  ).toBeVisible();
  const upgraded = await stored(page);
  for (const family of [
    "notes",
    "drafts",
    "bookmarks",
    "completions",
    "attempts",
    "reviews",
    "schedules",
    "extraPractice",
    "assessments",
  ] as const)
    expect(upgraded[family]).toEqual(old[family]);
  await nav(page, `#/lesson/${old.resume.lessonId}?path=${path.id}`);
  await expect
    .poll(async () => (await stored(page))?.resume?.pathId)
    .toBe(path.id);
  await nav(page, "#/settings");
  const dl = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export all study data", exact: true })
    .click();
  const downloaded = await dl;
  const file = await downloaded.path();
  const exported = parseImport(await readFile(file!, "utf8"));
  expect(exported.resume?.pathId).toBe(path.id);
  expect(exported.notes).toEqual(old.notes);
  await mkdir("test-results/evidence", { recursive: true });
  await writeFile(
    "test-results/evidence/baseline-v2-migration.json",
    JSON.stringify(
      {
        baselineSchema: 2,
        migratedSchema: exported.schemaVersion,
        retainedFamilies: Object.keys(old).filter(
          (k) => typeof old[k] === "object",
        ),
        originalTimestampsPreserved: true,
        exportedPathId: exported.resume?.pathId,
      },
      null,
      2,
    ),
  );
  // Independently parse a complete, ordinary JSON backup in the actual baseline format.
  const backup = JSON.stringify({
    format: "SpicyBrain study data",
    exportedAt: "2026-09-18T12:00:00.000Z",
    state: old,
  });
  expect(parseImport(backup)).toEqual(migrateState(old));
  const context = await browser.newContext();
  const fresh = await context.newPage();
  await ready(fresh, "http://127.0.0.1:4183/#/settings");
  for (const [name, raw, expected] of [
    ["baseline-v2.json", backup, migrateState(old)],
    ["path-v3.json", await readFile(file!, "utf8"), exported],
  ] as const) {
    await fresh
      .getByLabel("Study data file")
      .setInputFiles({
        name,
        mimeType: "application/json",
        buffer: Buffer.from(raw),
      });
    await expect(
      fresh.getByRole("heading", { name: "Import preview" }),
    ).toBeVisible();
    await fresh
      .getByRole("button", { name: "Merge import", exact: true })
      .click();
    await expect(
      fresh.getByText("Import committed.", { exact: false }),
    ).toBeVisible();
    expect(await stored(fresh)).toEqual(expected);
  }
  await context.close();
});

test("All-complete and revised roadmap states remain truthful", async ({
  page,
}) => {
  const state = emptyState();
  for (const id of sequence) {
    const l = lessons.find((l) => l.id === id)!;
    state.completions[`complete-${id}`] = {
      id: `complete-${id}`,
      courseId: "dbxfe",
      lessonId: id,
      completed: true,
      contentVersion: l.contentVersion,
      updatedAt: "2026-09-19T12:00:00.000Z",
    };
  }
  await ready(page);
  await page.evaluate(async (s) => {
    await new Promise<void>((resolve) => {
      const r = indexedDB.open("spicybrain-study-v2", 2);
      r.onsuccess = () => {
        const db = r.result,
          tx = db.transaction("study", "readwrite");
        tx.objectStore("study").put(s, "root");
        tx.oncomplete = () => {
          db.close();
          resolve();
        };
      };
    });
  }, state);
  await page.reload();
  await nav(page, `#/path/${path.id}`);
  await expect(
    page.getByText("You marked every current topic complete.", {
      exact: false,
    }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Open next topic" })).toHaveCount(
    0,
  );
  state.completions[`complete-${sequence[0]}`].contentVersion = "historical";
  await page.evaluate(async (s) => {
    await new Promise<void>((resolve) => {
      const r = indexedDB.open("spicybrain-study-v2", 2);
      r.onsuccess = () => {
        const db = r.result,
          tx = db.transaction("study", "readwrite");
        tx.objectStore("study").put(s, "root");
        tx.oncomplete = () => {
          db.close();
          resolve();
        };
      };
    });
  }, state);
  await page.reload();
  await expect(
    page.getByText("A topic has changed since you marked it complete."),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Open next topic" }),
  ).toHaveAttribute("href", `#/lesson/${sequence[0]}?path=${path.id}`);
});
