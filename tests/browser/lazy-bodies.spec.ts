import { test, expect, type Page } from "@playwright/test";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import type {
  CatalogCourse,
  CourseReferences,
  LessonBody,
} from "../../src/catalog-types";
import type { TeachingIndexEntry } from "../../src/teaching-schema";
import { ready, stored } from "./helpers";

const lesson = "dbxfe-m01-l01",
  section = `${lesson}-understand`,
  scenario = "dbxfe-m02-scenario";
const body = JSON.parse(
  await readFile(`public/teaching/bodies/${lesson}.json`, "utf8"),
) as LessonBody;
const index = JSON.parse(
  await readFile("src/generated/teaching-index.json", "utf8"),
) as TeachingIndexEntry[];
const references = JSON.parse(
  await readFile("public/teaching/references/dbxfe.json", "utf8"),
) as CourseReferences;
const rubric = (
  JSON.parse(
    await readFile("src/generated/catalog.json", "utf8"),
  ) as CatalogCourse[]
)
  .flatMap((c) => c.scenarios)
  .find((s) => s.id === scenario)!.rubric;
// A plain-prose excerpt of the section text, so the assertion reads rendered
// words rather than Markdown syntax.
const excerpt = body.sections[section]
  .split("\n")
  .map((line) => line.trim())
  .find((line) => line && !/^[#|>`*-]/.test(line))!
  .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
  .replace(/[*_`]/g, "")
  .slice(0, 40);

test("A failed lesson body keeps the lesson frame, notes and bookmarks usable; Retry recovers the text and checks", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  let fail = true;
  await page.route(`**/teaching/bodies/${lesson}.json`, (route) =>
    fail
      ? route.fulfill({ status: 503, body: "synthetic outage" })
      : route.continue(),
  );
  await ready(page, `/#/lesson/${lesson}/${section}`);
  const alert = page.getByRole("alert");
  await expect(alert).toContainText("This lesson could not load");
  await expect(alert).toContainText("Your study data is safe");
  const retry = page.getByRole("button", { name: "Retry lesson", exact: true });
  await expect(retry).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Lesson sections" }).getByRole("link"),
  ).toHaveCount(7);
  await expect(page.locator(".knowledge-check")).toHaveCount(0);
  const tools = page.locator(`#${section}`);
  await tools.getByText("Notes for this section", { exact: true }).click();
  await tools
    .getByLabel("Your lesson note")
    .fill("SYNTHETIC note typed while the lesson body was unavailable");
  await expect
    .poll(async () => (await stored(page)).notes[`note-${section}`]?.text)
    .toBe("SYNTHETIC note typed while the lesson body was unavailable");
  await tools
    .getByRole("button", { name: "Bookmark section", exact: true })
    .click();
  await expect
    .poll(
      async () => (await stored(page)).bookmarks[`bookmark-${section}`]?.active,
    )
    .toBe(true);
  expect(Object.keys((await stored(page)).completions)).toHaveLength(0);
  fail = false;
  await retry.click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.locator(".knowledge-check")).toHaveCount(
    body.questions.length,
  );
  await expect(page.locator(`#${section}`)).toContainText(excerpt);
  await expect(tools.getByLabel("Your lesson note")).toHaveValue(
    "SYNTHETIC note typed while the lesson body was unavailable",
  );
  expect(errors).toEqual([]);
});

test("A failed scenario body keeps the draft editable; Retry restores the situation, task and model response", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  let fail = true;
  await page.route(`**/teaching/bodies/${scenario}.json`, (route) =>
    fail ? route.abort("failed") : route.continue(),
  );
  await ready(page, `/#/practice/${scenario}`);
  const alert = page.getByRole("alert");
  await expect(alert).toContainText("This practice item could not load");
  const retry = page.getByRole("button", {
    name: "Retry practice item",
    exact: true,
  });
  await expect(retry).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "The situation", exact: true }),
  ).toHaveCount(0);
  // The rubric's levels are in the body: no half-usable form meanwhile.
  await expect(page.locator(".rubric")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Record self-assessment" }),
  ).toHaveCount(0);
  await expect(
    page.getByText("The rubric opens with the practice item above."),
  ).toBeVisible();
  const response = page.getByRole("textbox", {
    name: "Your response",
    exact: true,
  });
  await response.fill("SYNTHETIC draft written before the scenario loaded");
  await expect
    .poll(async () => (await stored(page)).drafts[`draft-${scenario}`]?.text)
    .toBe("SYNTHETIC draft written before the scenario loaded");
  fail = false;
  await retry.click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(
    page.getByRole("heading", { name: "The situation", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Your task", exact: true }),
  ).toBeVisible();
  await page
    .getByText("Reveal model response and reasoning", { exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "One defensible response" }),
  ).toBeVisible();
  await expect(response).toHaveValue(
    "SYNTHETIC draft written before the scenario loaded",
  );
  const rubrics = page.locator(".rubric");
  await expect(rubrics).toHaveCount(rubric.length);
  for (let i = 0; i < rubric.length; i++)
    await rubrics.nth(i).getByRole("radio").nth(1).check();
  await page.getByRole("button", { name: "Record self-assessment" }).click();
  await expect
    .poll(async () => Object.keys((await stored(page)).assessments).length)
    .toBe(1);
  // A saved self-assessment names its dimensions from the catalog, so a
  // later failed body still shows criteria, not ids.
  fail = true;
  await page.goto("about:blank");
  await ready(page, `/#/practice/${scenario}`);
  await expect(page.getByRole("alert")).toContainText(
    "This practice item could not load",
  );
  await page.getByText("1 self-assessments recorded", { exact: true }).click();
  for (const dimension of rubric)
    await expect(
      page.getByText(`${dimension.criterion}: partial`, { exact: true }),
    ).toBeVisible();
  expect(errors).toEqual([]);
});

test("A failed reference file is retried from any Sources panel, updates every panel and keeps focus; card prompts never wait for it", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  let fail = true;
  await page.route("**/teaching/references/*.json", (route) =>
    fail ? route.fulfill({ status: 503, body: "" }) : route.continue(),
  );
  // Review needs card text only. A session of this lesson's three core and
  // two extension cards loads its module for the extension text; with the
  // reference file failing, every prompt still opens.
  await ready(page, "/#/settings");
  await page.getByLabel("New cards per introduction").selectOption("5");
  await ready(page, "/#/review");
  await page.getByLabel("Choose lessons").selectOption(lesson);
  const moduleFile = page.waitForResponse((r) =>
    r.url().endsWith("/teaching/dbxfe-dbxfe-m01.json"),
  );
  await page
    .getByRole("button", { name: "Introduce new cards", exact: true })
    .click();
  await moduleFile;
  await expect(
    page.getByRole("button", { name: "Reveal answer", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  // A module workspace waits for the references (its glossary popovers need
  // their definitions): while they fail it offers Retry, then it opens.
  const delta = index.find((m) => m.moduleId === "dbxfe-delta")!;
  await ready(page, `/#/module/${delta.moduleId}/${delta.beats[0].id}`);
  await expect(page.getByRole("alert")).toContainText(
    "Sources and definitions could not load",
  );
  await expect(page.locator(".teaching-beat")).toHaveCount(0);
  fail = false;
  await page.getByRole("button", { name: "Retry module", exact: true }).click();
  await expect(page.locator(".teaching-beat>h2")).toHaveText(
    delta.beats[0].title,
  );
  fail = true;
  // A fresh document for the lesson, so the references are not cached.
  await page.goto("about:blank");
  await ready(page, `/#/lesson/${lesson}`);
  await expect(page.locator(".knowledge-check")).toHaveCount(
    body.questions.length,
  );
  const panels = page.locator("details.section-sources");
  for (const i of [0, 1]) {
    await panels.nth(i).locator("summary").click();
    await expect(panels.nth(i).getByRole("alert")).toContainText(
      "could not load",
    );
  }
  fail = false;
  await panels
    .first()
    .getByRole("button", { name: "Retry", exact: true })
    .click();
  for (const i of [0, 1]) {
    await expect(panels.nth(i).getByRole("alert")).toHaveCount(0);
    await expect(panels.nth(i).getByRole("status")).toHaveCount(0);
  }
  await expect(panels.first().locator("summary")).toBeFocused();
  expect(errors).toEqual([]);
});

test("Malformed or drifted body files are refused with a retryable message and no page error", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  let served: unknown = { kind: "lesson", id: lesson };
  await page.route(`**/teaching/bodies/${lesson}.json`, (route) =>
    route.fulfill({ json: served }),
  );
  await ready(page, `/#/lesson/${lesson}`);
  await expect(page.getByRole("alert")).toContainText(
    "files are incomplete or invalid",
  );
  served = {
    ...body,
    cards: body.cards.map((c, i) =>
      i ? c : { ...c, revision: `${c.revision}-drift` },
    ),
  };
  await page.getByRole("button", { name: "Retry lesson", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Course files changed or are incomplete",
  );
  served = body;
  await page.getByRole("button", { name: "Retry lesson", exact: true }).click();
  await expect(page.locator(".knowledge-check")).toHaveCount(
    body.questions.length,
  );
  expect(errors).toEqual([]);
});

test("Each view fetches only the teaching files it needs; request counts are recorded", async ({
  page,
}) => {
  const delta = index.find((m) => m.moduleId === "dbxfe-delta")!;
  const counts: Record<
    string,
    {
      total: number;
      teaching: string[];
      bodies: number;
      modules: number;
      references: number;
    }
  > = {};
  let log: string[] = [];
  page.on("request", (request) => log.push(request.url()));
  const record = (view: string) => {
    const teaching = log
      .filter((url) => url.includes("/teaching/"))
      .map((url) => url.slice(url.indexOf("/teaching/")));
    counts[view] = {
      total: log.length,
      teaching,
      bodies: teaching.filter((u) => u.startsWith("/teaching/bodies/")).length,
      references: teaching.filter((u) => u.startsWith("/teaching/references/"))
        .length,
      modules: teaching.filter(
        (u) =>
          !u.startsWith("/teaching/bodies/") &&
          !u.startsWith("/teaching/references/") &&
          !/\/(?:search|media)\.json$/.test(u),
      ).length,
    };
    log = [];
  };
  const open = async (
    view: string,
    hash: string,
    settle: () => Promise<void>,
  ) => {
    log = [];
    await ready(page, `/${hash}`);
    await settle();
    // Let deferred fetches (media references, positions) finish.
    await page.waitForTimeout(400);
    record(view);
  };
  const h1 = async () => {
    await expect(page.locator("main h1")).toBeVisible();
  };
  await open("today", "#/", h1);
  await open("courseMap", "#/course/dbxfe", async () => {
    await expect(page.locator(".teacher-module-map>li")).toHaveCount(
      index.filter((m) => m.courseId === "dbxfe").length,
    );
  });
  await open("lesson", `#/lesson/${lesson}`, async () => {
    await expect(page.locator(".knowledge-check")).toHaveCount(
      body.questions.length,
    );
  });
  await open(
    "moduleBeat",
    `#/module/${delta.moduleId}/${delta.beats[0].id}`,
    async () => {
      await expect(page.locator(".teaching-beat>h2")).toHaveText(
        delta.beats[0].title,
      );
    },
  );
  await open("practice", `#/practice/${scenario}`, async () => {
    await expect(
      page.getByRole("heading", { name: "The situation", exact: true }),
    ).toBeVisible();
  });
  await open("review", "#/review", h1);
  log = [];
  await page.getByLabel("Choose lessons").selectOption("all");
  await page
    .getByRole("button", { name: "Introduce new cards", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Reveal answer", exact: true }),
  ).toBeVisible();
  await page.waitForTimeout(200);
  record("reviewSession");
  // In a fresh document (the views above share one), a lesson fetches the
  // reference tier only when a Sources panel first opens; a second panel
  // reuses it.
  await page.goto("about:blank");
  await ready(page, `/#/lesson/${lesson}`);
  await expect(page.locator(".knowledge-check")).toHaveCount(
    body.questions.length,
  );
  await page.waitForTimeout(400);
  log = [];
  const panels = page.locator("details.section-sources");
  await Promise.all([
    page.waitForResponse((r) => r.url().includes("/teaching/references/")),
    panels.first().locator("summary").click(),
  ]);
  await expect(panels.first().getByRole("status")).toHaveCount(0);
  await expect(panels.first().getByRole("alert")).toHaveCount(0);
  // The panel shows the claims its section cites (read from the body) with
  // their text (read from the reference file).
  const [firstSection] = Object.keys(body.sectionClaims);
  expect(body.sectionClaims[firstSection].length).toBeGreaterThan(0);
  for (const id of body.sectionClaims[firstSection])
    await expect(panels.first()).toContainText(
      references.claims.find((c) => c.id === id)!.description,
    );
  await panels.nth(1).locator("summary").click();
  await expect(panels.nth(1).getByRole("status")).toHaveCount(0);
  await page.waitForTimeout(200);
  record("lessonSources");
  // A practice page, in a fresh document, fetches no reference file either.
  await page.goto("about:blank");
  log = [];
  await ready(page, `/#/practice/${scenario}`);
  await expect(
    page.getByRole("heading", { name: "The situation", exact: true }),
  ).toBeVisible();
  await page.waitForTimeout(400);
  record("practiceFresh");
  expect(counts.today.teaching).toEqual([]);
  expect(counts.courseMap.teaching).toEqual([]);
  expect(counts.lesson.bodies).toBe(1);
  expect(counts.lesson.modules).toBe(0);
  expect(counts.lesson.references).toBe(0);
  expect(counts.lessonSources.teaching).toEqual([
    "/teaching/references/dbxfe.json",
  ]);
  expect(counts.practice.bodies).toBe(1);
  expect(counts.practiceFresh.bodies).toBe(1);
  expect(counts.practiceFresh.references).toBe(0);
  expect(counts.moduleBeat.modules).toBe(1);
  expect(counts.moduleBeat.references).toBe(1);
  expect(counts.moduleBeat.bodies).toBeGreaterThanOrEqual(
    delta.lessonIds.length,
  );
  expect(counts.reviewSession.bodies).toBeGreaterThanOrEqual(1);
  expect(counts.reviewSession.modules).toBe(0);
  await mkdir("test-results/evidence", { recursive: true });
  await writeFile(
    "test-results/evidence/request-counts.json",
    JSON.stringify({ at: new Date().toISOString(), views: counts }, null, 2) +
      "\n",
  );
});

async function noPageErrors(page: Page) {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  return () => expect(errors).toEqual([]);
}

test("The review history panel lists lesson titles immediately and fetches prompts only when opened", async ({
  page,
}) => {
  const check = await noPageErrors(page);
  await ready(page, `/#/review/${lesson}`);
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
  await page.getByRole("button", { name: "End session", exact: true }).click();
  const requests: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/teaching/bodies/"))
      requests.push(request.url());
  });
  // A fresh document (a hash-only goto keeps the session's cached lesson
  // body), so the page itself must open without a body request.
  await ready(page, "/#/review");
  await page.reload();
  await expect(page.locator("main h1")).toBeVisible();
  await page.waitForTimeout(300);
  expect(requests).toEqual([]);
  const history = page.locator(".review-history");
  await history.locator("summary").click();
  const reviewed = Object.values((await stored(page)).reviews)[0];
  const prompt = body.cards.find((c) => c.id === reviewed.cardId)!.prompt;
  await expect(history).toContainText(prompt);
  expect(requests.length).toBe(1);
  await check();
});
