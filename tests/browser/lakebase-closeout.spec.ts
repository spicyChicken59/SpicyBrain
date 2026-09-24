import { test, expect } from "@playwright/test";
import { ready, nav, noOverflow, shot } from "./helpers";

for (const width of [1440, 390]) {
  test(`Lakebase restore and pooler correction are readable across deck, handbook and check at ${width}`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await ready(
      page,
      "/#/module/dbxfe-lakebase/dbxfe-lakebase-branches?view=deck",
    );
    await expect(page.locator(".teaching-beat>h2")).toContainText(
      "using it is a separate decision",
    );
    await page
      .locator(".teaching-beat .visual-stages")
      .first()
      .getByRole("button")
      .nth(2)
      .click();
    const figure = page.locator(".teaching-beat figure").first();
    await expect(figure).toContainText("Original branch");
    await expect(figure).toContainText(
      "Later claims and decisions still present",
    );
    await expect(figure).toContainText(
      "Existing sessions stay on the original",
    );
    await noOverflow(page);
    await shot(page, `lakebase-restore-${width}`);
    const check = page.locator(".beat-check").first();
    await check.locator("summary").click();
    await check
      .locator("textarea")
      .fill("SYNTHETIC: inspect recovered state and reconcile before cutover.");
    await check.getByRole("button", { name: "Reveal model reasoning" }).click();
    await expect(check).toContainText("cutover separately");
    await nav(
      page,
      "#/module/dbxfe-lakebase/dbxfe-lakebase-connections?view=handbook",
    );
    await expect(
      page.getByText(
        "LISTEN and NOTIFY are both unsupported by the managed pooler",
        { exact: true },
      ),
    ).toBeVisible();
    await noOverflow(page);
    await shot(page, `lakebase-pooler-${width}`);
  });
}
