import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import type { CatalogCourse } from "../../src/catalog-types";
import { ready, nav, stored, shot } from "./helpers";

// Every capstone in the released course, read from the generated catalog: a
// saved draft survives a reload, stakeholder disclosures and the model
// response open, the rubric records one self-assessment, and a data pack
// downloads with the bytes the catalog declares.
const catalog = JSON.parse(
  await readFile("src/generated/catalog.json", "utf8"),
) as CatalogCourse[];
const course = catalog.find((c) => c.scenarios.some((s) => s.isCapstone))!;
const capstones = course.scenarios.filter((s) => s.isCapstone);

test("Every capstone keeps a saved draft, opens its model response and rubric, and serves its data pack", async ({
  page,
}) => {
  test.setTimeout(120_000);
  expect(capstones.length).toBeGreaterThanOrEqual(3);
  await ready(page, "/#/practice");
  for (const [i, scenario] of capstones.entries()) {
    await nav(page, `#/practice/${scenario.id}`);
    await expect(page.locator("main h1")).toHaveText(scenario.title);
    await expect(
      page.getByRole("heading", { name: "The situation", exact: true }),
    ).toBeVisible();
    if (scenario.revisionNotice)
      await expect(page.locator(".academy-revision")).toContainText(
        scenario.revisionNotice.slice(0, 40),
      );
    for (const downloadId of scenario.downloadIds ?? []) {
      const pack = course.downloads!.find((d) => d.id === downloadId)!;
      const link = page
        .locator(".academy-data-pack")
        .getByRole("link", { name: pack.title });
      const event = page.waitForEvent("download");
      await link.click();
      expect(
        createHash("sha256")
          .update(await readFile((await (await event).path())!))
          .digest("hex"),
      ).toBe(pack.sha256);
    }
    const draft = `Synthetic capstone draft ${i + 1}: owner, evidence, a reversible decision and what is still unknown.`;
    await page
      .getByRole("textbox", { name: "Your response", exact: true })
      .fill(draft);
    const disclosures = page.locator(".stakeholder summary");
    for (let d = 0; d < (await disclosures.count()); d++)
      await disclosures.nth(d).click();
    await page
      .getByText("Reveal model response and reasoning", { exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "One defensible response" }),
    ).toBeVisible();
    await expect(page.locator(".model-response")).not.toBeEmpty();
    const rubrics = page.locator(".rubric");
    expect(await rubrics.count()).toBeGreaterThanOrEqual(4);
    for (let r = 0; r < (await rubrics.count()); r++)
      await rubrics.nth(r).getByRole("radio").nth(1).check();
    await page.getByRole("button", { name: "Record self-assessment" }).click();
    await expect(
      page.getByText("1 self-assessments recorded", { exact: true }),
    ).toBeVisible();
    await page.reload();
    await expect(
      page.getByRole("textbox", { name: "Your response", exact: true }),
    ).toHaveValue(draft);
    await shot(page, `capstone-${i + 1}`);
  }
  const state = await stored(page);
  expect(
    capstones.filter((s) =>
      Object.values(state.assessments).some((a) => a.targetId === s.id),
    ),
  ).toHaveLength(capstones.length);
});
