import { expect, type Page } from "@playwright/test";
import type { StudyState } from "../../src/study";
export async function stored(page: Page): Promise<StudyState> {
  return page.evaluate(
    () =>
      new Promise((resolve, reject) => {
        const request = indexedDB.open("spicybrain-study-v2", 2);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const db = request.result,
            tx = db.transaction("study"),
            read = tx.objectStore("study").get("root");
          read.onsuccess = () => resolve(read.result);
          tx.oncomplete = () => db.close();
        };
      }),
  );
}
export async function ready(page: Page, path = "/") {
  await page.goto(path);
  await expect(page.locator("main h1")).toBeVisible();
}
export async function nav(page: Page, hash: string) {
  await page.evaluate((h) => {
    location.hash = h;
  }, hash);
  await expect(page.locator("main h1")).toBeVisible();
}
export async function noOverflow(page: Page) {
  const result = await page.evaluate(() => ({
    width: innerWidth,
    scroll: document.documentElement.scrollWidth,
    route: location.hash,
    overflow: [...document.querySelectorAll<HTMLElement>("body *")]
      .filter(
        (e) =>
          e.getBoundingClientRect().right > innerWidth + 1 &&
          !e.closest(".sc-table-scroll,.diagram-scroll,pre"),
      )
      .slice(-15)
      .map((e) => ({
        tag: e.tagName,
        class: e.className,
        text: e.textContent?.slice(0, 70),
        right: e.getBoundingClientRect().right,
        width: e.getBoundingClientRect().width,
      })),
  }));
  expect(result.scroll, JSON.stringify(result)).toBeLessThanOrEqual(
    result.width + 1,
  );
}
export async function shot(page: Page, name: string) {
  await page.screenshot({
    path: `test-results/evidence/${name}.png`,
    animations: "disabled",
  });
}
export async function saved(page: Page) {
  await expect.poll(async () => (await stored(page))?.schemaVersion).toBe(2);
  await expect(
    page.getByText("Unsaved · keep this tab open", { exact: true }),
  ).toHaveCount(0);
}
