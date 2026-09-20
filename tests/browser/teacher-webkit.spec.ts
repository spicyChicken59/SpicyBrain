import { test, expect } from "@playwright/test";
import { ready, nav, stored, noOverflow } from "./helpers";

test("WebKit narrow teaching deck: touch definition, visual state, independent reveal and exact reload state", async ({
  page,
}) => {
  const beat = "dbxfe-genai-beat-context";
  const question = "dbxfe-genai-check-context";
  await ready(page, `/SpicyBrain/#/module/dbxfe-genai/${beat}`);
  const article = page.locator(".teaching-beat");
  await expect(
    article.getByRole("heading", {
      name: "An answer sees selected context",
      exact: true,
    }),
  ).toBeVisible();
  await article.getByRole("button", { name: "context", exact: true }).tap();
  const definition = page.getByRole("dialog", {
    name: "context definition",
    exact: true,
  });
  await expect(definition).toBeVisible();
  await expect(definition).toContainText(
    "Information supplied to the model for a particular request.",
  );
  const rect = await definition.boundingBox();
  expect(rect).not.toBeNull();
  expect(rect!.x).toBeGreaterThanOrEqual(0);
  expect(rect!.x + rect!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await definition.getByRole("button", { name: "Close definition" }).tap();
  await expect(definition).not.toBeVisible();

  const stages = article.getByRole("group", {
    name: "An answer sees selected context stages",
    exact: true,
  });
  const changed = stages.getByRole("button", {
    name: "2 Correct the selection",
    exact: true,
  });
  await changed.tap();
  await expect(changed).toHaveAttribute("aria-pressed", "true");
  await expect
    .poll(async () => (await stored(page)).beatPositions[beat]?.visualStateId)
    .toBe("change");
  await article
    .getByRole("button", { name: "Enlarge visual", exact: true })
    .tap();
  const enlarged = page.getByRole("dialog", {
    name: "An answer sees selected context, enlarged",
    exact: true,
  });
  await expect(enlarged).toBeVisible();
  await expect(
    enlarged.getByRole("button", {
      name: "2 Correct the selection",
      exact: true,
    }),
  ).toHaveAttribute("aria-pressed", "true");
  await enlarged.getByRole("button", { name: "Close enlarged visual" }).tap();

  await article.getByText("Check yourself", { exact: true }).tap();
  const reasoning = article.getByLabel("Your reasoning (saved locally)");
  await reasoning.fill(
    "Inspect the selected manual and revision before accepting the answer.",
  );
  await expect(
    article.getByText("Model reasoning · self-comparison", { exact: true }),
  ).toHaveCount(0);
  await expect
    .poll(async () => (await stored(page)).drafts[`draft-${question}`]?.text)
    .toBe(
      "Inspect the selected manual and revision before accepting the answer.",
    );
  await article
    .getByRole("button", { name: "Reveal model reasoning", exact: true })
    .tap();
  await expect(
    article.getByText("No automatic score is assigned to your writing.", {
      exact: true,
    }),
  ).toBeVisible();
  await page.getByText("Reading options", { exact: true }).tap();
  await page.getByLabel("Show Samajh analogies").uncheck();
  await article
    .getByRole("button", {
      name: "Open handbook beside this beat",
      exact: true,
    })
    .tap();
  await expect(
    page.getByRole("complementary", { name: "Handbook beside the deck" }),
  ).toBeVisible();
  await expect
    .poll(async () => {
      const state = await stored(page);
      return [
        state.beatChecks[`check-${question}`]?.revealed,
        state.beatPositions[beat]?.handbookOpen,
        state.settings.showSamajh,
      ];
    })
    .toEqual([true, true, false]);
  await noOverflow(page);

  await page.reload();
  await expect(
    article.getByRole("heading", {
      name: "An answer sees selected context",
      exact: true,
    }),
  ).toBeVisible();
  await expect(changed).toHaveAttribute("aria-pressed", "true");
  await expect(reasoning).toHaveValue(
    "Inspect the selected manual and revision before accepting the answer.",
  );
  await expect(
    article.getByText("No automatic score is assigned to your writing.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("complementary", { name: "Handbook beside the deck" }),
  ).toBeVisible();
  const state = await stored(page);
  expect(state.settings.showSamajh).toBe(false);
  expect(state.beatResume?.beatId).toBe(beat);
  expect(state.beatResume?.visualStateId).toBe("change");
  expect(Object.keys(state.completions)).toHaveLength(0);
  expect(Object.keys(state.attempts)).toHaveLength(0);
  expect(Object.keys(state.reviews)).toHaveLength(0);
  await noOverflow(page);
});

test("WebKit narrow module cards: optional browse, exact explanation detour and explicit scheduling", async ({
  page,
}) => {
  const cardsRoute = "#/module/dbxfe-m09/dbxfe-m09-beat-audience?view=cards";
  await ready(page, `/SpicyBrain/${cardsRoute}`);
  await expect(
    page.getByRole("heading", { name: "Keep the useful ideas", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("9 cards in this selection.", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Card set", exact: true })
    .selectOption("extension");
  await expect(
    page.getByText("4 cards in this selection.", { exact: true }),
  ).toBeVisible();
  await page
    .getByText(
      "Can a successful Free Edition demo workspace simply become a commercial customer service?",
      { exact: true },
    )
    .tap();
  await expect(
    page
      .locator(".card-library > details[open]")
      .getByText("Why it matters:", { exact: true }),
  ).toBeVisible();
  await expect
    .poll(async () => (await stored(page)).beatResume?.view)
    .toBe("cards");
  const exactExplanation = page
    .getByRole("link", {
      name: "Return to the exact explanation →",
      exact: true,
    })
    .first();
  await exactExplanation.scrollIntoViewIfNeeded();
  await expect
    .poll(async () => {
      const y = await page.evaluate(() => window.scrollY);
      return (
        Math.abs(((await stored(page)).beatResume?.offset ?? -1000) - y) < 1
      );
    })
    .toBe(true);
  const before = await stored(page);
  expect(Object.keys(before.reviews)).toHaveLength(0);
  expect(Object.keys(before.schedules)).toHaveLength(0);
  await exactExplanation.tap();
  await expect(page).toHaveURL(
    /dbxfe-m09-beat-failure\?view=handbook&detour=1&extension=dbxfe-m09-extension-free-demo$/,
  );
  const extension = page.locator("#extension-dbxfe-m09-extension-free-demo");
  await expect(extension).toBeVisible();
  await expect(
    extension.getByRole("heading", {
      name: "Can a successful Free Edition demo workspace simply become a commercial customer service?",
      exact: true,
    }),
  ).toBeVisible();
  await expect(extension).toContainText("non-commercial");
  await expect
    .poll(async () => (await stored(page)).beatResume)
    .toEqual(before.beatResume);
  await noOverflow(page);

  await nav(page, cardsRoute);
  await page
    .getByRole("combobox", { name: "Card set", exact: true })
    .selectOption("extension");
  await page
    .getByRole("button", { name: "Review this selection", exact: true })
    .tap();
  await page
    .getByRole("button", { name: "Introduce new cards", exact: true })
    .tap();
  expect(Object.keys((await stored(page)).reviews)).toHaveLength(0);
  await page.getByRole("button", { name: "Reveal answer", exact: true }).tap();
  expect(Object.keys((await stored(page)).reviews)).toHaveLength(0);
  await page.getByRole("button", { name: "Good", exact: true }).tap();
  await expect
    .poll(async () => Object.keys((await stored(page)).reviews).length)
    .toBe(1);
  const after = await stored(page);
  const review = Object.values(after.reviews)[0];
  expect(review.cardId).toMatch(/^dbxfe-m09-extension-/);
  expect(after.schedules[review.cardId].lastEventId).toBe(review.id);
  expect(Object.keys(after.completions)).toHaveLength(0);
  expect(Object.keys(after.attempts)).toHaveLength(0);
  await noOverflow(page);
});
