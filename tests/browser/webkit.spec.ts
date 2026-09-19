import { test, expect } from "@playwright/test";
import { ready, nav, stored, noOverflow } from "./helpers";
test("WebKit mobile emulation smoke: nested static reader, note, reload, dialog and review", async ({
  page,
}) => {
  await ready(
    page,
    "/SpicyBrain/#/lesson/dbxfe-m01-l01/dbxfe-m01-l01-understand",
  );
  const section = page.locator("#dbxfe-m01-l01-understand");
  await section.getByText("Notes for this section", { exact: true }).click();
  await section
    .getByLabel("Your lesson note")
    .fill("Synthetic WebKit emulation note");
  await expect
    .poll(
      async () =>
        (await stored(page))?.notes["note-dbxfe-m01-l01-understand"]?.text,
    )
    .toBe("Synthetic WebKit emulation note");
  await page.reload();
  await expect(section.getByLabel("Your lesson note")).toHaveValue(
    "Synthetic WebKit emulation note",
  );
  await nav(page, "#/lesson/dbxfe-m01-l01/dbxfe-m01-l01-see");
  await page.getByRole("button", { name: "Open diagram", exact: true }).click();
  await page.getByRole("button", { name: "Zoom in" }).click();
  await page.getByRole("button", { name: "Close diagram" }).click();
  await noOverflow(page);
  await nav(page, "#/review/dbxfe-m01-l01");
  await page.getByRole("button", { name: "Introduce new cards" }).click();
  await page
    .getByRole("button", { name: "Reveal answer", exact: true })
    .click();
  await page.getByRole("button", { name: "Good", exact: true }).click();
  await expect
    .poll(async () => Object.keys((await stored(page)).reviews).length)
    .toBe(1);
});
