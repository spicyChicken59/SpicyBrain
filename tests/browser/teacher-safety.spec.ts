import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import type { TeachingMedia, TeachingModule } from "../../src/teaching-schema";
import { ready, nav, stored } from "./helpers";

const delta = JSON.parse(
  await readFile("content/teaching/dbxfe/dbxfe-delta.json", "utf8"),
) as TeachingModule;
const platform = JSON.parse(
  await readFile("content/teaching/dbxfe/dbxfe-m03.json", "utf8"),
) as TeachingModule;
const commit = delta.beats.find((b) => b.id === "dbxfe-delta-commit")!;
const commitHref = `#/module/${delta.moduleId}/${commit.id}`;

test("A malformed successful module response is recoverable, and retry fetches valid content", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  let malformed = true;
  await page.route("**/teaching/dbxfe-dbxfe-delta.json", (route) =>
    malformed
      ? route.fulfill({
          json: {
            schemaVersion: 1,
            moduleId: delta.moduleId,
            courseId: delta.courseId,
          },
        })
      : route.continue(),
  );
  await ready(page);
  const beforeFailure = await stored(page);
  await nav(page, commitHref);
  await expect(
    page.getByRole("button", { name: "Retry module", exact: true }),
  ).toBeVisible();
  const afterFailure = await stored(page);
  expect(afterFailure?.beatResume ?? null).toBeNull();
  expect(afterFailure).toEqual(beforeFailure);
  malformed = false;
  await page.getByRole("button", { name: "Retry module", exact: true }).click();
  await expect(page.locator(".teaching-beat>h2")).toHaveText(commit.title);
  expect(errors).toEqual([]);
});

test("Malformed media metadata cannot blank the illustrated teaching beat", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/teaching/media.json", (route) =>
    route.fulfill({ json: [{ id: "broken-media" }] }),
  );
  await ready(page, `/${commitHref}`);
  await expect(page.locator(".teaching-beat>h2")).toHaveText(commit.title);
  await expect(page.getByText(/Video references could not load/)).toBeVisible();
  await expect(
    page.locator(".teaching-beat .teaching-visual").first(),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("A media fallback referencing a concept instead of a visual leaves the lesson usable", async ({
  page,
}) => {
  const media = JSON.parse(
    await readFile("content/teaching/dbxfe/media.json", "utf8"),
  ) as TeachingMedia[];
  const item = media.find((m) => m.moduleId === delta.moduleId)!;
  const beat = delta.beats.find((b) => b.id === item.beatId)!;
  // This ID is real and present in the index's generic reference list, but it
  // names the wrong kind of content and cannot be rendered as a visual.
  item.fallback.visualId = delta.concepts[0].id;
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/teaching/media.json", (route) =>
    route.fulfill({ json: media }),
  );
  await ready(page, `/#/module/${delta.moduleId}/${beat.id}`);
  await expect(page.locator(".teaching-beat>h2")).toHaveText(beat.title);
  await expect(page.getByText(/Video references could not load/)).toBeVisible();
  await expect(
    page.locator(".teaching-beat .teaching-visual").first(),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test("Opening a previously visited module recovers its saved beat after studying another module", async ({
  page,
}) => {
  await ready(page, `/${commitHref}`);
  await expect
    .poll(async () => (await stored(page)).beatResume?.beatId)
    .toBe(commit.id);
  await nav(page, `#/module/${platform.moduleId}/${platform.beats[0].id}`);
  await expect
    .poll(async () => (await stored(page)).beatResume?.moduleId)
    .toBe(platform.moduleId);
  await nav(page, `#/course/${delta.courseId}`);
  await page
    .getByRole("heading", { name: delta.title, exact: true })
    .getByRole("link")
    .click();
  await expect(page.locator(".teaching-beat>h2")).toHaveText(commit.title);
});

test("A lesson cross-link inside a teaching-reference detour keeps the return to the beat", async ({
  page,
}) => {
  await ready(page, `/${commitHref}`);
  await expect
    .poll(async () => (await stored(page)).beatResume?.beatId)
    .toBe(commit.id);
  await nav(
    page,
    `#/lesson/dbxfe-dataframes?from=${encodeURIComponent(commitHref)}`,
  );
  const bridge = page.getByRole("link", { name: "Python bridge", exact: true });
  await expect(bridge).toBeVisible();
  const href = (await bridge.getAttribute("href"))!;
  expect(new URLSearchParams(href.split("?")[1]).get("from")).toBe(commitHref);
  await bridge.click();
  const back = page.getByRole("link", {
    name: /Return to your saved learning context/,
  });
  await expect(back).toHaveAttribute("href", commitHref);
  await back.click();
  await expect(page.locator(".teaching-beat>h2")).toHaveText(commit.title);
});

test("A handbook popup cannot make the next main-deck action resume into the handbook", async ({
  page,
  context,
}) => {
  await ready(page, `/${commitHref}`);
  await expect
    .poll(async () => (await stored(page)).beatResume?.view)
    .toBe("deck");
  const popupEvent = context.waitForEvent("page");
  await page.getByRole("link", { name: /Handbook in a new tab/ }).click();
  const popup = await popupEvent;
  await expect(popup.locator(".module-handbook")).toBeVisible();
  await popup.evaluate(() => window.scrollBy(0, 400));
  await popup.waitForTimeout(400);
  expect((await stored(popup)).beatResume?.view).toBe("deck");
  await popup.close();

  const stage = page
    .locator(".teaching-beat .visual-stages")
    .first()
    .getByRole("button")
    .nth(1);
  await stage.click();
  await expect(stage).toHaveAttribute("aria-pressed", "true");
  await expect
    .poll(async () => (await stored(page)).beatResume?.visualStateId)
    .toBe(delta.visuals.find((v) => v.id === commit.visualId)!.states[1].id);
  expect((await stored(page)).beatResume?.view).toBe("deck");
  await nav(page, "#/");
  await page.getByRole("link", { name: /Resume learning/ }).click();
  await expect(page.locator(".teaching-beat>h2")).toHaveText(commit.title);
  await expect(stage).toHaveAttribute("aria-pressed", "true");
});

test("A definition near the lower viewport edge keeps its explanation and close control reachable", async ({
  page,
}) => {
  await page.setViewportSize({ width: 320, height: 640 });
  const beat = platform.beats.find((b) => b.id === "dbxfe-m03-transfer")!;
  await ready(page, `/#/module/${platform.moduleId}/${beat.id}`);
  const term = page.locator(".beat-explanation .concept-term").first();
  await term.evaluate((element) => {
    window.scrollBy(
      0,
      element.getBoundingClientRect().top - (innerHeight - 70),
    );
  });
  await term.focus();
  const popover = page.getByRole("dialog", { name: /definition$/ });
  await expect(popover).toBeVisible();
  await expect
    .poll(async () =>
      popover.evaluate((element) => {
        const rect = element.getBoundingClientRect();
        return (
          rect.top >= 0 &&
          rect.bottom <= innerHeight &&
          rect.left >= 0 &&
          rect.right <= innerWidth
        );
      }),
    )
    .toBe(true);
  await popover
    .getByRole("button", { name: "Close definition", exact: true })
    .click();
  await expect(popover).toHaveCount(0);
  await expect(term).toBeFocused();
});

test("A saved teaching-question draft remains linked to its real source in Notebook", async ({
  page,
}) => {
  const beat = platform.beats.find((b) => b.id === "dbxfe-m03-transfer")!;
  const question = platform.selfQuestions.find((q) =>
    beat.questionIds.includes(q.id),
  )!;
  await ready(page, `/#/module/${platform.moduleId}/${beat.id}`);
  const check = page
    .locator(".beat-check")
    .filter({ hasText: question.prompt });
  await check.locator("summary").click();
  await check
    .getByRole("textbox")
    .fill("SYNTHETIC safety audit: the source concept is still present.");
  await expect
    .poll(async () => (await stored(page)).drafts[`draft-${question.id}`]?.text)
    .toContain("SYNTHETIC safety audit");
  await nav(page, "#/notebook");
  const draft = page.locator(".draft-details");
  await expect(draft).toHaveCount(1);
  await expect(draft.locator("summary")).not.toContainText("Removed content");
  await draft.locator("summary").click();
  const source = draft.getByRole("link");
  await expect(source).toHaveAttribute("href", new RegExp(beat.id));
  await source.click();
  await expect(page.locator(".teaching-beat>h2")).toHaveText(beat.title);
});

for (const revealed of [false, true])
  test(`A stale imported answer choice cannot create malformed grading evidence (revealed=${revealed})`, async ({
    page,
  }) => {
    const question = delta.questions[0];
    const beat = delta.beats.find((b) => b.questionIds.includes(question.id))!;
    const href = `/#/module/${delta.moduleId}/${beat.id}`;
    await ready(page, href);
    await expect.poll(async () => (await stored(page))?.schemaVersion).toBe(4);
    const state = await stored(page);
    const id = `check-${question.id}`;
    state.beatChecks[id] = {
      id,
      courseId: delta.courseId,
      moduleId: delta.moduleId,
      beatId: beat.id,
      questionId: question.id,
      questionRevision: question.revision,
      selectedOptionId: "removed-choice",
      opened: true,
      revealed,
      updatedAt: "2026-09-20T12:00:00.000Z",
    };
    // Model a valid backup containing an unavailable content reference. Preserve
    // it in storage; the current UI must require a real current answer choice.
    await page.route("**/__teacher-stale-seed", (route) =>
      route.fulfill({
        contentType: "text/html",
        body: "<title>Synthetic seed</title>",
      }),
    );
    await page.goto("/__teacher-stale-seed");
    await page.evaluate(
      (state) =>
        new Promise<void>((resolve, reject) => {
          const request = indexedDB.open("spicybrain-study-v2", 2);
          request.onerror = () => reject(request.error);
          request.onsuccess = () => {
            const db = request.result;
            const tx = db.transaction("study", "readwrite");
            tx.objectStore("study").put(state, "root");
            tx.oncomplete = () => {
              db.close();
              resolve();
            };
            tx.onerror = () => reject(tx.error);
          };
        }),
      state,
    );
    await ready(page, href);
    const check = page
      .locator(".beat-check")
      .filter({ hasText: question.prompt });
    await expect(check.locator("input:checked")).toHaveCount(0);
    const retry = check.getByRole("button", { name: "Try again", exact: true });
    if (await retry.isVisible()) await retry.click();
    const grade = check.getByRole("button", {
      name: "Check my answer",
      exact: true,
    });
    await expect(grade).toBeDisabled();
    await check
      .getByRole("radio")
      .nth(question.options.findIndex((o) => o.id === question.correctOptionId))
      .check();
    await grade.click();
    await expect
      .poll(async () => Object.values((await stored(page)).attempts).length)
      .toBe(1);
    const attempt = Object.values((await stored(page)).attempts)[0];
    expect(attempt.optionId).toBe(question.correctOptionId);
    expect(attempt.correct).toBe(true);
    await expect(
      page.getByText("Unsaved · keep this tab open", { exact: true }),
    ).toHaveCount(0);
  });

test("Course Resume keeps the main deck context after a handbook detour to another beat", async ({
  page,
}) => {
  await ready(page, `/${commitHref}`);
  await expect
    .poll(async () => (await stored(page)).beatResume?.beatId)
    .toBe(commit.id);
  const detourBeat = delta.beats.find((b) => b.id !== commit.id)!;
  await nav(
    page,
    `#/module/${delta.moduleId}/${detourBeat.id}?view=handbook&detour=1`,
  );
  await expect(page.locator(".module-handbook")).toBeVisible();
  await expect
    .poll(async () => (await stored(page)).beatPositions[detourBeat.id]?.view)
    .toBe("handbook");
  expect((await stored(page)).beatResume?.beatId).toBe(commit.id);
  await nav(page, `#/course/${delta.courseId}`);
  const resume = page.getByRole("link", {
    name: "Resume the course →",
    exact: true,
  });
  await expect(resume).toHaveAttribute("href", commitHref);
  await resume.click();
  await expect(page.locator(".teaching-beat>h2")).toHaveText(commit.title);
});
