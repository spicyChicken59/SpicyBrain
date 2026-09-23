import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import type { Question } from "../../src/content-schema";
import type { CatalogCourse, LessonBody } from "../../src/catalog-types";
import type { TeachingModule, TeachingMedia } from "../../src/teaching-schema";
import { parseImport } from "../../src/study";
import { ready, nav, stored, noOverflow, shot } from "./helpers";
const delta = JSON.parse(
  await readFile("content/teaching/dbxfe/dbxfe-delta.json", "utf8"),
) as TeachingModule;
const course = (
  JSON.parse(
    await readFile("src/generated/catalog.json", "utf8"),
  ) as CatalogCourse[]
)[0];
// Question text lives in the lazy lesson bodies, not the initial catalog.
const lessonQuestions: Question[] = (
  await Promise.all(
    course.modules
      .flatMap((m) => m.lessons)
      .map(
        async (l) =>
          (
            JSON.parse(
              await readFile(`public/teaching/bodies/${l.id}.json`, "utf8"),
            ) as LessonBody
          ).questions,
      ),
  )
).flat();
const media = JSON.parse(
  await readFile("content/teaching/dbxfe/media.json", "utf8"),
) as TeachingMedia[];
const beat = delta.beats[0],
  visual = delta.visuals.find((v) => v.id === beat.visualId)!;
const href = (view = "deck") =>
  `#/module/${delta.moduleId}/${beat.id}?view=${view}`;
for (const base of ["/", "/SpicyBrain/"])
  test(`Teacher journey A–G: course, stage, handbook, check, cards and exact resume ${base}`, async ({
    page,
    context,
  }) => {
    const errors: string[] = [],
      outgoing: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("request", (r) => {
      if (!r.url().startsWith("http://127.0.0.1")) outgoing.push(r.url());
    });
    await ready(page, base);
    await page
      .getByRole("link", { name: "Open the course", exact: false })
      .click();
    await expect(page.locator(".teacher-module-map>li")).toHaveCount(
      course.modules.length,
    );
    await page
      .getByRole("heading", { name: delta.title, exact: true })
      .getByRole("link")
      .click();
    await expect(page.locator(".teaching-beat>h2")).toHaveText(beat.title);
    const stage = page
      .locator(".teaching-beat .visual-stages")
      .first()
      .getByRole("button")
      .nth(1);
    await stage.click();
    await expect(stage).toHaveAttribute("aria-pressed", "true");
    await expect
      .poll(async () => (await stored(page)).beatResume?.visualStateId)
      .toBe(visual.states[1].id);
    const samajh = page.locator(".samajh");
    await expect(samajh).not.toHaveAttribute("open");
    await samajh.locator("summary").click();
    await expect(samajh).toContainText(beat.samajh!.boundary);
    const check = page.locator(".beat-check").first();
    await expect(check).not.toHaveAttribute("open");
    await check.locator("summary").click();
    const response = check.locator("textarea");
    if (await response.count()) {
      await response.fill(
        "SYNTHETIC teacher-first reasoning: select committed files, not every stored file.",
      );
      await check
        .getByRole("button", { name: "Reveal model reasoning" })
        .click();
      await expect(check).toContainText("No automatic score");
    }
    await expect
      .poll(async () => Object.keys((await stored(page)).completions).length)
      .toBe(0);
    await page
      .getByRole("button", {
        name: "Open handbook beside this beat",
        exact: true,
      })
      .click();
    const pane = page.getByRole("complementary", {
      name: "Handbook beside the deck",
    });
    await expect(pane).toBeVisible();
    await expect(
      pane.getByRole("heading", { name: beat.title, exact: true }),
    ).toBeVisible();
    await pane.evaluate((e) => {
      e.scrollTop = 500;
    });
    await expect(stage).toHaveAttribute("aria-pressed", "true");
    await page
      .getByRole("link", { name: "Handbook in a new tab", exact: false })
      .scrollIntoViewIfNeeded();
    await page.waitForTimeout(350);
    const before = (await stored(page)).beatResume!;
    const popupEvent = context.waitForEvent("page");
    await page
      .getByRole("link", { name: "Handbook in a new tab", exact: false })
      .click();
    const popup = await popupEvent;
    await popup.waitForSelector(".module-handbook");
    await expect(popup.locator(`#handbook-${beat.id}>h2`)).toHaveText(
      beat.title,
    );
    await popup.evaluate(() => scrollTo(0, 900));
    await popup.waitForTimeout(350);
    expect((await stored(popup)).beatResume).toEqual(before);
    await popup.close();
    await page
      .getByRole("button", { name: "Close handbook", exact: true })
      .click();
    await page
      .locator(".teaching-tabs")
      .getByRole("link", { name: "Cards", exact: true })
      .click();
    await page
      .getByRole("combobox", { name: "Card set", exact: true })
      .selectOption("extension");
    await expect(page.locator(".card-library>details")).toHaveCount(4);
    await expect
      .poll(async () => Object.keys((await stored(page)).schedules).length)
      .toBe(0);
    await page
      .locator(".card-library>details")
      .first()
      .locator("summary")
      .first()
      .click();
    await expect(page.locator(".card-library")).toContainText(
      "Why it matters:",
    );
    await page
      .getByRole("button", { name: "Review this selection", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Introduce new cards", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Reveal answer", exact: true })
      .click();
    await page.getByRole("button", { name: "Good", exact: true }).click();
    await expect
      .poll(async () => Object.keys((await stored(page)).reviews).length)
      .toBe(1);
    await nav(page, href());
    await expect(stage).toHaveAttribute("aria-pressed", "true");
    if (await response.count())
      await expect(response).toHaveValue(/SYNTHETIC teacher-first/);
    await page
      .getByRole("button", { name: "Mark this beat complete", exact: true })
      .click();
    await expect
      .poll(
        async () =>
          (await stored(page)).completions[`beat-${beat.id}`]?.completed,
      )
      .toBe(true);
    await page.locator(".teaching-beat>h2").scrollIntoViewIfNeeded();
    await shot(page, `teacher-journey-${base === "/" ? "root" : "nested"}`);
    await page.locator(".module-options>summary").click();
    await page.getByLabel("Show Samajh analogies").uncheck();
    await nav(page, "#/");
    await page
      .getByRole("link", { name: "Resume learning", exact: false })
      .click();
    await expect(stage).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator(".samajh")).toHaveCount(0);
    await page.reload();
    await expect(stage).toHaveAttribute("aria-pressed", "true");
    await nav(page, "#/settings");
    const downloadEvent = page.waitForEvent("download");
    await page
      .getByRole("button", { name: "Export all study data", exact: true })
      .click();
    const file = await (await downloadEvent).path();
    const exported = parseImport(await readFile(file!, "utf8"));
    expect(exported.beatResume?.beatId).toBe(beat.id);
    expect(exported.beatResume?.visualStateId).toBe(visual.states[1].id);
    expect(exported.settings.showSamajh).toBe(false);
    expect(Object.keys(exported.reviews)).toHaveLength(1);
    expect(outgoing).toEqual([]);
    expect(errors).toEqual([]);
  });
test("Glossary is hoverable, keyboard dismissible and persistent; visual enlargement returns focus", async ({
  page,
}) => {
  await ready(page, `/${href()}`);
  const term = page.locator(".beat-explanation .concept-term").first();
  await term.hover();
  const definition = page.getByRole("dialog", { name: /definition$/ });
  await expect(definition).toBeVisible();
  await definition.hover();
  await expect(definition).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(definition).toHaveCount(0);
  await expect(term).toBeFocused();
  await page.keyboard.press("Tab");
  await term.focus();
  await expect(definition).toBeVisible();
  await definition.getByRole("button", { name: "Close definition" }).click();
  await expect(definition).toHaveCount(0);
  await expect(term).toBeFocused();
  const enlarge = page
    .getByRole("button", { name: "Enlarge visual", exact: true })
    .first();
  await enlarge.click();
  await expect(page.getByRole("dialog", { name: /enlarged$/ })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(enlarge).toBeFocused();
});
test("Objective answer produces correct immutable evidence; reveal and navigation never imply completion", async ({
  page,
}) => {
  const questions: Question[] = [...delta.questions, ...lessonQuestions];
  const b = delta.beats.find((b) =>
    b.questionIds.some((id) => questions.some((q) => q.id === id)),
  )!;
  const q = questions.find((q) => b.questionIds.includes(q.id))!;
  expect(b).toBeTruthy();
  await ready(page, `/#/module/${delta.moduleId}/${b.id}`);
  const check = page.locator(".beat-check").filter({ hasText: q.prompt });
  await check.locator("summary").click();
  const wrong = q.options.find((o) => o.id !== q.correctOptionId)!;
  await check.getByRole("radio").nth(q.options.indexOf(wrong)).check();
  await check
    .getByRole("button", { name: "Check my answer", exact: true })
    .click();
  await expect
    .poll(async () => Object.values((await stored(page)).attempts).length)
    .toBe(1);
  const a = Object.values((await stored(page)).attempts)[0];
  expect(a.correct).toBe(false);
  expect(a.optionId).toBe(wrong.id);
  expect(a.correctOptionId).toBe(q.correctOptionId);
  expect(a.snapshot.options).toEqual(q.options);
  expect(Object.keys((await stored(page)).completions)).toHaveLength(0);
  await page.reload();
  await expect(check).toHaveAttribute("open", "");
  await expect(check).toContainText(wrong.rationale);
  await check.getByRole("button", { name: "Try again", exact: true }).click();
  await check
    .getByRole("radio")
    .nth(q.options.findIndex((o) => o.id === q.correctOptionId))
    .check();
  await check
    .getByRole("button", { name: "Check my answer", exact: true })
    .click();
  await expect
    .poll(async () => Object.values((await stored(page)).attempts).length)
    .toBe(2);
  expect(
    Object.values((await stored(page)).attempts).filter((a) => a.correct),
  ).toHaveLength(1);
});
test("Video is consent-gated; blocked player keeps original link and authored equivalent", async ({
  page,
}) => {
  const item = media.find((m) => m.moduleId === delta.moduleId)!;
  expect(item.embedUrl).toBeTruthy();
  let requests = 0;
  await page.route("**/teaching/media.json", (r) =>
    r.fulfill({ json: [{ ...item, embeddingStatus: "verified" }] }),
  );
  await page.route("https://**/*", (r) => {
    requests++;
    return r.abort();
  });
  await ready(page, `/#/module/${delta.moduleId}/${item.beatId}`);
  await page.locator(".beat-media>summary").click();
  expect(requests).toBe(0);
  await expect(page.locator("iframe")).toHaveCount(0);
  await page
    .getByRole("button", { name: "Load video player", exact: true })
    .click();
  await expect.poll(() => requests).toBeGreaterThan(0);
  await expect(page.locator("iframe")).toHaveAttribute("src", item.embedUrl!);
  expect(item.embedUrl).not.toContain("autoplay");
  await page.getByRole("button", { name: /Player unavailable/ }).click();
  await expect(
    page.getByText(
      "The original link and illustrated explanation remain available.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(
    page
      .locator(".beat-media")
      .getByRole("link", { name: /Open original video/ }),
  ).toHaveAttribute("href", item.url);
  await expect(page.locator(".beat-media details[open]")).toContainText(
    item.fallback.title,
  );
  expect(Object.keys((await stored(page)).completions)).toHaveLength(0);
  await page
    .getByRole("button", { name: "Unload player", exact: true })
    .click();
  await expect(page.locator("iframe")).toHaveCount(0);
});
test("All modules render purposeful visuals in light/dark at desktop and narrow widths; no silent completion", async ({
  page,
}) => {
  test.setTimeout(120000);
  const report = [];
  for (const m of course.modules) {
    const content = JSON.parse(
      await readFile(`content/teaching/dbxfe/${m.id}.json`, "utf8"),
    ) as TeachingModule;
    for (const width of [1440, 390, 320]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.emulateMedia({
        colorScheme: width === 390 ? "dark" : "light",
        reducedMotion: "reduce",
      });
      await ready(page, `/#/module/${m.id}/${content.beats[0].id}`);
      await expect(page.locator(".teaching-beat>h2")).toHaveText(
        content.beats[0].title,
      );
      await noOverflow(page);
      if (width !== 320) {
        await page.locator(".teaching-beat>h2").scrollIntoViewIfNeeded();
        await shot(page, `teacher-${m.id}-${width}`);
      }
    }
    report.push({
      moduleId: m.id,
      beatCount: content.beats.length,
      handbookSections: content.beats.length,
      visuals: content.visuals.length,
      viewports: [1440, 390, 320],
    });
  }
  expect(Object.keys((await stored(page)).completions)).toHaveLength(0);
  await mkdir("test-results/evidence", { recursive: true });
  await writeFile(
    "test-results/evidence/teacher-module-browser.json",
    JSON.stringify({ at: new Date().toISOString(), report }, null, 2),
  );
});
test("Accessible reading controls, real doubled text, dark/light/auto and usable print handbook", async ({
  page,
}) => {
  await ready(page, `/${href()}`);
  await page.locator(".module-options>summary").click();
  await page.locator(".beat-check>summary").first().click();
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
  await page.setViewportSize({ width: 320, height: 1000 });
  await page.evaluate(() => {
    const nodes = [
      ...document.querySelectorAll<HTMLElement>(".teacher-workspace *"),
    ];
    const sizes = nodes.map((n) => parseFloat(getComputedStyle(n).fontSize));
    nodes.forEach((n, i) => (n.style.fontSize = `${sizes[i] * 2}px`));
  });
  await noOverflow(page);
  await shot(page, "teacher-320-double-text");
  await page.reload();
  for (const theme of ["dark", "light", "auto"]) {
    await nav(page, "#/settings");
    await page
      .getByRole("combobox", { name: "Theme", exact: true })
      .selectOption(theme);
    await nav(page, href());
    await noOverflow(page);
  }
  await nav(page, href("handbook"));
  await expect(page.locator(".handbook-article")).toHaveCount(
    delta.beats.length,
  );
  await page.emulateMedia({ media: "print" });
  await expect(page.locator(".sc-masthead")).not.toBeVisible();
  await expect(page.locator(".handbook-article").first()).toBeVisible();
  await shot(page, "teacher-handbook-print");
});
test("Module failure and unknown beat are recoverable without deleting study state", async ({
  page,
}) => {
  await ready(page, `/${href()}`);
  const before = await stored(page);
  await page.route("**/teaching/dbxfe-dbxfe-genai.json", (r) => r.abort());
  await nav(page, "#/module/dbxfe-genai");
  await expect(
    page.getByRole("button", { name: "Retry module", exact: true }),
  ).toBeVisible();
  expect((await stored(page)).beatResume).toEqual(before.beatResume);
  await nav(page, `#/module/${delta.moduleId}/removed-beat`);
  await expect(
    page.getByRole("heading", { name: "That teaching beat is unavailable" }),
  ).toBeVisible();
  expect((await stored(page)).beatResume).toEqual(before.beatResume);
});

test("Complete course handbook assembles every module and keeps main study resume unchanged", async ({
  page,
}) => {
  await ready(page, `/${href()}`);
  const before = (await stored(page)).beatResume;
  await nav(page, "#/handbook/dbxfe");
  const expected = await Promise.all(
    course.modules.map(
      async (m) =>
        JSON.parse(
          await readFile(`content/teaching/dbxfe/${m.id}.json`, "utf8"),
        ) as TeachingModule,
    ),
  );
  await expect(page.locator(".handbook-chapter")).toHaveCount(expected.length);
  await expect(page.locator(".handbook-article")).toHaveCount(
    expected.reduce((n, m) => n + m.beats.length, 0),
  );
  const last = course.modules.at(-1)!;
  await page
    .getByRole("navigation", { name: "Course handbook contents" })
    .getByRole("link", { name: last.title, exact: true })
    .click();
  await expect(page.locator(`#chapter-${last.id}>h2`)).toBeInViewport();
  expect((await stored(page)).beatResume).toEqual(before);
  await page.evaluate(() => window.dispatchEvent(new Event("beforeprint")));
  await expect(
    page.locator(".course-handbook details:not([open])"),
  ).toHaveCount(0);
  await page.emulateMedia({ media: "print" });
  await expect(page.locator(".handbook-chapter").last()).toBeVisible();
  await shot(page, "teacher-complete-handbook-print");
  await page.evaluate(() => window.dispatchEvent(new Event("afterprint")));
});
