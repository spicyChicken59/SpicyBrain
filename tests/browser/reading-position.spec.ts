import { readFile } from "node:fs/promises";
import { test, expect } from "@playwright/test";
import type { CatalogCourse } from "../../src/catalog-types";
import { nav, ready, stored } from "./helpers";

const courses = JSON.parse(
  await readFile("src/generated/catalog.json", "utf8"),
) as CatalogCourse[];
const lesson = courses
  .flatMap((c) => c.modules.flatMap((m) => m.lessons))
  .find((l) => l.id === "dbxfe-m04-l02")!;

const saved = async (page: import("@playwright/test").Page) =>
  (await stored(page))?.positions[lesson.id]?.sectionId;

test("Scrolling above the first section keeps the saved reading place; reading a section moves it; a first visit records the first section", async ({
  page,
}) => {
  const [first, second] = lesson.sections;
  await ready(page, `/#/lesson/${lesson.id}`);
  await expect.poll(() => saved(page)).toBe(first.id);
  await nav(page, `#/lesson/${lesson.id}/${second.id}`);
  await expect.poll(() => saved(page)).toBe(second.id);
  // Up at the masthead and title, no section has reached the reading line.
  await page.evaluate(() => window.scrollTo(0, 0));
  expect(
    await page
      .locator(`#${first.id}`)
      .evaluate((e) => e.getBoundingClientRect().top),
  ).toBeGreaterThan(180);
  // pagehide captures synchronously, so this is not a race with the debounce.
  await page.evaluate(() => window.dispatchEvent(new Event("pagehide")));
  await page.waitForTimeout(300);
  expect(await saved(page)).toBe(second.id);
  await expect(
    page.getByRole("link", { name: "Search", exact: true }),
  ).toHaveAttribute(
    "href",
    `#/search?from=${encodeURIComponent(`#/lesson/${lesson.id}/${second.id}`)}`,
  );
  // Reading the first section moves the saved place back to it.
  await page
    .locator(`#${first.id}`)
    .evaluate((e) => e.scrollIntoView({ block: "start" }));
  await page.evaluate(() => window.dispatchEvent(new Event("pagehide")));
  await expect.poll(() => saved(page)).toBe(first.id);
});
