import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";
import type { CatalogCourse } from "../../src/catalog-types";
import type { TeachingIndexEntry } from "../../src/teaching-schema";
import { ready, nav, noOverflow, stored, shot } from "./helpers";

// The released course's tracks, read from the generated catalog so these
// checks follow the content as modules are added. Labs, guides, cases,
// routes and capstone notices are exercised end to end on the synthetic
// fixture by `npm run test:collections`.
const catalog = JSON.parse(
  await readFile("src/generated/catalog.json", "utf8"),
) as CatalogCourse[];
const index = JSON.parse(
  await readFile("src/generated/teaching-index.json", "utf8"),
) as TeachingIndexEntry[];
const course = catalog.find((c) => c.tracks?.length);
const tracks = course?.tracks ?? [];
const moduleFiles = (page: Page) => {
  const files: string[] = [];
  page.on("request", (r) => {
    const path = new URL(r.url()).pathname;
    if (
      /\/teaching\/[^/]+\.json$/.test(path) &&
      !/\/(search|media)\.json$/.test(path)
    )
      files.push(path.slice(path.indexOf("/teaching/") + 1));
  });
  return files;
};
const axe = async (page: Page) => {
  // A theme switch fades the page's colours for a moment (the body's
  // transition); contrast is judged once nothing is still running. A
  // finished animation that fills forwards stays listed, so ask its state.
  await page.waitForFunction(() =>
    document.getAnimations().every((a) => a.playState !== "running"),
  );
  return (
    await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze()
  ).violations.map((v) => ({ id: v.id, nodes: v.nodes.map((n) => n.target) }));
};

test.skip(!course, "No registered course declares tracks");

test("A course with tracks groups its map under track headings with global numbering and loads no module", async ({
  page,
}) => {
  const files = moduleFiles(page);
  await ready(page, `/#/course/${course!.id}`);
  for (const track of tracks) {
    const section = page.locator(".academy-track").filter({
      has: page.getByRole("heading", {
        level: 2,
        name: track.title,
        exact: true,
      }),
    });
    await expect(section).toContainText(track.summary);
    await expect(section.locator(".teacher-module-map>li")).toHaveCount(
      track.moduleIds.length,
    );
  }
  await expect(page.locator(".teacher-module-map>li")).toHaveCount(
    course!.modules.length,
  );
  await expect(page.locator(".teacher-module-map h3")).toHaveCount(
    course!.modules.length,
  );
  expect(
    await page.locator(".teacher-module-map .module-index").allTextContents(),
  ).toEqual(
    tracks.flatMap((t) =>
      t.moduleIds.map((id) =>
        String(course!.modules.findIndex((m) => m.id === id) + 1).padStart(
          2,
          "0",
        ),
      ),
    ),
  );
  await page.waitForTimeout(300);
  expect(files).toEqual([]);
  for (const theme of ["dark", "light"]) {
    await nav(page, "#/settings");
    await page.getByLabel("Theme").selectOption(theme);
    await nav(page, `#/course/${course!.id}`);
    expect(await axe(page)).toEqual([]);
  }
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await nav(page, `#/course/${course!.id}`);
    await noOverflow(page);
  }
  await shot(page, "course-map-tracks-320");
});

test("A track handbook assembles only that track's modules; the scope links switch tracks and never navigate on arrow keys", async ({
  page,
}) => {
  const taught = (moduleIds: string[]) =>
    moduleIds.flatMap((id) => {
      const entry = index.find((m) => m.moduleId === id);
      return entry ? [entry.url] : [];
    });
  const [small, other] = [...tracks]
    .filter((t) => taught(t.moduleIds).length)
    .sort((a, b) => a.moduleIds.length - b.moduleIds.length);
  test.skip(!other, "Needs two tracks with teaching modules");
  const files = moduleFiles(page);
  await ready(page, `/#/handbook/${course!.id}?track=${small.id}`);
  await expect(page.locator(".handbook-chapter")).toHaveCount(
    taught(small.moduleIds).length,
  );
  expect([...files].sort()).toEqual(taught(small.moduleIds).sort());
  await expect(
    page.getByRole("navigation", { name: "Track handbook contents" }),
  ).toBeVisible();
  const scope = page.getByRole("navigation", { name: "Handbook scope" }),
    link = (title: string) =>
      scope.getByRole("link", { name: `Track: ${title}`, exact: true });
  await expect(link(small.title)).toHaveAttribute("aria-current", "page");
  // Moving through the scopes with the keyboard changes nothing (WCAG 3.2.2).
  const loaded = files.length,
    history = await page.evaluate(() => window.history.length);
  await link(small.title).focus();
  for (const key of ["ArrowDown", "ArrowUp", "ArrowDown"])
    await page.keyboard.press(key);
  await page.waitForTimeout(300);
  await expect(page).toHaveURL(new RegExp(`track=${small.id}$`));
  expect(files.length).toBe(loaded);
  expect(await page.evaluate(() => window.history.length)).toBe(history);
  // Following a scope is a route change: focus moves to the heading.
  await link(other.title).click();
  await expect(page).toHaveURL(new RegExp(`track=${other.id}$`));
  await expect(page.locator(".handbook-chapter")).toHaveCount(
    taught(other.moduleIds).length,
  );
  await expect(page.locator("main h1")).toBeFocused();
  await expect(link(other.title)).toHaveAttribute("aria-current", "page");
  await expect(scope.locator("[aria-current]")).toHaveCount(1);
  expect(await axe(page)).toEqual([]);
  await nav(page, `#/handbook/${course!.id}?track=missing-track`);
  await expect(page.getByRole("alert")).toContainText(
    "That track is not part of this course",
  );
  await expect(page.locator(".handbook-chapter")).toHaveCount(0);
});

test("Course collection routes open their shelf or explain what is missing, with a way back", async ({
  page,
}) => {
  await ready(page, `/#/course/${course!.id}`);
  // A route change inside the app moves focus to the new page's heading.
  await nav(page, `#/course/${course!.id}/labs/missing-lab`);
  await expect(page.locator("main h1")).toHaveText(
    course!.labs?.length
      ? "This lab is not in the current course."
      : "This course has no lab shelf.",
  );
  await expect(page.locator("main h1")).toBeFocused();
  await expect(
    page.getByRole("link", { name: course!.title, exact: true }),
  ).toHaveAttribute("href", `#/course/${course!.id}`);
  expect(await axe(page)).toEqual([]);
  await nav(page, `#/course/${course!.id}/unknown-section`);
  await expect(page.locator("main h1")).toHaveText(
    "That part of the course is not available.",
  );
  await nav(page, "#/course/missing-course/labs");
  await expect(page.locator("main h1")).toHaveText("Course unavailable");
});

test("The last beat names the next module in its track; Today names the saved beat's track and the beat before it", async ({
  page,
}) => {
  const track = tracks.find(
    (t) =>
      t.moduleIds.length > 1 &&
      index.some((m) => m.moduleId === t.moduleIds[0] && m.beats.length > 1),
  );
  test.skip(!track, "Needs a track whose first module has two beats");
  const first = index.find((m) => m.moduleId === track!.moduleIds[0])!,
    nextTitle =
      index.find((m) => m.moduleId === track!.moduleIds[1])?.title ??
      course!.modules.find((m) => m.id === track!.moduleIds[1])!.title;
  const last = first.beats.at(-1)!;
  await ready(page, `/#/module/${first.moduleId}/${last.id}`);
  await expect(page.locator(".teaching-beat>h2")).toHaveText(last.title);
  await expect(page.locator(".academy-next")).toContainText(
    `Next in this track: ${nextTitle}`,
  );
  await expect
    .poll(async () => (await stored(page)).beatResume?.beatId)
    .toBe(last.id);
  await nav(page, "#/");
  const cue = page.locator(".academy-reentry");
  await expect(cue).toContainText(`Track: ${track!.title}`);
  await expect(cue).toContainText(
    `Beat ${first.beats.length} of ${first.beats.length} in ${first.title}`,
  );
  await expect(cue).toContainText(`Before this: ${first.beats.at(-2)!.title}`);
  expect(await axe(page)).toEqual([]);
});
