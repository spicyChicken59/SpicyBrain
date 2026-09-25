import { test, expect } from "@playwright/test";
import { ready, nav, noOverflow, shot } from "./helpers";

for (const width of [1440, 390]) {
  test(`Genie Agent access distinctions remain readable at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await ready(page, "/#/module/dbxfe-genie/dbxfe-genie-names?view=deck");
    await expect(page.locator(".teaching-beat figure").first()).toContainText("Tune Genie Agent quality");
    await noOverflow(page);
    await nav(page, "#/module/dbxfe-genie/dbxfe-genie-access?view=handbook");
    const article = page.locator("#handbook-dbxfe-genie-access");
    await expect(article).toContainText("publisher's data grants");
    await expect(article).toContainText("shared as agent context");
    await noOverflow(page);
    await shot(page, `genie-agent-access-${width}`);
  });
  test(`Genie Code source corrections remain readable at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await ready(page, "/#/module/dbxfe-ai-assist/dbxfe-ai-assist-names?view=deck");
    await expect(page.locator(".teaching-beat figure").first()).toContainText("Former Assistant addresses");
    await expect(page.locator(".teaching-beat figure").first()).toContainText("Resolved pages");
    await noOverflow(page);
    await shot(page, `genie-code-names-${width}`);
    await nav(page, "#/module/dbxfe-ai-assist/dbxfe-ai-assist-review?view=handbook");
    const article = page.locator("#handbook-dbxfe-ai-assist-review");
    await expect(article).toContainText("Auto-approve as the current AWS first-use default");
    await expect(article).toContainText("not a security boundary");
    await noOverflow(page);
    await shot(page, `genie-code-approvals-${width}`);
  });
}
