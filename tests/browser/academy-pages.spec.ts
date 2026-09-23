import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFile } from "node:fs/promises";
import type { CatalogCourse } from "../../src/catalog-types";
import { ready, nav, noOverflow } from "./helpers";

// Every academy page kind a learner reaches from the course map, read from
// the generated catalog so the list follows the content: each lab, field
// guide, case analysis and capstone, the lab shelf, the guide list, the case
// list and the crosswalk. Phones at 390 px, and 320 px with every font size
// doubled (200% text), must not scroll sideways; axe finds nothing in either
// theme on one page of each kind; the keyboard reaches a lab download and a
// guide's Draft in Notebook.
const catalog = JSON.parse(
  await readFile("src/generated/catalog.json", "utf8"),
) as CatalogCourse[];
const course = catalog.find((c) => c.labs?.length && c.guides?.length);
test.skip(!course, "No course publishes labs and guides");
const c = course!;
const routes = [
  `#/course/${c.id}`,
  `#/course/${c.id}/labs`,
  `#/course/${c.id}/guides`,
  `#/course/${c.id}/cases`,
  `#/course/${c.id}/crosswalk`,
  ...(c.labs ?? []).map((l) => `#/course/${c.id}/labs/${l.id}`),
  ...(c.guides ?? []).map((g) => `#/course/${c.id}/guides/${g.id}`),
  ...(c.cases ?? []).map((k) => `#/course/${c.id}/cases/${k.id}`),
  ...c.scenarios.filter((s) => s.isCapstone).map((s) => `#/practice/${s.id}`),
];
const doubleText = (page: Page) =>
  page.evaluate(() => {
    const scale = (rules: CSSRuleList) => {
      for (const rule of rules) {
        if (rule instanceof CSSStyleRule && rule.style.fontSize)
          rule.style.fontSize = `calc((${rule.style.fontSize}) * 2)`;
        if ("cssRules" in rule) scale((rule as CSSGroupingRule).cssRules);
      }
    };
    for (const sheet of document.styleSheets) scale(sheet.cssRules);
  });
const axe = async (page: Page) => {
  await page.waitForFunction(() =>
    document.getAnimations().every((a) => a.playState !== "running"),
  );
  return (
    await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze()
  ).violations.map((v) => ({ id: v.id, nodes: v.nodes.map((n) => n.target) }));
};

test("Every academy page fits a 390 px phone without sideways scrolling", async ({
  page,
}) => {
  test.setTimeout(300_000);
  await page.setViewportSize({ width: 390, height: 844 });
  await ready(page);
  for (const hash of routes) {
    await nav(page, hash);
    await noOverflow(page);
  }
});

test("Every academy page fits 320 px with 200% text", async ({ page }) => {
  test.setTimeout(300_000);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 320, height: 800 });
  await ready(page);
  await doubleText(page);
  for (const hash of routes) {
    await nav(page, hash);
    await noOverflow(page);
  }
});

test("One page of each academy kind passes axe in both themes", async ({
  page,
}) => {
  test.setTimeout(180_000);
  const kinds = [
    `#/course/${c.id}/labs`,
    `#/course/${c.id}/labs/${c.labs![0].id}`,
    `#/course/${c.id}/guides/${c.guides![0].id}`,
    `#/course/${c.id}/cases/${c.cases![0].id}`,
    `#/course/${c.id}/crosswalk`,
    `#/practice/${c.scenarios.find((s) => s.isCapstone)!.id}`,
  ];
  await ready(page);
  for (const theme of ["dark", "light"]) {
    await nav(page, "#/settings");
    await page.getByLabel("Theme").selectOption(theme);
    for (const hash of kinds) {
      await nav(page, hash);
      expect(await axe(page), `${theme} ${hash}`).toEqual([]);
    }
  }
});

test("The keyboard reaches a lab download and a guide's Draft in Notebook", async ({
  page,
}) => {
  const lab = c.labs!.find((l) => l.downloadId)!;
  const download = c.downloads!.find((d) => d.id === lab.downloadId)!;
  await ready(page, `/#/course/${c.id}/labs`);
  const reach = async (name: string, role: "link" | "button") => {
    const target = page.getByRole(role, { name, exact: true }).first();
    for (let i = 0; i < 400; i++) {
      await page.keyboard.press("Tab");
      if (await target.evaluate((e) => e === document.activeElement)) return;
    }
    throw Error(`Tab never reached ${name}`);
  };
  await reach(download.title, "link");
  await expect(page.locator(":focus")).toBeVisible();
  await nav(page, `#/course/${c.id}/guides/${c.guides![0].id}`);
  const template = page.locator("section.academy-guide-part").filter({
    has: page.getByRole("heading", { level: 2, name: "Template", exact: true }),
  });
  await template.locator("summary").focus();
  await page.keyboard.press("Enter");
  await reach("Draft in Notebook", "button");
  await page.keyboard.press("Enter");
  await expect(
    template.getByLabel("Your draft from this template"),
  ).toBeFocused();
});
